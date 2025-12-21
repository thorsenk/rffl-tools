"""RFFL lineup validation logic."""

from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from .constants import FLEX_ELIGIBLE_POSITIONS, RFFL_LINEUP_REQUIREMENTS
from .exceptions import LineupValidationError


def validate_rffl_lineup(starters_df: pd.DataFrame) -> dict[str, Any]:
    """
    Validate RFFL lineup compliance and return issues found.

    Args:
        starters_df: DataFrame with starter rows (slot_type == "starters")

    Returns:
        Dictionary with validation results:
        - is_valid: bool
        - issues: list of issue dictionaries
    """
    issues = []

    # Count starters by slot
    slot_counts = starters_df["slot"].value_counts().to_dict()

    # Check each required position
    for position, required_count in RFFL_LINEUP_REQUIREMENTS.items():
        actual_count = slot_counts.get(position, 0)
        if actual_count != required_count:
            issues.append(
                {
                    "type": "count_mismatch",
                    "position": position,
                    "required": required_count,
                    "actual": actual_count,
                    "description": (
                        f"Expected {required_count} {position}, "
                        f"found {actual_count}"
                    ),
                }
            )

    # Check FLEX eligibility
    flex_players = starters_df[starters_df["slot"] == "FLEX"]
    for _, player in flex_players.iterrows():
        player_position = player["position"]
        if player_position not in FLEX_ELIGIBLE_POSITIONS:
            issues.append(
                {
                    "type": "flex_ineligible",
                    "position": player_position,
                    "player": player["player_name"],
                    "description": (
                        f"FLEX player {player['player_name']} pos {player_position} "
                        "not RB/WR/TE"
                    ),
                }
            )

    # Check for duplicate players
    player_counts = starters_df["player_name"].value_counts()
    duplicates = player_counts[player_counts > 1]
    for player, count in duplicates.items():
        issues.append(
            {
                "type": "duplicate_player",
                "player": player,
                "count": count,
                "description": f"Player {player} appears {count} times in starters",
            }
        )

    # Check for invalid positions in specific slots
    for _, player in starters_df.iterrows():
        slot = player["slot"]
        position = player["position"]

        # QB slot should only have QB position
        if slot == "QB" and position != "QB":
            issues.append(
                {
                    "type": "invalid_position_in_slot",
                    "slot": slot,
                    "position": position,
                    "player": player["player_name"],
                    "description": (
                        f"QB slot contains {position} "
                        f"player {player['player_name']}"
                    ),
                }
            )

        # K slot should only have K position
        if slot == "K" and position != "K":
            issues.append(
                {
                    "type": "invalid_position_in_slot",
                    "slot": slot,
                    "position": position,
                    "player": player["player_name"],
                    "description": (
                        f"K slot contains {position} "
                        f"player {player['player_name']}"
                    ),
                }
            )

        # D/ST slot should only have D/ST position
        if slot == "D/ST" and position != "D/ST":
            issues.append(
                {
                    "type": "invalid_position_in_slot",
                    "slot": slot,
                    "position": position,
                    "player": player["player_name"],
                    "description": (
                        f"D/ST slot contains {position} "
                        f"player {player['player_name']}"
                    ),
                }
            )

    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "total_issues": len(issues),
    }


def validate_lineup_file(
    csv_path: str | Path,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Validate RFFL lineup compliance for a boxscores CSV file.

    Args:
        csv_path: Path to boxscores CSV file
        output_path: Optional path for validation report

    Returns:
        Dictionary with validation results
    """
    df = pd.read_csv(csv_path)
    starters = df[df["slot_type"] == "starters"].copy()

    # Group by team-week and validate each lineup
    lineup_issues = []
    valid_lineups = 0
    total_lineups = 0

    team_key = "team_code" if "team_code" in starters.columns else "team_abbrev"
    for (week, matchup, team), lineup_df in starters.groupby(
        ["week", "matchup", team_key]
    ):
        total_lineups += 1
        validation = validate_rffl_lineup(lineup_df)

        if validation["is_valid"]:
            valid_lineups += 1
        else:
            for issue in validation["issues"]:
                lineup_issues.append(
                    {
                        "week": week,
                        "matchup": matchup,
                        team_key: team,
                        "issue_type": issue["type"],
                        "description": issue["description"],
                        **{
                            k: v
                            for k, v in issue.items()
                            if k not in ["type", "description"]
                        },
                    }
                )

    report_path = None
    if lineup_issues and output_path:
        report_path = Path(output_path)
        pd.DataFrame(lineup_issues).to_csv(report_path, index=False)
    elif lineup_issues:
        csv_path_obj = Path(csv_path)
        report_path = (
            csv_path_obj.parent / f"{csv_path_obj.stem}_lineup_validation_report.csv"
        )
        pd.DataFrame(lineup_issues).to_csv(report_path, index=False)

    return {
        "is_valid": len(lineup_issues) == 0,
        "total_lineups": total_lineups,
        "valid_lineups": valid_lineups,
        "invalid_lineups": total_lineups - valid_lineups,
        "total_issues": len(lineup_issues),
        "issues": lineup_issues,
        "report_path": report_path,
    }

