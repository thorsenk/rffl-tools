"""Unified CLI for RFFL tools."""

import os
from pathlib import Path

import typer
from dotenv import load_dotenv, find_dotenv
from rich.console import Console

from .core.api import ESPNCredentials
from .core.draft import export_draft
from .core.exceptions import RecipeLockedError
from .core.export import export_boxscores
from .core.h2h import export_h2h
from .core.inbox import ensure_inbox_clean, list_inbox_files
from .core.lineup import validate_lineup_file
from .core.transactions import export_transactions
from .core.validation import validate_boxscores
from .recipes.loader import find_repo_root, resolve_output_path
from .recipes.migrate import migrate_recipe
from .recipes.models import load_recipe, validate_recipe_paths
from .recipes.runner import RecipeRunner
from .recipes.wizard import RecipeWizard
from .moa import MOADispatcher

load_dotenv(find_dotenv(), override=False)

app = typer.Typer(add_completion=False, help="RFFL Fantasy Football data toolkit")
console = Console()

# Command groups
core_app = typer.Typer(help="Core data operations")
recipe_app = typer.Typer(help="Recipe orchestration")
live_app = typer.Typer(help="Live scoring features")
forensic_app = typer.Typer(help="Forensic investigation commands")
utils_app = typer.Typer(help="Utility commands")

app.add_typer(core_app, name="core", help="Core commands")
app.add_typer(recipe_app, name="recipe", help="Recipe commands")
app.add_typer(live_app, name="live", help="Live commands")
app.add_typer(forensic_app, name="forensic", help="Forensic commands")
app.add_typer(utils_app, name="utils", help="Utility commands")


# Core commands
@core_app.command("export")
def cmd_export(
    league: int | None = typer.Option(None, help="ESPN leagueId (defaults to $LEAGUE)"),
    year: int = typer.Option(..., help="Season year"),
    out: str = typer.Option(None, help="Output CSV path"),
    start_week: int = typer.Option(None, help="Start week (default auto)"),
    end_week: int = typer.Option(None, help="End week (default auto)"),
    fill_missing_slots: bool = typer.Option(
        False, help="Insert 0-pt placeholders for missing required starter slots"
    ),
    require_clean: bool = typer.Option(
        False, help="Validate in-memory and fail if sums/counts are not clean"
    ),
    tolerance: float = typer.Option(
        0.0,
        help="Allowed |sum(starters rs_projected_pf) - team_projected_total| for --require-clean",
    ),
):
    """Export ESPN fantasy football boxscores to CSV format."""
    league_id = league
    if league_id is None:
        env_league = os.getenv("LEAGUE")
        if env_league and env_league.isdigit():
            league_id = int(env_league)
    if league_id is None:
        console.print("[red]❌ Missing league id. Pass --league or set $LEAGUE in .env[/red]")
        raise typer.Exit(1)

    try:
        repo_root = find_repo_root()
        credentials = ESPNCredentials(
            espn_s2=os.getenv("ESPN_S2"),
            swid=os.getenv("SWID"),
        )
        output_path = resolve_output_path(out or f"data/seasons/{year}/boxscores.csv")
        path = export_boxscores(
            league_id=league_id,
            year=year,
            output_path=output_path,
            start_week=start_week,
            end_week=end_week,
            fill_missing_slots=fill_missing_slots,
            require_clean=require_clean,
            tolerance=tolerance,
            credentials=credentials,
            public_only=True,  # Default to public-only
            repo_root=repo_root,
        )
    except Exception as e:
        console.print(f"[red]❌ Export failed: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✅ Wrote {path}[/green]")


@core_app.command("h2h")
def cmd_h2h(
    league: int | None = typer.Option(None, help="ESPN leagueId (defaults to $LEAGUE)"),
    year: int = typer.Option(..., help="Season year"),
    out: str = typer.Option(None, help="Output CSV path"),
    start_week: int = typer.Option(None, help="Start week (default auto)"),
    end_week: int = typer.Option(None, help="End week (default auto)"),
):
    """Export simplified head-to-head matchup results."""
    league_id = league
    if league_id is None:
        env_league = os.getenv("LEAGUE")
        if env_league and env_league.isdigit():
            league_id = int(env_league)
    if league_id is None:
        console.print("[red]❌ Missing league id. Pass --league or set $LEAGUE in .env[/red]")
        raise typer.Exit(1)

    try:
        repo_root = find_repo_root()
        output_path = resolve_output_path(out or f"data/seasons/{year}/h2h.csv")
        path = export_h2h(
            league_id=league_id,
            year=year,
            output_path=output_path,
            start_week=start_week,
            end_week=end_week,
            credentials=None,
            public_only=True,
        )
    except Exception as e:
        console.print(f"[red]❌ H2H export failed: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✅ Wrote {path}[/green]")


