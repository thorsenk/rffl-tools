"""Data validation logic."""

from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from .exceptions import ValidationError


def validate_boxscores(
    csv_path: str | Path,
    tolerance: float = 0.0,
) -> dict[str, Any]:
    """
    Validate exported boxscore data for consistency and completeness.

    Args:
        csv_path: Path to boxscores CSV file
        tolerance: Allowed difference for sums

    Returns:
        Dictionary with validation results:
        - is_valid: bool
        - issues: list of issue dictionaries
        - report_path: Path to validation report (if issues found)
    """
    df = pd.read_csv(csv_path)
    starters = df[df["slot_type"] == "starters"].copy()
    team_key = "team_code" if "team_code" in starters.columns else "team_abbrev"
    agg = starters.groupby(["week", "matchup", team_key], as_index=False).agg(
        team_projected_total=("team_projected_total", "first"),
        team_actual_total=("team_actual_total", "first"),
        starters_proj_sum=("rs_projected_pf", "sum"),
        starters_actual_sum=("rs_actual_pf", "sum"),
        starter_count=("slot", "count"),
        slots_list=("slot", lambda s: ",".join(sorted(s))),
    )
    agg["proj_diff"] = (agg["starters_proj_sum"] - agg["team_projected_total"]).round(2)
    agg["act_diff"] = (agg["starters_actual_sum"] - agg["team_actual_total"]).round(2)

    bad_proj = agg[agg["proj_diff"].abs() > tolerance]
    bad_act = agg[agg["act_diff"].abs() > tolerance]
    bad_cnt = agg[agg["starter_count"] != 9]

    issues = []
    if not bad_proj.empty:
        issues.extend(
            [
                {
                    "type": "proj_mismatch",
                    "week": row["week"],
                    "matchup": row["matchup"],
                    "team": row[team_key],
                    "diff": row["proj_diff"],
                }
                for _, row in bad_proj.iterrows()
            ]
        )
    if not bad_act.empty:
        issues.extend(
            [
                {
                    "type": "actual_mismatch",
                    "week": row["week"],
                    "matchup": row["matchup"],
                    "team": row[team_key],
                    "diff": row["act_diff"],
                }
                for _, row in bad_act.iterrows()
            ]
        )
    if not bad_cnt.empty:
        issues.extend(
            [
                {
                    "type": "starter_count",
                    "week": row["week"],
                    "matchup": row["matchup"],
                    "team": row[team_key],
                    "count": row["starter_count"],
                }
                for _, row in bad_cnt.iterrows()
            ]
        )

    report_path = None
    if issues:
        csv_path_obj = Path(csv_path)
        report_path = csv_path_obj.parent / f"{csv_path_obj.stem}_validation_report.csv"
        pd.concat(
            [
                bad_proj.assign(issue="proj_mismatch"),
                bad_act.assign(issue="actual_mismatch"),
                bad_cnt.assign(issue="starter_count"),
            ],
            ignore_index=True,
        ).to_csv(report_path, index=False)

    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "total_issues": len(issues),
        "report_path": report_path,
        "team_weeks": len(agg),
        "proj_mismatches": len(bad_proj),
        "actual_mismatches": len(bad_act),
        "bad_counts": len(bad_cnt),
    }

