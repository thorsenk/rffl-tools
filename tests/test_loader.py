"""Tests for recipe loader and path resolution."""

from pathlib import Path

import pytest

from rffl.core.exceptions import PathResolutionError
from rffl.recipes.loader import find_repo_root, resolve_output_path


def test_find_repo_root(repo_root):
    """Test finding repository root."""
    # Create a subdirectory
    subdir = repo_root / "subdir" / "nested"
    subdir.mkdir(parents=True)

    # Should find repo root from subdirectory
    found_root = find_repo_root(subdir)
    assert found_root == repo_root


def test_find_repo_root_not_found(tmp_path):
    """Test that PathResolutionError is raised when repo root not found."""
    # Create directory without pyproject.toml
    test_dir = tmp_path / "no_repo"
    test_dir.mkdir()

    with pytest.raises(PathResolutionError):
        find_repo_root(test_dir)


def test_resolve_output_path_absolute(tmp_path):
    """Test resolving absolute paths."""
    abs_path = Path("/absolute/path/to/file.csv")
    resolved = resolve_output_path(str(abs_path))
    assert resolved == abs_path


def test_resolve_output_path_relative(repo_root):
    """Test resolving relative paths."""
    # Change to repo root
    import os
    old_cwd = os.getcwd()
    try:
        os.chdir(repo_root)
        resolved = resolve_output_path("data/seasons/2024/boxscores.csv")
        assert resolved == repo_root / "data" / "seasons" / "2024" / "boxscores.csv"
    finally:
        os.chdir(old_cwd)


def test_resolve_output_path_legacy_data_root(repo_root, monkeypatch):
    """Test resolving legacy ${DATA_ROOT} paths."""
    import warnings

    # Change to repo root
    import os
    old_cwd = os.getcwd()
    try:
        os.chdir(repo_root)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            resolved = resolve_output_path("${DATA_ROOT}/data/seasons/2024/boxscores.csv")
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert resolved == repo_root / "data" / "seasons" / "2024" / "boxscores.csv"
    finally:
        os.chdir(old_cwd)

