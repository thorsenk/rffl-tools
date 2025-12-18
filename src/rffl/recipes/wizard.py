"""Interactive wizard for creating and cloning recipes."""

import os
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt

from .models import load_recipe

console = Console()


class RecipeWizard:
    """Interactive wizard for creating and cloning recipes."""

    def __init__(self, repo_root: Path | None = None) -> None:
        """
        Initialize wizard.

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
                raise ValueError("Could not find repository root")

        self.repo_root = repo_root
        self.baselines_dir = repo_root / "recipes" / "baselines"
        self.local_dir = repo_root / "recipes" / "local"
        self.local_dir.mkdir(parents=True, exist_ok=True)

    def run(self, baseline_name: str | None = None, profile: str = "active") -> None:
        """Run the interactive wizard."""
        console.print("[bold blue]RFFL Recipes Wizard[/bold blue]")
        console.print("Create a new recipe by cloning a baseline template\n")

        # List available baselines
        baselines = self._get_available_baselines()
        if not baselines:
            console.print("[red]No baseline recipes found in recipes/baselines/[/red]")
            return

        # Select baseline
        if baseline_name:
            baseline_path = self.baselines_dir / f"{baseline_name}.yaml"
            if not baseline_path.exists():
                console.print(f"[red]Baseline not found: {baseline_name}[/red]")
                return
        else:
            selected_path = self._select_baseline(baselines)
            if selected_path is None:
                return
            baseline_path = selected_path

        # Load baseline recipe
        try:
            baseline_recipe = load_recipe(baseline_path)
        except Exception as e:
            console.print(f"[red]Error loading baseline: {e}[/red]")
            return

        # Clone and customize recipe
        new_recipe = self._clone_and_customize(baseline_recipe, profile)

        # Save new recipe
        self._save_recipe(new_recipe)

    def _get_available_baselines(self) -> list[Path]:
        """Get list of available baseline recipes."""
        if not self.baselines_dir.exists():
            return []

        return list(self.baselines_dir.glob("*.yaml"))

    def _select_baseline(self, baselines: list[Path]) -> Path | None:
        """Let user select a baseline recipe."""
        console.print("Available baseline recipes:")
        for i, baseline in enumerate(baselines, 1):
            console.print(f"  {i}. {baseline.stem}")

        while True:
            try:
                choice = Prompt.ask("Select baseline (number)", default="1")
                index = int(choice) - 1
                if 0 <= index < len(baselines):
                    return baselines[index]
                else:
                    console.print("[red]Invalid selection[/red]")
            except ValueError:
                console.print("[red]Please enter a valid number[/red]")
            except KeyboardInterrupt:
                console.print("\n[yellow]Cancelled[/yellow]")
                return None

    def _clone_and_customize(
        self, baseline_recipe: Any, profile: str
    ) -> dict[str, Any]:
        """Clone baseline recipe and customize it."""
        console.print(f"\n[blue]Cloning baseline: {baseline_recipe.name}[/blue]")

        # Start with baseline data
        recipe_data = baseline_recipe.model_dump()

        # Reset to editable state
        recipe_data["locked"] = False
        recipe_data["version"] = 1

        # Customize based on profile
        if profile == "preview":
            recipe_data["profile"] = "preview"
            console.print("[yellow]Preview mode: suggesting current/next week[/yellow]")

        # Get customizations
        recipe_data = self._customize_recipe(recipe_data, profile)

        return recipe_data

    def _customize_recipe(
        self, recipe_data: dict[str, Any], profile: str
    ) -> dict[str, Any]:
        """Customize recipe through interactive prompts."""
        console.print("\n[bold]Recipe Customization[/bold]")

        # Recipe name
        default_name = f"{recipe_data['name']}_v1"
        recipe_data["name"] = Prompt.ask(
            "Recipe name",
            default=default_name,
        )

        # League ID
        current_league = os.getenv("LEAGUE", "323196")
        recipe_data["league"] = int(
            Prompt.ask(
                "ESPN League ID",
                default=current_league,
            )
        )

        # Year
        current_year = 2024  # Could be dynamic
        recipe_data["year"] = int(
            Prompt.ask(
                "Season year",
                default=str(current_year),
            )
        )

        # Weeks (if applicable)
        if recipe_data["type"] in ["export", "h2h"]:
            if Confirm.ask("Specify week range?", default=False):
                start_week = int(
                    Prompt.ask(
                        "Start week",
                        default="1",
                    )
                )
                end_week = int(
                    Prompt.ask(
                        "End week",
                        default="18",
                    )
                )

                if start_week > end_week:
                    console.print("[red]Start week must be <= end week[/red]")
                    start_week, end_week = end_week, start_week
                    console.print(
                        f"[yellow]Swapped to: {start_week}-{end_week}[/yellow]"
                    )

                recipe_data["weeks"] = {"start": start_week, "end": end_week}
            else:
                recipe_data["weeks"] = None

        # Output path (relative to repo root, no DATA_ROOT)
        default_output = f"data/seasons/{recipe_data['year']}"

        if recipe_data["type"] == "export":
            default_output += "/boxscores.csv"
        elif recipe_data["type"] == "h2h":
            default_output += "/h2h.csv"
        elif recipe_data["type"] == "draft":
            default_output += "/draft.csv"

        recipe_data["out"] = Prompt.ask("Output path", default=default_output)

        # Export-specific flags
        if recipe_data["type"] == "export":
            recipe_data["flags"]["fill_missing_slots"] = Confirm.ask(
                "Fill missing starter slots?",
                default=recipe_data["flags"].get("fill_missing_slots", True),
            )
            recipe_data["flags"]["require_clean"] = Confirm.ask(
                "Require clean data?",
                default=recipe_data["flags"].get("require_clean", True),
            )

        # Post-processing
        recipe_data["post"]["validate"] = Confirm.ask(
            "Run data validation?", default=recipe_data["post"].get("validate", True)
        )

        if recipe_data["type"] == "export":
            recipe_data["post"]["lineup_validate"] = Confirm.ask(
                "Run lineup validation?",
                default=recipe_data["post"].get("lineup_validate", True),
            )

        # Notes
        current_notes = recipe_data.get("notes", "")
        recipe_data["notes"] = Prompt.ask(
            "Recipe notes (optional)", default=current_notes
        )

        return recipe_data

    def _save_recipe(self, recipe_data: dict[str, Any]) -> None:
        """Save the new recipe to local directory."""
        recipe_name = recipe_data["name"]
        output_path = self.local_dir / f"{recipe_name}.yaml"

        # Check if file already exists
        if output_path.exists():
            if not Confirm.ask(f"Recipe {recipe_name} already exists. Overwrite?"):
                console.print("[yellow]Recipe not saved[/yellow]")
                return

        # Save recipe
        with open(output_path, "w") as f:
            yaml.dump(recipe_data, f, default_flow_style=False, sort_keys=False)

        console.print(f"[green]Recipe saved: {output_path}[/green]")
        console.print(f"[blue]Run with: rffl recipe run {output_path}[/blue]")

    def list_baselines(self) -> None:
        """List available baseline recipes with descriptions."""
        baselines = self._get_available_baselines()

        if not baselines:
            console.print("[yellow]No baseline recipes found[/yellow]")
            return

        console.print("[bold]Available Baseline Recipes:[/bold]")

        for baseline in baselines:
            try:
                recipe = load_recipe(baseline)

                console.print(f"\n[bold green]{baseline.stem}[/bold green]")
                console.print(f"  Type: {recipe.type}")
                console.print(f"  League: {recipe.league}")
                console.print(f"  Year: {recipe.year}")
                if recipe.weeks:
                    console.print(f"  Weeks: {recipe.weeks.start}-{recipe.weeks.end}")
                console.print(f"  Notes: {recipe.notes}")

            except Exception as e:
                console.print(f"\n[red]{baseline.stem} (error loading: {e})[/red]")

