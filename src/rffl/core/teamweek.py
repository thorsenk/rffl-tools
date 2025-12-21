"""Generate teamweek_unified.csv from boxscores.csv.

This module provides functionality to transform player-level boxscore data
into team-week aggregated data suitable for analysis and KORM processing.
"""

import csv
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]


def generate_teamweek_unified(
    boxscores_path: str | Path,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Generate teamweek_unified.csv from boxscores.csv.

    Transforms player-level boxscore data into team-week aggregated data,
    matching opponents and calculating win/loss results.

    Args:
        boxscores_path: Path to boxscores.csv file
        output_path: Optional output path for CSV. If None, returns DataFrame only.

    Returns:
        DataFrame with team-week unified data

    Raises:
        FileNotFoundError: If boxscores_path doesn't exist
        ValueError: If boxscores data is invalid
    """
    boxscores_path = Path(boxscores_path)
    if not boxscores_path.exists():
        raise FileNotFoundError(f"Boxscores file not found: {boxscores_path}")

    # Read boxscores
    df = pd.read_csv(boxscores_path)

    # Validate required columns
    required_cols = [
        "season_year", "week", "matchup", "team_code",
        "is_co_owned?", "team_owner_1", "team_owner_2",
        "team_projected_total", "team_actual_total"
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Group by team-week and take first row (team totals are duplicated per player)
    team_week = df.groupby(
        ["season_year", "week", "matchup", "team_code"],
        as_index=False
    ).agg({
        "is_co_owned?": "first",
        "team_owner_1": "first",
        "team_owner_2": "first",
        "team_projected_total": "first",
        "team_actual_total": "first",
    })

    # Create matchup pairs to find opponents
    rows = []
    for (season, week, matchup), group in team_week.groupby(
        ["season_year", "week", "matchup"]
    ):
        teams = group.to_dict("records")
        if len(teams) != 2:
            # Skip incomplete matchups (e.g., bye weeks or data issues)
            continue

        team_a, team_b = teams[0], teams[1]

        # Create row for team_a
        rows.append(_create_unified_row(team_a, team_b, season, week, matchup))
        # Create row for team_b
        rows.append(_create_unified_row(team_b, team_a, season, week, matchup))

    # Create output DataFrame
    result = pd.DataFrame(rows)

    # Sort by season, week, matchup, team_code
    result = result.sort_values(
        ["season_year", "week", "matchup", "team_code"]
    ).reset_index(drop=True)

    # Write to CSV if output path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(output_path, index=False, quoting=csv.QUOTE_MINIMAL)

    return result


def _create_unified_row(
    team: dict[str, Any],
    opponent: dict[str, Any],
    season: int,
    week: int,
    matchup: int,
) -> dict[str, Any]:
    """Create a unified row for one team in a matchup."""
    team_score = team["team_actual_total"]
    opp_score = opponent["team_actual_total"]
    margin = round(team_score - opp_score, 2)

    if team_score > opp_score:
        result = "W"
    elif team_score < opp_score:
        result = "L"
    else:
        result = "T"

    return {
        "season_year": season,
        "week": week,
        "matchup": matchup,
        "team_code": team["team_code"],
        "is_co_owned?": team["is_co_owned?"],
        "team_owner_1": team["team_owner_1"],
        "team_owner_2": team["team_owner_2"] if pd.notna(team["team_owner_2"]) else "",
        "opponent_code": opponent["team_code"],
        "opp_is_co_owned?": opponent["is_co_owned?"],
        "opp_owner_1": opponent["team_owner_1"],
        "opp_owner_2": opponent["team_owner_2"] if pd.notna(opponent["team_owner_2"]) else "",
        "team_projected_total": team["team_projected_total"],
        "team_actual_total": team_score,
        "opp_actual_total": opp_score,
        "result": result,
        "margin": margin,
    }


def generate_teamweek_for_season(
    season_dir: str | Path,
    force: bool = False,
) -> Path | None:
    """
    Generate teamweek_unified.csv for a season directory.

    Args:
        season_dir: Path to season directory (e.g., data/seasons/2024)
        force: If True, overwrite existing file. If False, skip if exists.

    Returns:
        Path to generated file, or None if skipped
    """
    season_dir = Path(season_dir)
    boxscores_path = season_dir / "boxscores.csv"
    output_path = season_dir / "reports" / "teamweek_unified.csv"

    if not boxscores_path.exists():
        return None

    if output_path.exists() and not force:
        return None

    generate_teamweek_unified(boxscores_path, output_path)
    return output_path
