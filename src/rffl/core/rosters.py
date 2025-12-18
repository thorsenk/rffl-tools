"""Historical roster export logic."""

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd
import requests

from .api import ESPNCredentials
from .exceptions import ESPNAPIError
from .utils import load_alias_index, resolve_canonical


@dataclass
class HistoricalRosterRow:
    """Row data structure for historical roster export."""

    season_year: int
    week: int
    matchup: int
    team_code: str
    slot: str
    player_name: str
    nfl_team: str | None
    position: str | None
    is_starter: bool


def map_lineup_slot_id(slot_id: int) -> str:
    """Map ESPN lineup slot ID to readable slot name."""
    slot_mapping = {
        0: "QB",
        1: "TQB",
        2: "RB",
        3: "RB/WR",
        4: "WR",
        5: "WR/TE",
        6: "TE",
        7: "OP",
        8: "DT",
        9: "DE",
        10: "LB",
        11: "DL",
        12: "CB",
        13: "S",
        14: "DB",
        15: "DP",
        16: "D/ST",
        17: "K",
        20: "Bench",
        21: "IR",
        23: "FLEX",
    }
    return slot_mapping.get(slot_id, "Unknown")


def map_position_id(position_id: int | None) -> str:
    """Map ESPN position ID to readable position."""
    if position_id is None:
        return "Unknown"
    position_mapping = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "D/ST"}
    return position_mapping.get(position_id, "Unknown")


def map_pro_team_id(team_id: int | None) -> str | None:
    """Map ESPN pro team ID to NFL team abbreviation."""
    if team_id is None:
        return None
    # Simplified mapping - expand as needed
    team_mapping = {
        1: "ATL",
        2: "BUF",
        3: "CHI",
        4: "CIN",
        5: "CLE",
        6: "DAL",
        7: "DEN",
        8: "DET",
        9: "GB",
        10: "TEN",
        11: "IND",
        12: "KC",
        13: "LV",
        14: "LAR",
        15: "MIA",
        16: "MIN",
        17: "NE",
        18: "NO",
        19: "NYG",
        20: "NYJ",
        21: "PHI",
        22: "ARI",
        23: "PIT",
        24: "LAC",
        25: "SF",
        26: "SEA",
        27: "TB",
        28: "WAS",
        29: "CAR",
        30: "JAX",
        33: "BAL",
        34: "HOU",
    }
    return team_mapping.get(team_id, "Unknown")


def export_historical_rosters(
    league_id: int,
    year: int,
    output_path: str | Path,
    week: int | None = None,
    credentials: ESPNCredentials | None = None,
    public_only: bool = True,
    repo_root: Path | None = None,
) -> Path:
    """
    Export END-OF-SEASON roster compositions for historical seasons (2011-2018).

    NOTE: This API returns final roster state after all season transactions,
    not weekly lineups.

    Args:
        league_id: ESPN league ID
        year: Season year (2011-2018)
        output_path: Output CSV file path
        week: Week parameter (IGNORED - all weeks return same data)
        credentials: Optional ESPN authentication credentials
        public_only: If True, ignore credentials (public league mode)
        repo_root: Repository root path (for team mappings)

    Returns:
        Path to written CSV file

    Raises:
        ESPNAPIError: If ESPN API calls fail
        ValueError: If year >= 2019 (use export command instead)
    """
    if year >= 2019:
        raise ValueError(
            "Use 'export' command for 2019+ seasons. "
            "This command is for 2011-2018."
        )

    if repo_root is None:
        # Find repo root
        current = Path.cwd()
        for parent in [current, *current.parents]:
            if (parent / "pyproject.toml").exists():
                repo_root = parent
                break
        if repo_root is None:
            raise ValueError("Could not find repository root")

    # Use historical API endpoint for pre-2019 seasons
    base_url = (
        f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/"
        f"leagueHistory/{league_id}"
    )
    params = {
        "seasonId": year,
        "view": ["mRoster", "mTeam"],  # Try to get team info too
    }

    if week:
        params["scoringPeriodId"] = week

    # Setup authentication cookies if provided
    cookies = {}
    if not public_only and credentials and credentials.is_authenticated:
        if credentials.espn_s2:
            cookies["espn_s2"] = credentials.espn_s2
        if credentials.swid:
            cookies["SWID"] = credentials.swid

    try:
        response = requests.get(base_url, params=params, cookies=cookies, timeout=10)
        response.raise_for_status()

        # Historical API returns data wrapped in array
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            league_data = data[0]
        else:
            league_data = data

    except requests.exceptions.RequestException as e:
        raise ESPNAPIError(
            f"Failed to fetch historical roster data for {year}. "
            f"URL: {base_url}, Params: {params}. Error: {e}"
        ) from e

    rows: list[HistoricalRosterRow] = []

    # Load alias index for canonical team resolution
    mapping_path = repo_root / "data" / "teams" / "alias_mapping.yaml"
    alias_idx = load_alias_index(mapping_path)

    try:
        # Extract teams and their rosters
        teams = league_data.get("teams", [])

        for team in teams:
            team_id = team.get("id", "Unknown")
            # Now we have team info with mTeam view
            team_abbrev = (
                team.get("abbrev")
                or team.get("teamAbbrev")
                or team.get("name")
                or f"TEAM_{team_id}"
            )
            team_code = resolve_canonical(team_abbrev, year, alias_idx)

            # Get roster for each week requested
            roster = team.get("roster", {})
            entries = roster.get("entries", [])

            for entry in entries:
                player_info = entry.get("playerPoolEntry", {}).get("player", {})
                lineup_slot = entry.get("lineupSlotId", 0)

                # Map lineup slot ID to readable slot name
                slot_name = map_lineup_slot_id(lineup_slot)
                # ESPN typically uses <20 for starters, but bench is 20, IR is 21
                is_starter = lineup_slot not in [20, 21]  # Not bench or IR

                player_name = player_info.get("fullName", "Unknown")
                pro_team = player_info.get("proTeamId")
                position = map_position_id(player_info.get("defaultPositionId"))

                # Convert pro team ID to team abbreviation if available
                nfl_team = map_pro_team_id(pro_team) if pro_team else None

                rows.append(
                    HistoricalRosterRow(
                        season_year=year,
                        week=week or 1,  # Default to week 1 if not specified
                        matchup=1,  # Historical data may not have matchup info
                        team_code=team_code,
                        slot=slot_name,
                        player_name=player_name,
                        nfl_team=nfl_team,
                        position=position,
                        is_starter=is_starter,
                    )
                )

    except Exception as e:
        raise ESPNAPIError(f"Failed to parse historical roster data: {e}") from e

    if not rows:
        raise ESPNAPIError(
            "No roster data found. Check year, league_id, and credentials."
        )

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([asdict(r) for r in rows]).to_csv(
        out_path, index=False, quoting=csv.QUOTE_MINIMAL
    )
    return out_path

