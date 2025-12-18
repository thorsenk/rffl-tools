#!/usr/bin/env python3
"""Scaffold a new season directory structure based on the completed season template."""

import argparse
import sys
from pathlib import Path


def scaffold_season(year: int, repo_root: Path | None = None) -> Path:
    """
    Create a new season directory structure.

    Args:
        year: Season year (e.g., 2024)
        repo_root: Repository root path (auto-detected if None)

    Returns:
        Path to the created season directory
    """
    if repo_root is None:
        # Find repo root by looking for pyproject.toml
        current = Path.cwd()
        for parent in [current, *current.parents]:
            if (parent / "pyproject.toml").exists():
                repo_root = parent
                break
        if repo_root is None:
            raise ValueError("Could not find repository root (no pyproject.toml found)")

    season_dir = repo_root / "data" / "seasons" / str(year)
    reports_dir = season_dir / "reports"

    # Create directories
    season_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Determine if this is a historical season (2011-2018) or recent season (2019+)
    # ESPN only maintains detailed boxscores for the past 6 years (5 past + current)
    # Historical seasons only have draft.csv and h2h.csv
    is_historical = year < 2019

    # Common files for all seasons
    files_to_create = {
        season_dir / "draft.csv": (
            "year,round,round_pick,team_abbrev,player_id,player_name,bid_amount,keeper,nominating_team\n"
        ),
        reports_dir / f"{year}-Draft-Snake-Canonicals.csv": (
            "year,round,round_pick,team_abbrev,player_id,player_name,bid_amount,keeper,nominating_team\n"
        ),
    }

    if is_historical:
        # Historical seasons (2011-2018): draft + h2h only
        files_to_create.update({
            season_dir / "h2h.csv": (
                "week,matchup,home_team,away_team,home_score,away_score,winner,margin\n"
            ),
            reports_dir / "h2h_teamweek.csv": (
                "season_year,week,matchup,team_code,opponent_code,team_score,opp_score,result,margin\n"
            ),
        })
        print(f"📅 Historical season detected ({year}): Creating draft + h2h structure")
        print("   ⚠️  Note: Detailed boxscores not available (ESPN has purged this data)")
    else:
        # Recent seasons (2019+): full boxscore data available
        files_to_create.update({
            season_dir / "boxscores.csv": (
                "season_year,week,matchup,team_code,is_co_owned?,team_owner_1,team_owner_2,"
                "team_projected_total,team_actual_total,slot_type,slot,player_name,nfl_team,"
                "position,is_placeholder,issue_flag,rs_projected_pf,rs_actual_pf\n"
            ),
            season_dir / "transactions.csv": (
                "season_year,bid_amount,date,effective_date,id,is_pending,rating,status,type,"
                "team_id,team_code,member_id,player_id,player_name,to_team_id,to_team_code,"
                "from_team_id,from_team_code\n"
            ),
            reports_dir / "boxscores_normalized.csv": (
                "season_year,week,matchup,team_code,is_co_owned?,team_owner_1,team_owner_2,"
                "team_projected_total,team_actual_total,slot_type,slot,player_name,nfl_team,"
                "position,is_placeholder,issue_flag,rs_projected_pf,rs_actual_pf\n"
            ),
            reports_dir / "teamweek_unified.csv": (
                "season_year,week,matchup,team_code,is_co_owned?,team_owner_1,team_owner_2,"
                "opponent_code,opp_is_co_owned?,opp_owner_1,opp_owner_2,team_projected_total,"
                "team_actual_total,opp_actual_total,result,margin\n"
            ),
        })
        print(f"📅 Recent season detected ({year}): Creating full boxscore structure")
        print("   📝 Note: transactions.csv included (may require authentication to fill)")

    created_files = []
    for file_path, header in files_to_create.items():
        if file_path.exists():
            print(f"⚠️  File already exists: {file_path}")
        else:
            file_path.write_text(header)
            created_files.append(file_path)
            print(f"✅ Created: {file_path}")

    if created_files:
        print(f"\n✨ Season {year} directory scaffolded successfully!")
        print(f"📁 Location: {season_dir}")
    else:
        print(f"\n📁 Season {year} directory already exists: {season_dir}")

    return season_dir


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scaffold a new season directory structure"
    )
    parser.add_argument(
        "year",
        type=int,
        help="Season year (e.g., 2025)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Repository root path (auto-detected if not provided)",
    )

    args = parser.parse_args()

    try:
        scaffold_season(args.year, args.repo_root)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

