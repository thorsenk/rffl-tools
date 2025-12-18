#!/usr/bin/env python3
"""Fill out a completed season by exporting boxscores and draft data from ESPN API."""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def find_repo_root() -> Path:
    """Find repository root by looking for pyproject.toml."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    raise ValueError("Could not find repository root (no pyproject.toml found)")


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    console.print(f"[cyan]▶[/cyan] {description}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            console.print(f"[dim]{result.stdout.strip()}[/dim]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Failed: {e}[/red]")
        if e.stderr:
            console.print(f"[red]{e.stderr}[/red]")
        return False
    except FileNotFoundError:
        console.print(
            "[red]❌ Command not found. Make sure 'rffl' is installed and in PATH.[/red]"
        )
        return False


def fill_completed_season(
    year: int,
    league: Optional[int] = None,
    repo_root: Optional[Path] = None,
    fill_missing_slots: bool = True,
    require_clean: bool = True,
    start_week: Optional[int] = None,
    end_week: Optional[int] = None,
    skip_draft: bool = False,
    skip_boxscores: bool = False,
    skip_transactions: bool = False,
) -> bool:
    """
    Fill out a completed season by exporting data from ESPN API.

    Args:
        year: Season year (e.g., 2024)
        league: ESPN league ID (defaults to $LEAGUE env var)
        repo_root: Repository root path (auto-detected if None)
        fill_missing_slots: Fill missing starter slots with placeholders
        require_clean: Require clean data validation
        start_week: Start week (default: 1)
        end_week: End week (default: 18)
        skip_draft: Skip draft export
        skip_boxscores: Skip boxscores export

    Returns:
        True if all exports succeeded
    """
    if repo_root is None:
        repo_root = find_repo_root()

    # Get league ID
    league_id = league
    if league_id is None:
        env_league = os.getenv("LEAGUE")
        if env_league and env_league.isdigit():
            league_id = int(env_league)
    if league_id is None:
        console.print(
            "[red]❌ Missing league ID. Pass --league or set $LEAGUE in .env[/red]"
        )
        return False

    season_dir = repo_root / "data" / "seasons" / str(year)
    season_dir.mkdir(parents=True, exist_ok=True)
    (season_dir / "reports").mkdir(parents=True, exist_ok=True)

    console.print(f"\n[bold blue]📊 Filling completed season: {year}[/bold blue]")
    console.print(f"📁 Season directory: {season_dir}")
    console.print(f"🏈 League ID: {league_id}\n")

    # Determine if this is a historical season (2011-2018) or recent season (2019+)
    is_historical = year < 2019

    if is_historical:
        console.print(
            "[yellow]⚠️  Historical season detected (2011-2018)[/yellow]"
        )
        console.print(
            "[yellow]   ESPN has purged detailed boxscore data for these seasons.[/yellow]"
        )
        console.print(
            "[yellow]   Only draft.csv and h2h.csv will be exported.[/yellow]\n"
        )
        # Force skip boxscores for historical seasons
        skip_boxscores = True

    success = True

    # Export boxscores (2019+ only)
    if not skip_boxscores:
        boxscores_path = season_dir / "boxscores.csv"
        cmd = [
            "rffl",
            "core",
            "export",
            "--year",
            str(year),
            "--out",
            str(boxscores_path),
            "--fill-missing-slots" if fill_missing_slots else "--no-fill-missing-slots",
            "--require-clean" if require_clean else "--no-require-clean",
        ]
        if start_week:
            cmd.extend(["--start-week", str(start_week)])
        if end_week:
            cmd.extend(["--end-week", str(end_week)])
        if league_id:
            cmd.extend(["--league", str(league_id)])

        if not run_command(cmd, f"Exporting boxscores for {year}"):
            success = False
        else:
            console.print(f"[green]✅ Boxscores exported: {boxscores_path}[/green]\n")
    else:
        console.print("[yellow]⏭️  Skipping boxscores export[/yellow]\n")

    # Export draft
    if not skip_draft:
        draft_path = season_dir / "draft.csv"
        cmd = [
            "rffl",
            "core",
            "draft",
            "--year",
            str(year),
            "--out",
            str(draft_path),
        ]
        if league_id:
            cmd.extend(["--league", str(league_id)])

        if not run_command(cmd, f"Exporting draft for {year}"):
            success = False
        else:
            console.print(f"[green]✅ Draft exported: {draft_path}[/green]\n")
    else:
        console.print("[yellow]⏭️  Skipping draft export[/yellow]\n")

    # Export h2h for historical seasons (2011-2018)
    if is_historical:
        h2h_path = season_dir / "h2h.csv"
        cmd = [
            "rffl",
            "core",
            "h2h",
            "--year",
            str(year),
            "--out",
            str(h2h_path),
        ]
        if league_id:
            cmd.extend(["--league", str(league_id)])

        if not run_command(cmd, f"Exporting h2h matchups for {year}"):
            success = False
        else:
            console.print(f"[green]✅ H2H matchups exported: {h2h_path}[/green]\n")

    # Export transactions (2018+ only, optional)
    if not skip_transactions and not is_historical:
        transactions_path = season_dir / "transactions.csv"
        cmd = [
            "rffl",
            "core",
            "transactions",
            "--year",
            str(year),
            "--out",
            str(transactions_path),
        ]
        if league_id:
            cmd.extend(["--league", str(league_id)])

        # Check if credentials are available
        has_credentials = bool(os.getenv("ESPN_S2") and os.getenv("SWID"))
        if has_credentials:
            console.print(
                "[dim]   Using ESPN_S2 and SWID credentials from environment[/dim]"
            )

        if not run_command(cmd, f"Exporting transactions for {year}"):
            # Don't fail the whole process if transactions fail
            if not has_credentials:
                console.print(
                    "[yellow]⚠️  Transactions export failed (authentication may be required)[/yellow]"
                )
                console.print(
                    "[yellow]   Set ESPN_S2 and SWID environment variables to authenticate[/yellow]"
                )
            else:
                console.print(
                    "[yellow]⚠️  Transactions export failed (data may not be available for this season)[/yellow]"
                )
            console.print(
                "[yellow]   This is optional - continuing with other exports...[/yellow]\n"
            )
        else:
            console.print(
                f"[green]✅ Transactions exported: {transactions_path}[/green]\n"
            )
    elif is_historical and not skip_transactions:
        console.print(
            "[yellow]⏭️  Skipping transactions export (not available for historical seasons)[/yellow]\n"
        )
    elif skip_transactions:
        console.print("[yellow]⏭️  Skipping transactions export[/yellow]\n")

    # Summary
    if success:
        console.print("[bold green]✨ Season export completed successfully![/bold green]\n")
        if is_historical:
            console.print(
                "[yellow]📝 Note: Historical seasons (2011-2018) only have draft and h2h data.[/yellow]"
            )
            console.print(
                "[yellow]   Detailed boxscores are not available (ESPN has purged this data).[/yellow]\n"
            )
        else:
            console.print(
                "[yellow]📝 Note: Report files (boxscores_normalized.csv, teamweek_unified.csv)"
            )
            console.print(
                "[yellow]   need to be generated separately using post-processing scripts.[/yellow]\n"
            )
    else:
        console.print("[bold red]❌ Some exports failed. Check errors above.[/bold red]\n")

    return success


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Fill out a completed season by exporting data from ESPN API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fill out recent season 2024 (uses $LEAGUE env var)
  python scripts/fill_completed_season.py 2024

  # Fill out recent season 2023 with specific league ID
  python scripts/fill_completed_season.py 2023 --league 323196

  # Fill out recent season 2022, weeks 1-17 only
  python scripts/fill_completed_season.py 2022 --start-week 1 --end-week 17

  # Fill out historical season 2011 (draft + h2h only, no detailed boxscores)
  python scripts/fill_completed_season.py 2011 --league 323196

  # Export only boxscores (skip draft) - 2019+ only
  python scripts/fill_completed_season.py 2024 --skip-draft

  # Export only draft (skip boxscores)
  python scripts/fill_completed_season.py 2024 --skip-boxscores

  # Export with transactions (2018+ only, may require authentication)
  python scripts/fill_completed_season.py 2024

  # Skip transactions export
  python scripts/fill_completed_season.py 2024 --skip-transactions

Note: Historical seasons (2011-2018) automatically skip boxscores and transactions export
      since ESPN has purged this data. Only draft.csv and h2h.csv are available.
        """,
    )
    parser.add_argument(
        "year",
        type=int,
        help="Season year (e.g., 2024)",
    )
    parser.add_argument(
        "--league",
        type=int,
        help="ESPN league ID (defaults to $LEAGUE env var)",
    )
    parser.add_argument(
        "--start-week",
        type=int,
        help="Start week (default: 1)",
    )
    parser.add_argument(
        "--end-week",
        type=int,
        help="End week (default: 18)",
    )
    parser.add_argument(
        "--no-fill-missing-slots",
        action="store_true",
        help="Don't fill missing starter slots with placeholders",
    )
    parser.add_argument(
        "--no-require-clean",
        action="store_true",
        help="Don't require clean data validation",
    )
    parser.add_argument(
        "--skip-draft",
        action="store_true",
        help="Skip draft export",
    )
    parser.add_argument(
        "--skip-boxscores",
        action="store_true",
        help="Skip boxscores export",
    )
    parser.add_argument(
        "--skip-transactions",
        action="store_true",
        help="Skip transactions export (2018+ only)",
    )

    args = parser.parse_args()

    try:
        success = fill_completed_season(
            year=args.year,
            league=args.league,
            fill_missing_slots=not args.no_fill_missing_slots,
            require_clean=not args.no_require_clean,
            start_week=args.start_week,
            end_week=args.end_week,
            skip_draft=args.skip_draft,
            skip_boxscores=args.skip_boxscores,
            skip_transactions=args.skip_transactions,
        )
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()

