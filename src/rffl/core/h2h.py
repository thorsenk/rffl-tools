"""H2H matchup export logic."""

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from .api import ESPNCredentials, ESPNClient
from .exceptions import ESPNAPIError
from .utils import get_team_abbrev, safe_float


@dataclass
class H2HRow:
    """Row data structure for H2H export."""

    week: int
    matchup: int
    home_team: str
    away_team: str
    home_score: float
    away_score: float
    winner: str  # home_team, away_team, or TIE
    margin: float


def export_h2h(
    league_id: int,
    year: int,
    output_path: str | Path,
    start_week: int | None = None,
    end_week: int | None = None,
    credentials: ESPNCredentials | None = None,
    public_only: bool = True,
) -> Path:
    """
    Export simplified head-to-head matchup results for a season.

    This uses per-matchup team scores from ESPN (no per-player lineups),
    which is more stable for older seasons (pre-2019).

    Args:
        league_id: ESPN league ID
        year: Season year
        output_path: Output CSV file path
        start_week: Start week (default: 1)
        end_week: End week (default: 18)
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

    rows: list[H2HRow] = []

    # Iterate via scoreboard to support pre-2019 seasons
    lo = start_week or 1
    hi = end_week or 18
    league = client.get_league()

    try:
        for week in range(lo, hi + 1):
            try:
                matchups = league.scoreboard(week)
            except Exception:
                # Skip weeks that cannot be fetched
                continue
            if not matchups:
                continue
            for m_idx, mu in enumerate(matchups, start=1):
                home_t = getattr(mu, "home_team", None)
                away_t = getattr(mu, "away_team", None)
                home_score = round(safe_float(getattr(mu, "home_score", None), 0.0), 2)
                away_score = round(safe_float(getattr(mu, "away_score", None), 0.0), 2)

                home_abbrev = get_team_abbrev(home_t) if home_t else "HOME"
                away_abbrev = get_team_abbrev(away_t) if away_t else "AWAY"

                if home_score > away_score:
                    winner = home_abbrev
                elif away_score > home_score:
                    winner = away_abbrev
                else:
                    winner = "TIE"

                margin = round(abs(home_score - away_score), 2)

                rows.append(
                    H2HRow(
                        week=week,
                        matchup=m_idx,
                        home_team=home_abbrev,
                        away_team=away_abbrev,
                        home_score=home_score,
                        away_score=away_score,
                        winner=winner,
                        margin=margin,
                    )
                )
    except ESPNAPIError as e:
        raise
    except Exception as e:
        raise ESPNAPIError(f"Failed fetching matchup results: {e}") from e

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([asdict(r) for r in rows]).to_csv(
        out_path, index=False, quoting=csv.QUOTE_MINIMAL
    )
    return out_path