@core_app.command("draft")
def cmd_draft(
    league: int | None = typer.Option(None, help="ESPN leagueId (defaults to $LEAGUE)"),
    year: int = typer.Option(..., help="Season year"),
    out: str = typer.Option(None, help="Output CSV path"),
):
    """Export season draft results to CSV (snake or auction)."""
    league_id = league
    if league_id is None:
        env_league = os.getenv("LEAGUE")
        if env_league and env_league.isdigit():
            league_id = int(env_league)
    if league_id is None:
        console.print("[red]❌ Missing league id. Pass --league or set $LEAGUE in .env[/red]")
        raise typer.Exit(1)

    try:
        repo_root = find_repo_root()
        output_path = resolve_output_path(out or f"data/seasons/{year}/draft.csv")
        path = export_draft(
            league_id=league_id,
            year=year,
            output_path=output_path,
            credentials=None,
            public_only=True,
        )
    except Exception as e:
        console.print(f"[red]❌ Draft export failed: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✅ Wrote {path}[/green]")


@core_app.command("transactions")
def cmd_transactions(
    league: int | None = typer.Option(None, help="ESPN leagueId (defaults to $LEAGUE)"),
    year: int = typer.Option(..., help="Season year"),
    out: str = typer.Option(None, help="Output CSV path"),
):
    """Export transaction history."""
    league_id = league
    if league_id is None:
        env_league = os.getenv("LEAGUE")
        if env_league and env_league.isdigit():
            league_id = int(env_league)
    if league_id is None:
        console.print("[red]❌ Missing league id. Pass --league or set $LEAGUE in .env[/red]")
        raise typer.Exit(1)

    try:
        repo_root = find_repo_root()
        output_path = resolve_output_path(out or f"data/seasons/{year}/transactions.csv")
        # Use credentials from environment if available
        credentials = ESPNCredentials(
            espn_s2=os.getenv("ESPN_S2"),
            swid=os.getenv("SWID"),
        )
        # If credentials are provided, use them (don't force public_only)
        public_only = not credentials.is_authenticated
        path = export_transactions(
            league_id=league_id,
            year=year,
            output_path=output_path,
            credentials=credentials,
            public_only=public_only,
            repo_root=repo_root,
        )
    except Exception as e:
        console.print(f"[red]❌ Transactions export failed: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✅ Wrote {path}[/green]")


@core_app.command("stat-corrections")
def cmd_stat_corrections(
    league: int | None = typer.Option(None, help="ESPN leagueId (defaults to $LEAGUE)"),
    year: int = typer.Option(..., help="Season year"),
    week: int | None = typer.Option(None, help="Specific week (defaults to all weeks 1-18)"),
    out: str = typer.Option(None, help="Output CSV path"),
):
    """Export stat corrections history (requires authentication)."""
    league_id = league
    if league_id is None:
        env_league = os.getenv("LEAGUE")
        if env_league and env_league.isdigit():
            league_id = int(env_league)
    if league_id is None:
        console.print("[red]❌ Missing league id. Pass --league or set $LEAGUE in .env[/red]")
        raise typer.Exit(1)

    try:
        from .core.stat_corrections import export_stat_corrections

        credentials = ESPNCredentials(
            espn_s2=os.getenv("ESPN_S2"),
            swid=os.getenv("SWID"),
        )
        
        if not credentials.is_authenticated:
            console.print(
                "[red]❌ Stat corrections require authentication. Set ESPN_S2 and SWID in .env[/red]"
            )
            raise typer.Exit(1)

        repo_root = find_repo_root()
        output_path = resolve_output_path(out or f"data/seasons/{year}/stat_corrections.csv")
        
        start_week = week if week else 1
        end_week = week if week else 18
        
        path = export_stat_corrections(
            league_id=league_id,
            year=year,
            output_path=output_path,
            credentials=credentials,
            start_week=start_week,
            end_week=end_week,
        )
    except Exception as e:
        console.print(f"[red]❌ Stat corrections export failed: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✅ Wrote {path}[/green]")


@core_app.command("historical-rosters")
def cmd_historical_rosters(
    league: int | None = typer.Option(None, help="ESPN leagueId (defaults to $LEAGUE)"),
    year: int = typer.Option(..., help="Season year (2011-2018)"),
    out: str = typer.Option(None, help="Output CSV path"),
):
    """Export END-OF-SEASON roster compositions for historical seasons (2011-2018)."""
    if year >= 2019:
        console.print(
            "[red]❌ Use 'export' command for 2019+ seasons. This command is for 2011-2018.[/red]"
        )
        raise typer.Exit(1)

    league_id = league
    if league_id is None:
        env_league = os.getenv("LEAGUE")
        if env_league and env_league.isdigit():
            league_id = int(env_league)
    if league_id is None:
        console.print("[red]❌ Missing league id. Pass --league or set $LEAGUE in .env[/red]")
        raise typer.Exit(1)

    try:
        from .core.rosters import export_historical_rosters

        repo_root = find_repo_root()
        output_path = resolve_output_path(out or f"data/seasons/{year}/rosters.csv")
        path = export_historical_rosters(
            league_id=league_id,
            year=year,
            output_path=output_path,
            credentials=None,
            public_only=True,
            repo_root=repo_root,
        )
    except Exception as e:
        console.print(f"[red]❌ Historical rosters export failed: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✅ Wrote {path}[/green]")


