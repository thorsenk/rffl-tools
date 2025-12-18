"""Draft export logic."""

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from .api import ESPNCredentials, ESPNClient
from .exceptions import ESPNAPIError
from .utils import get_team_abbrev


@dataclass
class DraftRow:
    """Row data structure for draft export."""

    year: int
    round: int | None
    round_pick: int | None
    team_abbrev: str
    player_id: int | None
    player_name: str
    bid_amount: float | None
    keeper: bool | None
    nominating_team: str | None


def export_draft(
    league_id: int,
    year: int,
    output_path: str | Path,
    credentials: ESPNCredentials | None = None,
    public_only: bool = True,
) -> Path:
    """
    Export season draft results to CSV (snake or auction).

    Args:
        league_id: ESPN league ID
        year: Season year
        output_path: Output CSV file path
        credentials: Optional ESPN authentication credentials
        public_only: If True, ignore credentials (public league mode)

    Returns:
        Path to written CSV file

    Raises:
        ESPNAPIError: If ESPN API calls fail
    """
    client = ESPNClient(
        league_id=league_id,
        year=year,
        credentials=credentials,
        public_only=public_only,
    )

    # League initialization already fetches players, teams, and draft picks.
    # Avoid calling refresh_draft here to prevent duplicate picks from being appended.
    league = client.get_league()

    rows: list[DraftRow] = []
    try:
        for p in getattr(league, "draft", []) or []:
            team_abbrev = get_team_abbrev(getattr(p, "team", None))
            nom_team = (
                get_team_abbrev(getattr(p, "nominatingTeam", None))
                if getattr(p, "nominatingTeam", None)
                else None
            )
            rows.append(
                DraftRow(
                    year=year,
                    round=getattr(p, "round_num", None),
                    round_pick=getattr(p, "round_pick", None),
                    team_abbrev=team_abbrev,
                    player_id=getattr(p, "playerId", None),
                    player_name=(getattr(p, "playerName", None) or ""),
                    bid_amount=(
                        float(p.bid_amount)
                        if getattr(p, "bid_amount", None) is not None
                        else None
                    ),
                    keeper=getattr(p, "keeper_status", None),
                    nominating_team=nom_team,
                )
            )
    except Exception as e:
        raise ESPNAPIError(f"Failed fetching draft: {e}") from e

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([asdict(r) for r in rows]).to_csv(
        out_path, index=False, quoting=csv.QUOTE_MINIMAL
    )
    return out_path

