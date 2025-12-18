"""Boxscore export logic."""

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .api import ESPNCredentials, ESPNClient
from .constants import FLEX_ELIGIBLE_POSITIONS, RFFL_LINEUP_REQUIREMENTS
from .exceptions import ESPNAPIError, ValidationError
from .utils import (
    get_team_abbrev,
    is_starter,
    load_alias_index,
    load_canonical_meta,
    norm_slot,
    resolve_canonical,
    safe_float,
)


@dataclass
class Row:
    """Row data structure for boxscore export."""

    season_year: int
    week: int
    matchup: int
    team_code: str
    is_co_owned: str
    team_owner_1: str
    team_owner_2: str
    team_projected_total: float
    team_actual_total: float
    slot_type: str
    slot: str
    player_name: str
    nfl_team: str | None
    position: str | None
    is_placeholder: str
    issue_flag: str | None
    rs_projected_pf: float
    rs_actual_pf: float


def iter_weeks(client: ESPNClient, start: int | None, end: int | None):
    """Iterate over weeks, yielding (week, boxscores) tuples."""
    lo = start or 1
    hi = end or 18
    league = client.get_league()
    for wk in range(lo, hi + 1):
        try:
            b = client.get_boxscores(wk)
            if b:
                yield wk, b
        except ESPNAPIError:
            continue