@core_app.command("validate")
def cmd_validate(
    csv_path: str = typer.Argument(..., help="validated_boxscores_YYYY.csv"),
    tolerance: float = typer.Option(
        0.0,
        help="Allowed |sum(starters rs_projected_pf) - team_projected_total| (e.g., 0.02)",
    ),
):
    """Validate exported boxscore data for consistency and completeness."""
    result = validate_boxscores(csv_path, tolerance=tolerance)

    console.print(f"Team-weeks: {result['team_weeks']}")
    console.print(f"❌ proj mismatches > {tolerance}: {result['proj_mismatches']}")
    console.print(f"❌ actual mismatches > {tolerance}: {result['actual_mismatches']}")
    console.print(f"❌ starter_count != 9: {result['bad_counts']}")

    if result["is_valid"]:
        console.print("[green]✅ clean[/green]")
    else:
        if result["report_path"]:
            console.print(f"[yellow]↳ wrote detail: {result['report_path']}[/yellow]")


@core_app.command("validate-lineup")
def cmd_validate_lineup(
    csv_path: str = typer.Argument(..., help="validated_boxscores_YYYY.csv"),
    out: str = typer.Option(None, help="Output report path"),
):
    """Validate RFFL lineup compliance (1 QB, 2 RB, 2 WR, 1 TE, 1 FLEX, 1 D/ST, 1 K)."""
    result = validate_lineup_file(csv_path, output_path=out)

    console.print("RFFL Lineup Validation Report")
    console.print("=" * 50)
    console.print(f"Total lineups checked: {result['total_lineups']}")
    console.print(f"[green]✅ Valid lineups: {result['valid_lineups']}[/green]")
    console.print(f"[red]❌ Invalid lineups: {result['invalid_lineups']}[/red]")
    console.print(f"Total issues found: {result['total_issues']}")

    if result["issues"]:
        console.print("\nIssues by type:")
        issue_types: dict[str, int] = {}
        for issue in result["issues"]:
            issue_type = issue["issue_type"]
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        for issue_type, count in issue_types.items():
            console.print(f"  {issue_type}: {count}")

    if result["report_path"]:
        console.print(f"\n[yellow]Report written: {result['report_path']}[/yellow]")


# Recipe commands
@recipe_app.command("run")
def cmd_recipe_run(
    recipe_path: str = typer.Argument(..., help="Path to recipe YAML file"),
    dry_run: bool = typer.Option(False, help="Show what would be executed without running"),
):
    """Execute a recipe."""
    recipe_file = Path(recipe_path)
    if not recipe_file.exists():
        console.print(f"[red]❌ Recipe not found: {recipe_path}[/red]")
        raise typer.Exit(1)

    try:
        recipe = load_recipe(recipe_file)
        repo_root = find_repo_root(recipe_file.parent)
        runner = RecipeRunner(repo_root=repo_root)
        success = runner.run_recipe(recipe, recipe_path=recipe_file, dry_run=dry_run)
        if success:
            console.print("[green]✅ Recipe executed successfully[/green]")
        else:
            console.print("[red]❌ Recipe execution failed[/red]")
            raise typer.Exit(1)
    except RecipeLockedError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Recipe execution failed: {e}[/red]")
        raise typer.Exit(1)


@recipe_app.command("wizard")
def cmd_recipe_wizard(
    baseline: str | None = typer.Option(None, help="Baseline recipe name"),
    profile: str = typer.Option("active", help="Recipe profile (active/preview)"),
):
    """Interactive wizard for creating recipes."""
    try:
        repo_root = find_repo_root()
        wizard = RecipeWizard(repo_root=repo_root)
        wizard.run(baseline_name=baseline, profile=profile)
    except Exception as e:
        console.print(f"[red]❌ Wizard failed: {e}[/red]")
        raise typer.Exit(1)


@recipe_app.command("list")
def cmd_recipe_list(
    all: bool = typer.Option(False, "--all", help="List all recipes including baselines"),
):
    """List available recipes."""
    try:
        repo_root = find_repo_root()
        wizard = RecipeWizard(repo_root=repo_root)
        if all:
            wizard.list_baselines()
        # TODO: List local recipes
    except Exception as e:
        console.print(f"[red]❌ Failed to list recipes: {e}[/red]")
        raise typer.Exit(1)


@recipe_app.command("validate")
def cmd_recipe_validate(
    recipe_path: str = typer.Argument(..., help="Path to recipe YAML file"),
):
    """Validate a recipe file."""
    recipe_file = Path(recipe_path)
    if not recipe_file.exists():
        console.print(f"[red]❌ Recipe not found: {recipe_path}[/red]")
        raise typer.Exit(1)

    try:
        recipe = load_recipe(recipe_file)
        errors = validate_recipe_paths(recipe, recipe_path=recipe_file)
        if errors:
            console.print("[red]❌ Recipe validation failed:[/red]")
            for error in errors:
                console.print(f"  - {error}")
            raise typer.Exit(1)
        else:
            console.print("[green]✅ Recipe is valid[/green]")
    except Exception as e:
        console.print(f"[red]❌ Recipe validation failed: {e}[/red]")
        raise typer.Exit(1)


