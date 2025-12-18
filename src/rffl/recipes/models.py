"""Pydantic models for recipe schema validation."""

import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class WeeksConfig(BaseModel):
    """Configuration for week ranges."""

    start: int = Field(ge=1, le=18, description="Starting week (1-18)")
    end: int = Field(ge=1, le=18, description="Ending week (1-18)")

    @model_validator(mode="after")
    def validate_week_range(self) -> "WeeksConfig":
        """Ensure start week is not after end week."""
        if self.start > self.end:
            raise ValueError("Start week must be <= end week")
        return self


class ExportFlags(BaseModel):
    """Flags specific to export recipes."""

    fill_missing_slots: bool = Field(
        default=False, description="Fill missing starter slots with 0-pt placeholders"
    )
    require_clean: bool = Field(
        default=True, description="Require clean data (no mismatches)"
    )
    tolerance: float = Field(
        default=0.0, ge=0.0, description="Tolerance for validation mismatches"
    )


class PostProcessing(BaseModel):
    """Post-processing configuration."""

    validate: bool = Field(default=True, description="Run data validation")  # type: ignore[assignment]
    lineup_validate: bool = Field(
        default=False, description="Run lineup validation (export only)"
    )


class BaseRecipe(BaseModel):
    """Base recipe model with common fields."""

    name: str = Field(description="Recipe name (unique identifier)")
    version: int = Field(ge=1, description="Recipe version number")
    type: Literal[
        "export",
        "h2h",
        "draft",
        "transactions",
        "roster-changes",
        "weekly-roster-changes",
    ] = Field(description="Recipe type")
    league: int = Field(ge=1, description="ESPN League ID")
    year: int = Field(ge=2011, le=2030, description="Season year")
    weeks: WeeksConfig | None = Field(
        default=None, description="Week range (optional for full season)"
    )
    out: str = Field(
        description="Output file path (relative to repo root, supports legacy ${DATA_ROOT})"
    )
    flags: dict[str, Any] = Field(
        default_factory=dict, description="Type-specific flags"
    )
    post: PostProcessing = Field(
        default_factory=PostProcessing, description="Post-processing configuration"
    )
    profile: Literal["active", "preview"] = Field(
        default="active", description="Recipe profile"
    )
    public_only: bool = Field(
        default=True, description="Enforce public league mode (no cookies)"
    )
    locked: bool = Field(
        default=False, description="Whether recipe is locked (baselines only)"
    )
    notes: str = Field(default="", description="Recipe description and notes")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate recipe name format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Recipe name must contain only alphanumeric characters, hyphens, and underscores"
            )
        return v

    @field_validator("out")
    @classmethod
    def validate_output_path(cls, v: str) -> str:
        """Validate output path and prevent directory traversal."""
        # Check for directory traversal attempts
        if ".." in v:
            raise ValueError("Output path cannot contain '..' for security reasons")
        return v

    @model_validator(mode="after")
    def validate_public_only(self) -> "BaseRecipe":
        """Validate public-only mode constraints."""
        if self.public_only and self.locked:
            # Baselines should always be public-only
            pass
        return self


class ExportRecipe(BaseRecipe):
    """Recipe for exporting enhanced boxscores."""

    type: Literal["export"] = "export"
    flags: ExportFlags = Field(default_factory=ExportFlags)  # type: ignore[assignment]

    @model_validator(mode="after")
    def validate_export_specific(self) -> "ExportRecipe":
        """Validate export-specific configuration."""
        if self.post.lineup_validate and self.type != "export":
            raise ValueError("Lineup validation is only available for export recipes")
        return self


class H2HRecipe(BaseRecipe):
    """Recipe for head-to-head matchup exports."""

    type: Literal["h2h"] = "h2h"


class DraftRecipe(BaseRecipe):
    """Recipe for draft result exports."""

    type: Literal["draft"] = "draft"


class TransactionsRecipe(BaseRecipe):
    """Recipe for transaction exports."""

    type: Literal["transactions"] = "transactions"


class RosterChangesRecipe(BaseRecipe):
    """Recipe for roster change exports."""

    type: Literal["roster-changes"] = "roster-changes"


class WeeklyRosterChangesRecipe(BaseRecipe):
    """Recipe for weekly roster change exports."""

    type: Literal["weekly-roster-changes"] = "weekly-roster-changes"


# Union type for all recipe types
Recipe = (
    ExportRecipe
    | H2HRecipe
    | DraftRecipe
    | TransactionsRecipe
    | RosterChangesRecipe
    | WeeklyRosterChangesRecipe
)


def load_recipe(file_path: Path) -> Recipe:
    """
    Load and validate a recipe from a YAML file.

    Args:
        file_path: Path to recipe YAML file

    Returns:
        Recipe object with resolved paths
    """
    import yaml

    with open(file_path) as f:
        data = yaml.safe_load(f)

    # Determine recipe type and create appropriate model
    recipe_type = data.get("type")

    recipe: Recipe
    if recipe_type == "export":
        recipe = ExportRecipe(**data)
    elif recipe_type == "h2h":
        recipe = H2HRecipe(**data)
    elif recipe_type == "draft":
        recipe = DraftRecipe(**data)
    elif recipe_type == "transactions":
        recipe = TransactionsRecipe(**data)
    elif recipe_type == "roster-changes":
        recipe = RosterChangesRecipe(**data)
    elif recipe_type == "weekly-roster-changes":
        recipe = WeeklyRosterChangesRecipe(**data)
    else:
        raise ValueError(f"Unknown recipe type: {recipe_type}")

    return recipe


def validate_recipe_paths(recipe: Recipe, recipe_path: Path | None = None) -> list[str]:
    """
    Validate that recipe paths exist and are accessible.

    Args:
        recipe: Recipe object to validate
        recipe_path: Optional path to recipe file (for context)

    Returns:
        List of error messages (empty if valid)
    """
    from .loader import resolve_output_path

    errors = []

    try:
        # Resolve output path
        output_path = resolve_output_path(recipe.out, recipe_path)
        output_dir = output_path.parent

        if not output_dir.exists():
            errors.append(f"Output directory does not exist: {output_dir}")
        elif not output_dir.is_dir():
            errors.append(f"Output path is not a directory: {output_dir}")
    except Exception as e:
        errors.append(f"Failed to resolve output path: {e}")

    return errors

