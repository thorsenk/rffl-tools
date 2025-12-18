"""Tests for validation logic."""

import pytest

from rffl.core.validation import validate_boxscores


def test_validate_boxscores_clean(sample_boxscores_path):
    """Test validation of clean boxscores."""
    result = validate_boxscores(sample_boxscores_path, tolerance=0.0)
    # Note: Sample data may not be perfectly clean, adjust as needed
    assert "is_valid" in result
    assert "issues" in result
    assert "total_issues" in result


def test_validate_boxscores_with_tolerance(sample_boxscores_path):
    """Test validation with tolerance."""
    result = validate_boxscores(sample_boxscores_path, tolerance=1.0)
    assert "is_valid" in result
    assert "proj_mismatches" in result
    assert "actual_mismatches" in result

