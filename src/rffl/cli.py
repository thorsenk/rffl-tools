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
from .core.lineup import validate_lineup_file
from .core.transactions import export_transactions
from .core.validation import validate_boxscores
from .recipes.loader import find_repo_root, resolve_output_path
from .recipes.migrate import migrate_recipe
from .recipes.models import load_recipe, validate_recipe_paths
from .recipes.runner import RecipeRunner
from .recipes.wizard import RecipeWizard

load_dotenv(find_dotenv(), override=False)

app = typer.Typer(add_completion=False, help="RFFL Fantasy Football data toolkit")
console = Console()

# Command groups
core_app = typer.Typer(help="Core data operations")
recipe_app = typer.Typer(help="Recipe orchestration")
live_app = typer.Typer(help="Live scoring features")

app.add_typer(core_app, name="core", help="Core commands")
app.add_typer(recipe_app, name="recipe", help="Recipe commands")
app.add_typer(live_app, name="live", help="Live commands")


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
        issue_types = {}
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


# Main entry point
if __name__ == "__main__":
    app()

