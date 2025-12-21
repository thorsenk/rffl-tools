"""Recipe execution engine with logging and validation."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.api import ESPNCredentials
from ..core.draft import export_draft
from ..core.exceptions import RecipeError, RecipeLockedError
from ..core.export import export_boxscores
from ..core.h2h import export_h2h
from ..core.lineup import validate_lineup_file
from ..core.transactions import export_transactions
from ..core.validation import validate_boxscores
from .loader import resolve_output_path
from .models import Recipe

console = Console()


class RecipeRunner:
    """Executes recipes with comprehensive logging and validation."""

    def __init__(self, repo_root: Path | None = None):
        """
        Initialize runner.

        Args:
            repo_root: Optional repository root path (auto-detected if None)
        """
        if repo_root is None:
            # Find repo root
            current = Path.cwd()
            for parent in [current, *current.parents]:
                if (parent / "pyproject.toml").exists():
                    repo_root = parent
                    break
            if repo_root is None:
                raise RecipeError("Could not find repository root")

        self.repo_root = repo_root
        self.build_dir = repo_root / "build" / "recipes"
        self.build_dir.mkdir(parents=True, exist_ok=True)

    def run_recipe(self, recipe: Recipe, recipe_path: Path | None = None, dry_run: bool = False) -> bool:
        """
        Execute a recipe with full logging and validation.

        Args:
            recipe: Recipe object to execute
            recipe_path: Optional path to recipe file (for context)
            dry_run: If True, don't actually execute

        Returns:
            True if successful, False otherwise

        Raises:
            RecipeLockedError: If recipe is locked and shouldn't be executed
        """
        if recipe.locked:
            raise RecipeLockedError(
                f"Recipe '{recipe.name}' is locked. "
                "Baseline recipes cannot be executed directly."
            )

        # Create run directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self.build_dir / recipe.name / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)

        # Log recipe details
        self._log_recipe_info(recipe, run_dir)

        # Resolve output path
        output_path = resolve_output_path(recipe.out, recipe_path)

        # Log what would be executed
        self._log_execution_plan(recipe, output_path, run_dir)

        if dry_run:
            console.print(
                f"[yellow]Dry run - would execute recipe: {recipe.name}[/yellow]"
            )
            console.print(f"[yellow]Output: {output_path}[/yellow]")
            return True

        # Execute recipe
        success = self._execute_recipe(recipe, output_path, run_dir)

        # Run validations if successful
        if success and recipe.post.validate:
            success = self._run_validations(recipe, output_path, run_dir)

        # Copy artifacts
        self._copy_artifacts(output_path, run_dir)

        return success

    def _log_recipe_info(self, recipe: Recipe, run_dir: Path) -> None:
        """Log recipe information to run directory."""
        recipe_info = {
            "name": recipe.name,
            "version": recipe.version,
            "type": recipe.type,
            "league": recipe.league,
            "year": recipe.year,
            "weeks": recipe.weeks.model_dump() if recipe.weeks else None,
            "output": recipe.out,
            "flags": (
                recipe.flags.model_dump()
                if hasattr(recipe.flags, "model_dump")
                else recipe.flags
            ),
            "post_processing": recipe.post.model_dump(),
            "profile": recipe.profile,
            "public_only": recipe.public_only,
            "locked": recipe.locked,
            "notes": recipe.notes,
            "timestamp": datetime.now().isoformat(),
        }

        with open(run_dir / "recipe_info.json", "w") as f:
            json.dump(recipe_info, f, indent=2)

    def _log_execution_plan(self, recipe: Recipe, output_path: Path, run_dir: Path) -> None:
        """Log the execution plan."""
        plan = {
            "recipe_type": recipe.type,
            "league": recipe.league,
            "year": recipe.year,
            "weeks": recipe.weeks.model_dump() if recipe.weeks else None,
            "output_path": str(output_path),
            "flags": (
                recipe.flags.model_dump()
                if hasattr(recipe.flags, "model_dump")
                else recipe.flags
            ),
        }

        with open(run_dir / "execution_plan.json", "w") as f:
            json.dump(plan, f, indent=2)

    def _execute_recipe(
        self, recipe: Recipe, output_path: Path, run_dir: Path
    ) -> bool:
        """Execute the recipe using direct imports."""
        console.print(f"[blue]Executing recipe: {recipe.name}[/blue]")

        with open(run_dir / "run.log", "w") as log_file:
            log_file.write(f"Recipe: {recipe.name}\n")
            log_file.write(f"Type: {recipe.type}\n")
            log_file.write(f"Timestamp: {datetime.now().isoformat()}\n")
            log_file.write("=" * 80 + "\n")

            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Running recipe...", total=None)

                    # Create credentials if needed
                    credentials = None
                    if not recipe.public_only:
                        import os
                        credentials = ESPNCredentials(
                            espn_s2=os.getenv("ESPN_S2"),
                            swid=os.getenv("SWID"),
                        )

                    # Execute based on recipe type
                    if recipe.type == "export":
                        start_week = recipe.weeks.start if recipe.weeks else None
                        end_week = recipe.weeks.end if recipe.weeks else None
                        flags: Any = recipe.flags if hasattr(recipe.flags, "fill_missing_slots") else {}
                        
                        export_boxscores(
                            league_id=recipe.league,
                            year=recipe.year,
                            output_path=output_path,
                            start_week=start_week,
                            end_week=end_week,
                            fill_missing_slots=getattr(flags, "fill_missing_slots", False),
                            require_clean=getattr(flags, "require_clean", False),
                            tolerance=getattr(flags, "tolerance", 0.0),
                            credentials=credentials,
                            public_only=recipe.public_only,
                            repo_root=self.repo_root,
                        )

                    elif recipe.type == "h2h":
                        start_week = recipe.weeks.start if recipe.weeks else None
                        end_week = recipe.weeks.end if recipe.weeks else None
                        export_h2h(
                            league_id=recipe.league,
                            year=recipe.year,
                            output_path=output_path,
                            start_week=start_week,
                            end_week=end_week,
                            credentials=credentials,
                            public_only=recipe.public_only,
                        )

                    elif recipe.type == "draft":
                        export_draft(
                            league_id=recipe.league,
                            year=recipe.year,
                            output_path=output_path,
                            credentials=credentials,
                            public_only=recipe.public_only,
                        )

                    elif recipe.type == "transactions":
                        export_transactions(
                            league_id=recipe.league,
                            year=recipe.year,
                            output_path=output_path,
                            credentials=credentials,
                            public_only=recipe.public_only,
                            repo_root=self.repo_root,
                        )

                    else:
                        raise RecipeError(f"Unsupported recipe type: {recipe.type}")

                    progress.update(task, description="Recipe completed")
                    log_file.write("Recipe executed successfully\n")
                    console.print("[green]Recipe executed successfully[/green]")
                    return True

            except Exception as e:
                error_msg = f"Exception during execution: {e}\n"
                log_file.write(error_msg)
                import traceback
                log_file.write(traceback.format_exc())
                console.print(f"[red]{error_msg}[/red]")
                return False

    def _run_validations(
        self, recipe: Recipe, output_path: Path, run_dir: Path
    ) -> bool:
        """Run post-processing validations."""
        if recipe.type != "export":
            return True

        console.print("[blue]Running validations...[/blue]")

        validations_success = True

        # Run data validation
        if recipe.post.validate:
            try:
                validate_flags: Any = recipe.flags if hasattr(recipe.flags, "tolerance") else {}
                tolerance = getattr(validate_flags, "tolerance", 0.0)
                result = validate_boxscores(output_path, tolerance=tolerance)

                validation_log = run_dir / "validation.log"
                with open(validation_log, "w") as f:
                    f.write(f"Validation result: {result}\n")
                    if result["issues"]:
                        f.write(f"Issues found: {len(result['issues'])}\n")
                        for issue in result["issues"]:
                            f.write(f"  - {issue}\n")

                if not result["is_valid"]:
                    console.print(
                        f"[red]Validation failed: {result['total_issues']} issues found[/red]"
                    )
                    validations_success = False
                else:
                    console.print("[green]Data validation passed[/green]")
            except Exception as e:
                console.print(f"[red]Validation error: {e}[/red]")
                validations_success = False

        # Run lineup validation
        if recipe.post.lineup_validate:
            try:
                result = validate_lineup_file(output_path)

                lineup_log = run_dir / "lineup_validation.log"
                with open(lineup_log, "w") as f:
                    f.write(f"Lineup validation result: {result}\n")
                    if result["issues"]:
                        f.write(f"Issues found: {len(result['issues'])}\n")
                        for issue in result["issues"]:
                            f.write(f"  - {issue}\n")

                if not result["is_valid"]:
                    console.print(
                        f"[red]Lineup validation failed: {result['total_issues']} issues found[/red]"
                    )
                    validations_success = False
                else:
                    console.print("[green]Lineup validation passed[/green]")
            except Exception as e:
                console.print(f"[red]Lineup validation error: {e}[/red]")
                validations_success = False

        return validations_success

    def _copy_artifacts(self, output_path: Path, run_dir: Path) -> None:
        """Copy output artifacts to run directory."""
        if output_path.exists():
            artifacts_dir = run_dir / "artifacts"
            artifacts_dir.mkdir(exist_ok=True)

            # Copy main output file
            shutil.copy2(output_path, artifacts_dir / output_path.name)

            # Copy validation reports if they exist
            output_dir = output_path.parent
            for report_file in output_dir.glob("*_validation_report.csv"):
                shutil.copy2(report_file, artifacts_dir / report_file.name)

            console.print(f"[green]Artifacts copied to {artifacts_dir}[/green]")
        else:
            console.print(f"[yellow]Output file not found: {output_path}[/yellow]")

