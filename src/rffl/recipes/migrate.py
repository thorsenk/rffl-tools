"""Migrate recipes from DATA_ROOT to relative paths."""

import re
from pathlib import Path


def migrate_recipe(recipe_path: Path, dry_run: bool = False) -> list[str]:
    """
    Migrate a recipe from ${DATA_ROOT} to relative paths.

    Args:
        recipe_path: Path to recipe YAML file
        dry_run: If True, don't write changes

    Returns:
        List of changes made (or would be made)
    """
    with open(recipe_path) as f:
        content = f.read()

    changes = []

    # Find all ${DATA_ROOT} references
    pattern = r'\$\{DATA_ROOT\}/?'
    matches = list(re.finditer(pattern, content))

    if not matches:
        return ["No migration needed"]

    # Replace ${DATA_ROOT}/ with empty string (relative to repo root)
    new_content = re.sub(pattern, "", content)
    changes.append(f"Replaced {len(matches)} ${{DATA_ROOT}} references")

    if not dry_run:
        with open(recipe_path, "w") as f:
            f.write(new_content)
        changes.append(f"Updated {recipe_path}")
    else:
        changes.append("(dry run - no changes written)")

    return changes

