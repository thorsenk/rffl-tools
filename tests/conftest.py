"""Shared pytest fixtures and configuration."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rffl.core.api import ESPNClient, ESPNCredentials


@pytest.fixture
def mock_espn_client():
    """Mock ESPN client for unit tests."""
    client = MagicMock(spec=ESPNClient)
    client.get_league.return_value = MagicMock()
    client.get_boxscores.return_value = []
    client.get_draft.return_value = []
    return client


@pytest.fixture
def sample_boxscores_path(tmp_path):
    """Create sample boxscores CSV for validation tests."""
    csv_path = tmp_path / "boxscores.csv"
    # Write minimal sample data
    csv_content = """season_year,week,matchup,team_code,is_co_owned?,team_owner_1,team_owner_2,team_projected_total,team_actual_total,slot_type,slot,player_name,nfl_team,position,is_placeholder,issue_flag,rs_projected_pf,rs_actual_pf
2024,1,1,TEAM1,,Owner1,,100.0,95.0,starters,QB,Player 1,GB,QB,No,,20.0,18.0
2024,1,1,TEAM1,,Owner1,,100.0,95.0,starters,RB,Player 2,KC,RB,No,,15.0,12.0
"""
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def repo_root(tmp_path):
    """Create a temporary repository root with pyproject.toml."""
    root = tmp_path / "rffl-tools"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname = 'rffl-tools'\n")
    return root


@pytest.fixture
def sample_recipe_path(tmp_path):
    """Create a sample recipe YAML file."""
    recipe_path = tmp_path / "recipe.yaml"
    recipe_content = """name: test-recipe
version: 1
type: export
league: 323196
year: 2024
weeks:
  start: 1
  end: 18
out: data/seasons/2024/boxscores.csv
flags:
  fill_missing_slots: true
  require_clean: true
  tolerance: 0.0
post:
  validate: true
  lineup_validate: false
profile: active
public_only: true
locked: false
notes: Test recipe
"""
    recipe_path.write_text(recipe_content)
    return recipe_path


@pytest.fixture
def credentials():
    """Sample ESPN credentials."""
    return ESPNCredentials(espn_s2="test_s2", swid="test_swid")

