"""Recipe loading and path resolution."""

import warnings
from pathlib import Path

from ..core.exceptions import PathResolutionError


def find_repo_root(start_path: Path | None = None) -> Path:
    """
    Find repository root by looking for pyproject.toml.

    Searches upward from start_path (or cwd) until finding pyproject.toml.

    Args:
        start_path: Starting path for search (defaults to current working directory)

    Returns:
        Path to repository root

    Raises:
        PathResolutionError: If repository root cannot be found
    """
    current = start_path or Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    raise PathResolutionError("Could not find repository root (pyproject.toml)")


def resolve_output_path(path_str: str, recipe_path: Path | None = None) -> Path:
    """
    Resolve output path from recipe.

    Rules:
    1. Absolute paths (/...) → used as-is
    2. Relative paths (data/...) → relative to repo root
    3. Legacy ${DATA_ROOT} paths → emit warning, resolve relative to repo root

    Args:
        path_str: Path string from recipe (may contain ${DATA_ROOT})
        recipe_path: Optional path to recipe file (for context)

    Returns:
        Resolved Path object
    """
    # Handle legacy DATA_ROOT paths
    if "${DATA_ROOT}" in path_str:
        warnings.warn(
            "Recipe uses deprecated ${DATA_ROOT}. "
            "Run 'rffl recipe migrate' to update.",
            DeprecationWarning,
            stacklevel=2,
        )
        path_str = path_str.replace("${DATA_ROOT}/", "").replace("${DATA_ROOT}", "")

    path = Path(path_str)

    # Absolute paths used as-is
    if path.is_absolute():
        return path

    # Relative paths: resolve from repo root
    repo_root = find_repo_root(recipe_path.parent if recipe_path else None)
    return repo_root / path