@recipe_app.command("migrate")
def cmd_recipe_migrate(
    recipe_path: str = typer.Argument(..., help="Path to recipe YAML file"),
    dry_run: bool = typer.Option(False, help="Show what would change without modifying"),
):
    """Migrate recipe from ${DATA_ROOT} to relative paths."""
    recipe_file = Path(recipe_path)
    if not recipe_file.exists():
        console.print(f"[red]❌ Recipe not found: {recipe_path}[/red]")
        raise typer.Exit(1)

    try:
        changes = migrate_recipe(recipe_file, dry_run=dry_run)
        for change in changes:
            console.print(f"  {change}")
        if not dry_run:
            console.print("[green]✅ Recipe migrated successfully[/green]")
    except Exception as e:
        console.print(f"[red]❌ Migration failed: {e}[/red]")
        raise typer.Exit(1)


# Live commands
@live_app.command("scores")
def cmd_live_scores(
    league: int | None = typer.Option(None, help="ESPN leagueId (defaults to $LEAGUE)"),
    season: int = typer.Option(..., help="Season year"),
    scoring_period: int | None = typer.Option(None, help="Scoring period (defaults to current)"),
    mode: str = typer.Option("scoreboard", help="Output mode: scoreboard, boxscore, combined"),
    save_json: str | None = typer.Option(None, help="Save raw JSON to path"),
):
    """Fetch live scores."""
    league_id = league
    if league_id is None:
        env_league = os.getenv("LEAGUE")
        if env_league and env_league.isdigit():
            league_id = int(env_league)
    if league_id is None:
        console.print("[red]❌ Missing league id. Pass --league or set $LEAGUE in .env[/red]")
        raise typer.Exit(1)

    if mode not in ("scoreboard", "boxscore", "combined"):
        console.print(f"[red]❌ Invalid mode: {mode}. Must be scoreboard, boxscore, or combined[/red]")
        raise typer.Exit(1)

    try:
        from .live.scores import fetch_and_render_live_scores, LiveCommandMode

        payload = fetch_and_render_live_scores(
            league_id=league_id,
            season=season,
            scoring_period=scoring_period,
            mode=mode,  # type: ignore
            timeout=10.0,
            espn_s2=os.getenv("ESPN_S2"),
            swid=os.getenv("SWID"),
        )

        if save_json:
            import json
            json_path = Path(save_json)
            json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(json_path, "w") as f:
                json.dump(payload, f, indent=2)
            console.print(f"[green]✅ Saved JSON to {json_path}[/green]")

    except Exception as e:
        console.print(f"[red]❌ Live scores failed: {e}[/red]")
        raise typer.Exit(1)


@live_app.command("report")
def cmd_live_report(
    league: int | None = typer.Option(None, help="ESPN leagueId (defaults to $LEAGUE)"),
    season: int = typer.Option(..., help="Season year"),
    scoring_period: int | None = typer.Option(None, help="Scoring period (defaults to current)"),
    all_matchups: bool = typer.Option(False, "--all-matchups", help="Show all matchups"),
    team_id: int | None = typer.Option(None, help="Filter by team ID"),
    matchup_id: int | None = typer.Option(None, help="Filter by matchup ID"),
):
    """Generate live matchup report."""
    league_id = league
    if league_id is None:
        env_league = os.getenv("LEAGUE")
        if env_league and env_league.isdigit():
            league_id = int(env_league)
    if league_id is None:
        console.print("[red]❌ Missing league id. Pass --league or set $LEAGUE in .env[/red]")
        raise typer.Exit(1)

    try:
        from .live.report import generate_live_matchup_report

        report = generate_live_matchup_report(
            league_id=league_id,
            season=season,
            scoring_period=scoring_period,
            team_id=team_id,
            matchup_id=matchup_id,
            all_matchups=all_matchups,
            timeout=10.0,
            espn_s2=os.getenv("ESPN_S2"),
            swid=os.getenv("SWID"),
        )
        console.print(report)

    except Exception as e:
        console.print(f"[red]❌ Live report failed: {e}[/red]")
        raise typer.Exit(1)