def export_boxscores(
    league_id: int,
    year: int,
    output_path: str | Path,
    start_week: int | None = None,
    end_week: int | None = None,
    fill_missing_slots: bool = False,
    require_clean: bool = False,
    tolerance: float = 0.0,
    credentials: ESPNCredentials | None = None,
    public_only: bool = True,
    repo_root: Path | None = None,
) -> Path:
    """
    Export ESPN fantasy football boxscores to CSV format.

    Args:
        league_id: ESPN league ID
        year: Season year
        output_path: Output CSV file path
        start_week: Start week (default: 1)
        end_week: End week (default: 18)
        fill_missing_slots: Insert 0-pt placeholders for missing required starters
        require_clean: Validate and fail if sums/counts are not clean
        tolerance: Allowed difference for --require-clean
        credentials: Optional ESPN authentication credentials
        public_only: If True, ignore credentials (public league mode)
        repo_root: Repository root path (for loading team mappings)

    Returns:
        Path to written CSV file

    Raises:
        ESPNAPIError: If ESPN API calls fail
        ValidationError: If require_clean validation fails
    """
    if repo_root is None:
        # Find repo root by looking for pyproject.toml
        current = Path.cwd()
        for parent in [current, *current.parents]:
            if (parent / "pyproject.toml").exists():
                repo_root = parent
                break
        if repo_root is None:
            raise ValueError("Could not find repository root")

    client = ESPNClient(
        league_id=league_id,
        year=year,
        credentials=credentials,
        public_only=public_only,
    )

    rows: list[Row] = []

    try:
        # Load alias index once for canonical team_code resolution
        mapping_path = repo_root / "data" / "teams" / "alias_mapping.yaml"
        alias_idx = load_alias_index(mapping_path)
        canon_meta = load_canonical_meta(repo_root)

        for week, boxscores in iter_weeks(client, start_week, end_week):
            for m_idx, bs in enumerate(boxscores, start=1):
                for side in ("home", "away"):
                    team = getattr(bs, f"{side}_team", None)
                    lineup = getattr(bs, f"{side}_lineup", None) or []
                    if not team:
                        continue

                    # Resolve canonical team_code
                    src_abbrev = get_team_abbrev(team)
                    team_code = resolve_canonical(src_abbrev, year, alias_idx)

                    # Owners/co-owned from canonical meta
                    meta = canon_meta.get((year, team_code), {})
                    is_co_owned = meta.get("is_co_owned", "")
                    owner1 = meta.get("owner_code_1", "")
                    owner2 = meta.get("owner_code_2", "")

                    # Build starter list
                    # Per-player rounding occurs before summing so team totals
                    # match the sum of starter rows exactly.
                    starters = []
                    stamped = []
                    for _idx, bp in enumerate(lineup):
                        slot = norm_slot(
                            getattr(bp, "slot_position", None),
                            getattr(bp, "position", None),
                        )
                        proj = round(safe_float(getattr(bp, "projected_points", 0.0)), 2)
                        act = round(safe_float(getattr(bp, "points", 0.0)), 2)
                        row = {
                            "slot": slot,
                            "slot_type": "starters" if is_starter(slot) else "bench",
                            "player_name": getattr(bp, "name", None),
                            "nfl_team": getattr(bp, "proTeam", ""),
                            "position": getattr(bp, "position", None),
                            "is_placeholder": "No",
                            "issue_flag": "",
                            "rs_projected_pf": proj,
                            "rs_actual_pf": act,
                            "_orig_idx": _idx,
                        }
                        # Flag invalid FLEX position on real rows (RB/WR/TE only)
                        if row["slot"] == "FLEX":
                            pos = (row.get("position") or "").upper()
                            if pos not in FLEX_ELIGIBLE_POSITIONS:
                                row["issue_flag"] = (
                                    f"INVALID_FLEX_POSITION:{pos or 'UNKNOWN'}"
                                )
                        stamped.append(row)
                        if row["slot_type"] == "starters":
                            starters.append(row)

                    # Fill missing required starter slots (0-pt placeholders)
                    if fill_missing_slots:
                        # Count current starters by slot
                        have_counts = {}
                        for r in starters:
                            have_counts[r["slot"]] = have_counts.get(r["slot"], 0) + 1

                        for req_slot, req_count in RFFL_LINEUP_REQUIREMENTS.items():
                            have = have_counts.get(req_slot, 0)
                            missing = max(0, req_count - have)
                            for _i in range(missing):
                                placeholder = {
                                    "slot": req_slot,
                                    "slot_type": "starters",
                                    "player_name": f"EMPTY SLOT - {req_slot}",
                                    # FLEX placeholder uses a FLEX-eligible position
                                    "position": (
                                        req_slot if req_slot != "FLEX" else "WR"
                                    ),
                                    "nfl_team": "",
                                    "is_placeholder": "Yes",
                                    "issue_flag": f"MISSING_SLOT:{req_slot}",
                                    "rs_projected_pf": 0.0,
                                    "rs_actual_pf": 0.0,
                                    "_orig_idx": 1000,
                                }
                                starters.append(placeholder)
                                stamped.append(placeholder)

                    team_proj = round(sum(r["rs_projected_pf"] for r in starters), 2)
                    team_act = round(sum(r["rs_actual_pf"] for r in starters), 2)

                    # Order rows: starters in fixed slot sequence, then bench (original order)
                    desired_order = [
                        "QB",
                        "RB",
                        "RB",
                        "WR",
                        "WR",
                        "TE",
                        "FLEX",
                        "D/ST",
                        "K",
                    ]
                    # Build starters by desired sequence
                    starters_by_slot = {}
                    for r in starters:
                        starters_by_slot.setdefault(r["slot"], []).append(r)
                    # Maintain original order within same slot
                    for lst in starters_by_slot.values():
                        lst.sort(key=lambda x: x.get("_orig_idx", 0))
                    starters_sorted: list[dict] = []
                    for s in desired_order:
                        if s in starters_by_slot and starters_by_slot[s]:
                            starters_sorted.append(starters_by_slot[s].pop(0))
                    # Append any leftover starters just in case (stable by slot then orig idx)
                    leftovers = [r for lst in starters_by_slot.values() for r in lst]
                    slot_rank = {
                        "QB": 0,
                        "RB": 1,
                        "WR": 2,
                        "TE": 3,
                        "FLEX": 4,
                        "D/ST": 5,
                        "K": 6,
                    }
                    leftovers.sort(
                        key=lambda x: (
                            slot_rank.get(x.get("slot", ""), 99),
                            x.get("_orig_idx", 0),
                        )
                    )
                    starters_sorted.extend(leftovers)
                    bench_sorted = [r for r in stamped if r["slot_type"] != "starters"]
                    bench_sorted.sort(key=lambda x: x.get("_orig_idx", 0))
                    ordered = starters_sorted + bench_sorted

                    for r in ordered:
                        r.pop("_orig_idx", None)
                        rows.append(
                            Row(
                                season_year=year,
                                week=week,
                                matchup=m_idx,
                                team_code=team_code,
                                is_co_owned=is_co_owned,
                                team_owner_1=owner1,
                                team_owner_2=owner2,
                                team_projected_total=team_proj,
                                team_actual_total=team_act,
                                **r,
                            )
                        )
    except ESPNAPIError as e:
        raise
    except Exception as e:
        raise ESPNAPIError(f"Failed fetching box scores: {e}") from e

    df = pd.DataFrame([asdict(r) for r in rows])
    # Rename columns to final header names
    rename_map = {
        "is_co_owned": "is_co_owned?",
    }
    df = df.rename(columns=rename_map)

    # Optional: enforce cleanliness before writing
    if require_clean:
        starters = df[df["slot_type"] == "starters"].copy()
        team_key = "team_code" if "team_code" in starters.columns else "team_abbrev"
        agg = starters.groupby(["week", "matchup", team_key], as_index=False).agg(
            team_projected_total=("team_projected_total", "first"),
            team_actual_total=("team_actual_total", "first"),
            starters_proj_sum=("rs_projected_pf", "sum"),
            starters_actual_sum=("rs_actual_pf", "sum"),
            starter_count=("slot", "count"),
        )
        agg["proj_diff"] = (
            agg["starters_proj_sum"] - agg["team_projected_total"]
        ).round(2)
        agg["act_diff"] = (agg["starters_actual_sum"] - agg["team_actual_total"]).round(
            2
        )

        bad_proj = agg[agg["proj_diff"].abs() > tolerance]
        bad_act = agg[agg["act_diff"].abs() > tolerance]
        bad_cnt = agg[agg["starter_count"] != 9]

        if not bad_proj.empty or not bad_act.empty or not bad_cnt.empty:
            raise ValidationError(
                (
                    f"Export not clean: proj={len(bad_proj)}, act={len(bad_act)}, "
                    f"bad_count={len(bad_cnt)}."
                )
            )

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, quoting=csv.QUOTE_MINIMAL)
    return out_path