@live_app.command("korm")
def cmd_korm(
    week: int = typer.Argument(..., help="Week number"),
    league: int | None = typer.Option(None, help="ESPN leagueId (defaults to $LEAGUE)"),
    season: int = typer.Option(..., help="Season year"),
    history_dir: str | None = typer.Option(None, help="Path to KORM history directory"),
    output: str | None = typer.Option(None, help="Output file path for report"),
):
    """Generate KORM (King of the Red Marks) live update report."""
    league_id = league
    if league_id is None:
        env_league = os.getenv("LEAGUE")
        if env_league and env_league.isdigit():
            league_id = int(env_league)
    if league_id is None:
        console.print("[red]❌ Missing league id. Pass --league or set $LEAGUE in .env[/red]")
        raise typer.Exit(1)

    try:
        from .live.korm import KORMTracker, KORMReportGenerator, load_historical_korm_state
        from .live.scores import LiveScoreClient

        # Load historical KORM state
        if history_dir:
            history_path = Path(history_dir)
        else:
            repo_root = find_repo_root()
            history_path = repo_root / "data" / "korm_history"
            history_path.mkdir(parents=True, exist_ok=True)

        tracker = load_historical_korm_state(history_path)

        # Fetch live scores for the week
        client = LiveScoreClient(
            league_id=league_id,
            season=season,
            espn_s2=os.getenv("ESPN_S2"),
            swid=os.getenv("SWID"),
        )

        scoring_period = week
        data = client.fetch_scoreboard(scoring_period, include_boxscore=True, include_live=True)

        # Convert to WeekScore objects
        from .live.korm import WeekScore
        scores = []
        teams = data.get("teams") or []
        for team in teams:
            team_id = team.get("id")
            team_name = team.get("name") or f"Team {team_id}"
            points_by_period = team.get("pointsByScoringPeriod") or {}
            actual_score = float(points_by_period.get(str(scoring_period)) or team.get("totalPoints") or 0.0)
            
            # Get projected score (simplified - would need more logic for live projections)
            projected_score = actual_score  # Placeholder - would calculate from live player data
            
            scores.append(WeekScore(
                team_name=team_name,
                week=week,
                actual_score=actual_score,
                projected_score=projected_score,
                baseline_projection=projected_score,  # Placeholder
                completion_pct=100.0,  # Placeholder
                players_remaining=0,  # Placeholder
                total_players=9,  # Placeholder
            ))

        # Generate report
        generator = KORMReportGenerator(tracker)
        output_path = Path(output) if output else None
        report = generator.generate_live_report(week, scores, output_path)

        console.print(report)

        if output_path:
            console.print(f"[green]✅ Report saved to {output_path}[/green]")

    except Exception as e:
        console.print(f"[red]❌ KORM report failed: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        raise typer.Exit(1)


# KORM historical processing commands
korm_app = typer.Typer(help="KORM historical results processing")
app.add_typer(korm_app, name="korm", help="KORM commands")


@korm_app.command("generate")
def cmd_korm_generate(
    year: int = typer.Argument(..., help="Season year to process (e.g., 2024)"),
    output_dir: str | None = typer.Option(
        None, "--output", "-o", help="Output directory (defaults to season dir)"
    ),
):
    """Generate KORM results for a single season."""
    from .core.korm_processor import process_and_save_korm_season

    try:
        repo_root = find_repo_root()
        out_dir = Path(output_dir) if output_dir else None

        console.print(f"[cyan]Processing KORM for {year}...[/cyan]")
        json_path, md_path = process_and_save_korm_season(year, repo_root, out_dir)

        console.print(f"[green]✅ Generated:[/green]")
        console.print(f"   JSON: {json_path}")
        console.print(f"   Markdown: {md_path}")

    except FileNotFoundError as e:
        console.print(f"[red]❌ Data not found: {e}[/red]")
        console.print("[yellow]Hint: Run 'python scripts/fill_completed_season.py {year}' first[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ KORM processing failed: {e}[/red]")
        raise typer.Exit(1)


@korm_app.command("generate-all")
def cmd_korm_generate_all(
    start_year: int = typer.Option(2018, help="First season to process"),
    end_year: int = typer.Option(2025, help="Last season to process"),
):
    """Generate KORM results for all seasons (2018-2025)."""
    from .core.korm_processor import process_and_save_korm_season, SEASON_CONFIG

    try:
        repo_root = find_repo_root()

        console.print(f"[cyan]Processing KORM for seasons {start_year}-{end_year}...[/cyan]")
        console.print()

        results = []
        for year in range(start_year, end_year + 1):
            if year not in SEASON_CONFIG:
                console.print(f"[yellow]⏭️  Skipping {year} (no config)[/yellow]")
                continue

            try:
                json_path, md_path = process_and_save_korm_season(year, repo_root)
                console.print(f"[green]✅ {year}[/green] → {md_path.name}")
                results.append((year, "success"))
            except FileNotFoundError as e:
                console.print(f"[yellow]⚠️  {year}[/yellow] - {e}")
                results.append((year, "missing"))
            except Exception as e:
                console.print(f"[red]❌ {year}[/red] - {e}")
                results.append((year, "error"))

        console.print()
        success = sum(1 for _, status in results if status == "success")
        console.print(f"[cyan]Processed {success}/{len(results)} seasons[/cyan]")

    except Exception as e:
        console.print(f"[red]❌ KORM batch processing failed: {e}[/red]")
        raise typer.Exit(1)


@korm_app.command("standings")
def cmd_korm_standings(
    year: int = typer.Argument(..., help="Season year"),
    week: int | None = typer.Option(None, help="Show standings after specific week"),
):
    """Show KORM standings for a season."""
    from .core.korm_processor import load_weekly_scores, process_korm_season

    try:
        repo_root = find_repo_root()
        weekly_scores = load_weekly_scores(year, repo_root)
        result = process_korm_season(year, weekly_scores)

        if week:
            console.print(f"[bold]KORM Standings After Week {week} - {year}[/bold]")
            # Find week result and validate week exists
            week_result = next((w for w in result.weeks if w.week == week), None)
            if not week_result:
                console.print(f"[red]Week {week} not found[/red]")
                raise typer.Exit(1)
            
            # Reconstruct team state at this week
            # Track cumulative strikes and eliminations up to this week
            team_strikes: dict[str, int] = {team: 0 for team in result.teams}
            eliminated_teams: set[str] = set()
            
            # Use week_result to ensure we process up to and including the requested week
            for w in result.weeks:
                if w.week > week_result.week:
                    break
                # Add strikes for this week
                for team in w.strikes_given:
                    team_strikes[team] += 1
                # Track eliminations
                eliminated_teams.update(w.eliminations)
            
            # Build standings at this week
            week_standings = []
            for team_code in result.teams:
                strikes = team_strikes[team_code]
                is_eliminated = team_code in eliminated_teams
                
                if is_eliminated:
                    status = "eliminated"
                    status_emoji = "☠️"
                elif strikes > 0:
                    status = f"on_notice ({strikes} strike{'s' if strikes > 1 else ''})"
                    status_emoji = "⚠️"
                else:
                    status = "active"
                    status_emoji = "-"
                
                week_standings.append({
                    "team": team_code,
                    "strikes": strikes,
                    "status": status,
                    "status_emoji": status_emoji,
                    "eliminated": is_eliminated,
                })
            
            # Sort: active teams by strikes (fewer = better), then eliminated teams
            week_standings.sort(key=lambda x: (
                1 if x["eliminated"] else 0,  # Active teams first
                x["strikes"],  # Then by strike count
            ))
            
            console.print()
            console.print("| Place | Team | Strikes | Status |")
            console.print("|-------|------|---------|--------|")
            
            for place, standing in enumerate(week_standings, 1):
                console.print(
                    f"| {place} | {standing['team']} | {standing['strikes']} | "
                    f"{standing['status_emoji']} {standing['status']} |"
                )
            
            # Show winner if competition ended early
            active_count = sum(1 for s in week_standings if not s["eliminated"])
            if active_count == 1:
                winner = next(s["team"] for s in week_standings if not s["eliminated"])
                console.print()
                console.print(f"[bold green]Champion: {winner} 🏆[/bold green]")
        else:
            console.print(f"[bold]KORM Final Standings - {year}[/bold]")

            console.print()
            console.print("| Place | Team | Strikes | Status |")
            console.print("|-------|------|---------|--------|")

            sorted_results = sorted(
                result.team_results.values(),
                key=lambda r: r.final_place if r.final_place else 999
            )

            for r in sorted_results:
                status_emoji = "☠️" if r.status == "eliminated" else ("⚠️" if r.strikes else "-")
                payout_str = f" (${r.payout})" if r.payout else ""
                console.print(f"| {r.final_place} | {r.team_code} | {r.strike_count} | {status_emoji} {r.status}{payout_str} |")

            if result.winner:
                console.print()
                console.print(f"[bold green]Champion: {result.winner} 🏆[/bold green]")

    except FileNotFoundError as e:
        console.print(f"[red]❌ Data not found: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Failed: {e}[/red]")
        raise typer.Exit(1)


# Forensic commands
@forensic_app.command("investigate")
def cmd_forensic_investigate(
    case_id: str = typer.Argument(..., help="Case ID (e.g., RFFL-INQ-2025-001)"),
    season: int | None = typer.Option(
        None, "--season", "-s",
        help="Run for specific season only (for rate limit management)"
    ),
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Skip commissioner approval check"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="Show investigation plan without executing"
    ),
):
    """
    Execute a forensic investigation.
    
    Examples:
        rffl forensic investigate RFFL-INQ-2025-001
        rffl forensic investigate RFFL-INQ-2025-001 --season 2024
        rffl forensic investigate RFFL-INQ-2025-001 --dry-run
    """
    from .forensic.agent import ForensicAgent
    
    try:
        repo_root = find_repo_root()
        agent = ForensicAgent(repo_root / "investigations")
        config = agent.load_investigation(case_id)
        
        if not config.commissioner_approved and not force:
            console.print(f"[red]❌ Investigation {case_id} not yet approved by Commissioner.[/red]")
            console.print("   Use --force to bypass, or update investigation.yaml")
            raise typer.Exit(1)
        
        if dry_run:
            console.print(f"[bold]📋 Investigation Plan: {case_id}[/bold]")
            console.print(f"   Title: {config.title}")
            console.print(f"   Category: {config.category.value}")
            console.print(f"   Data Range: {config.data_range[0]}–{config.data_range[1]}")
            console.print(f"\n   Tasks:")
            for task in config.tasks:
                status = "✅" if task.completed else "⏳"
                console.print(f"     {status} {task.id}: {task.description}")
            return
        
        # Execute with optional season filter
        console.print(f"[cyan]🔍 Executing investigation: {case_id}[/cyan]")
        results = agent.execute_investigation(config, season_filter=season)
        report_path = agent.generate_report(config, results)
        
        console.print(f"[green]✅ Investigation complete: {report_path}[/green]")
        
    except FileNotFoundError as e:
        console.print(f"[red]❌ Investigation not found: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Investigation failed: {e}[/red]")
        raise typer.Exit(1)


@forensic_app.command("list")
def cmd_forensic_list():
    """List all investigations."""
    from pathlib import Path
    import yaml
    
    repo_root = find_repo_root()
    investigations_dir = repo_root / "investigations"
    
    if not investigations_dir.exists():
        console.print("[yellow]No investigations directory found.[/yellow]")
        return
    
    found = False
    for case_dir in sorted(investigations_dir.iterdir()):
        if case_dir.is_dir() and case_dir.name.startswith("RFFL-INQ-"):
            config_file = case_dir / "investigation.yaml"
            if config_file.exists():
                found = True
                try:
                    config = yaml.safe_load(config_file.read_text())
                    status = config.get("status", "unknown")
                    title = config.get("title", "Untitled")
                    approved = "✅" if config.get("commissioner_approved", False) else "⏳"
                    console.print(f"  {approved} {case_dir.name}: {title} [{status}]")
                except Exception as e:
                    console.print(f"  ⚠️  {case_dir.name}: Error reading config ({e})")
    
    if not found:
        console.print("[yellow]No investigations found.[/yellow]")


@forensic_app.command("approve")
def cmd_forensic_approve(
    case_id: str = typer.Argument(..., help="Case ID to approve"),
):
    """Mark an investigation as commissioner-approved."""
    import yaml
    from pathlib import Path
    
    repo_root = find_repo_root()
    config_path = repo_root / "investigations" / case_id / "investigation.yaml"
    
    if not config_path.exists():
        console.print(f"[red]❌ Investigation {case_id} not found.[/red]")
        raise typer.Exit(1)
    
    try:
        config = yaml.safe_load(config_path.read_text())
        config["commissioner_approved"] = True
        config["status"] = "investigation"
        
        config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
        console.print(f"[green]✅ Investigation {case_id} approved. Ready for execution.[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to approve investigation: {e}[/red]")
        raise typer.Exit(1)


# Utility commands
@utils_app.command("read-inbox")
def cmd_read_inbox(
    preview: bool = typer.Option(False, "--preview", help="Preview file contents (first 20 lines)"),
):
    """List files in the inbox folder."""
    from pathlib import Path
    
    try:
        repo_root = find_repo_root()
        files = list_inbox_files(repo_root)
        
        if not files:
            console.print("[green]✅ Inbox is empty - no files awaiting processing[/green]")
            return
        
        console.print(f"[cyan]Found {len(files)} file(s) in inbox:[/cyan]\n")
        
        for i, file_path in enumerate(files, 1):
            size = file_path.stat().st_size
            size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
            console.print(f"[cyan]{i}. {file_path.name}[/cyan] ({size_str})")
            
            if preview and file_path.is_file():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()[:20]
                        if lines:
                            console.print("[dim]   Preview:[/dim]")
                            for line in lines[:5]:  # Show first 5 lines
                                console.print(f"[dim]   {line.rstrip()}[/dim]")
                            if len(lines) > 5:
                                console.print(f"[dim]   ... ({len(lines)} lines total)[/dim]")
                except Exception:
                    console.print("[dim]   (binary or unreadable file)[/dim]")
        
        console.print(f"\n[yellow]Process these files, then run 'rffl utils clean-inbox' to remove them.[/yellow]")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to read inbox: {e}[/red]")
        raise typer.Exit(1)


@utils_app.command("clean-inbox")
def cmd_clean_inbox(
    delete: bool = typer.Option(False, "--delete", help="Delete files instead of prompting for destination"),
    destination: str = typer.Option(None, "--move-to", help="Move all files to this directory"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """
    Clean up the inbox folder by moving or deleting files.
    
    By default, prompts for each file's destination. Use --delete to remove files,
    or --move-to to move all files to a single directory.
    """
    from pathlib import Path
    import shutil
    
    try:
        repo_root = find_repo_root()
        files = list_inbox_files(repo_root)
        
        if not files:
            console.print("[green]✅ Inbox is already clean[/green]")
            return
        
        console.print(f"[yellow]Found {len(files)} file(s) in inbox[/yellow]\n")
        
        if destination:
            # Move all files to specified destination
            dest_path = Path(destination)
            dest_path.mkdir(parents=True, exist_ok=True)
            
            if not force:
                console.print(f"[yellow]Move all {len(files)} file(s) to '{destination}'?[/yellow]")
                if not typer.confirm("Continue?"):
                    console.print("[yellow]Cancelled[/yellow]")
                    return
            
            moved = 0
            for file_path in files:
                dest_file = dest_path / file_path.name
                if dest_file.exists() and not force:
                    console.print(f"[yellow]⚠️  {file_path.name} already exists at destination. Skipping.[/yellow]")
                    continue
                shutil.move(str(file_path), str(dest_file))
                console.print(f"[green]✓ Moved: {file_path.name} → {dest_file}[/green]")
                moved += 1
            
            console.print(f"\n[green]✅ Moved {moved} file(s) to {destination}[/green]")
            
        elif delete:
            # Delete all files
            if not force:
                console.print(f"[red]⚠️  Delete all {len(files)} file(s)?[/red]")
                for file_path in files:
                    console.print(f"  - {file_path.name}")
                if not typer.confirm("Continue?"):
                    console.print("[yellow]Cancelled[/yellow]")
                    return
            
            deleted = 0
            for file_path in files:
                file_path.unlink()
                console.print(f"[green]✓ Deleted: {file_path.name}[/green]")
                deleted += 1
            
            console.print(f"\n[green]✅ Deleted {deleted} file(s)[/green]")
            
        else:
            # Interactive mode - prompt for each file
            console.print("[cyan]Interactive cleanup mode. For each file:[/cyan]")
            console.print("[cyan]  - Enter destination path to move file[/cyan]")
            console.print("[cyan]  - Enter 'd' or 'delete' to delete file[/cyan]")
            console.print("[cyan]  - Enter 's' or 'skip' to leave file[/cyan]\n")
            
            moved = 0
            deleted = 0
            skipped = 0
            
            for file_path in files:
                console.print(f"\n[cyan]File: {file_path.name}[/cyan]")
                action = typer.prompt("Action (path/d/skip)", default="skip")
                
                if action.lower() in ["d", "delete"]:
                    file_path.unlink()
                    console.print(f"[green]✓ Deleted: {file_path.name}[/green]")
                    deleted += 1
                elif action.lower() in ["s", "skip"]:
                    console.print(f"[yellow]⊘ Skipped: {file_path.name}[/yellow]")
                    skipped += 1
                else:
                    # Move to destination
                    dest_path = Path(action)
                    if not dest_path.is_absolute():
                        dest_path = repo_root / dest_path
                    
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if dest_path.is_dir():
                        dest_file = dest_path / file_path.name
                    else:
                        dest_file = dest_path
                    
                    if dest_file.exists() and not force:
                        console.print(f"[yellow]⚠️  Destination exists. Skipping.[/yellow]")
                        skipped += 1
                        continue
                    
                    shutil.move(str(file_path), str(dest_file))
                    console.print(f"[green]✓ Moved: {file_path.name} → {dest_file}[/green]")
                    moved += 1
            
            console.print(f"\n[green]✅ Cleanup complete:[/green]")
            console.print(f"  Moved: {moved}")
            console.print(f"  Deleted: {deleted}")
            console.print(f"  Skipped: {skipped}")
        
        # Verify final state
        remaining = list_inbox_files(repo_root)
        if remaining:
            console.print(f"\n[yellow]⚠️  {len(remaining)} file(s) still in inbox[/yellow]")
        else:
            console.print("\n[green]✅ Inbox is now clean[/green]")
            
    except Exception as e:
        console.print(f"[red]❌ Failed to clean inbox: {e}[/red]")
        raise typer.Exit(1)


@utils_app.command("inbox-status")
def cmd_inbox_status():
    """Check the status of the inbox folder (alias for read-inbox)."""
    cmd_read_inbox(preview=False)


# MOA - Master Orchestrator Agent
@app.command("moa")
def cmd_moa(
    request: str = typer.Argument(..., help="What do you want to do?"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be executed without running"),
):
    """
    Master Orchestrator Agent - intelligent command dispatcher.

    Natural language interface to all RFFL tools. MOA understands your intent
    and routes requests to the appropriate commands.

    Examples:
        rffl moa "export 2024 boxscores"
        rffl moa "list capabilities"
        rffl moa "what did I just do"
        rffl moa "run the weekly recipe"
        rffl moa "show KORM standings for 2024"
    """
    try:
        repo_root = find_repo_root()
        dispatcher = MOADispatcher(repo_root=repo_root, dry_run=dry_run)
        result = dispatcher.dispatch(request)

        if result.success:
            if result.output:
                console.print(result.output)
            if dry_run:
                console.print(f"\n[dim]Command: {result.command}[/dim]")
        else:
            if result.error:
                console.print(f"[red]{result.error}[/red]")
            if result.command:
                console.print(f"[dim]Attempted: {result.command}[/dim]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]MOA error: {e}[/red]")
        raise typer.Exit(1)


# Main entry point
if __name__ == "__main__":
    app()

