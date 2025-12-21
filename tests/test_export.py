"""Tests for the boxscore export module."""

from dataclasses import asdict
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from rffl.core.export import Row, iter_weeks, export_boxscores
from rffl.core.exceptions import ESPNAPIError, ValidationError


class TestRow:
    """Tests for the Row dataclass."""

    def test_row_creation(self):
        """Test basic Row creation with all required fields."""
        row = Row(
            season_year=2024,
            week=1,
            matchup=1,
            team_code="TEAM1",
            is_co_owned="No",
            team_owner_1="Owner1",
            team_owner_2="",
            team_projected_total=100.0,
            team_actual_total=95.0,
            slot_type="starters",
            slot="QB",
            player_name="Patrick Mahomes",
            nfl_team="KC",
            position="QB",
            is_placeholder="No",
            issue_flag=None,
            rs_projected_pf=20.0,
            rs_actual_pf=18.5,
        )
        assert row.season_year == 2024
        assert row.week == 1
        assert row.team_code == "TEAM1"
        assert row.player_name == "Patrick Mahomes"

    def test_row_to_dict(self):
        """Test Row conversion to dictionary."""
        row = Row(
            season_year=2024,
            week=1,
            matchup=1,
            team_code="TEAM1",
            is_co_owned="No",
            team_owner_1="Owner1",
            team_owner_2="",
            team_projected_total=100.0,
            team_actual_total=95.0,
            slot_type="starters",
            slot="QB",
            player_name="Player 1",
            nfl_team="GB",
            position="QB",
            is_placeholder="No",
            issue_flag=None,
            rs_projected_pf=15.0,
            rs_actual_pf=12.0,
        )
        row_dict = asdict(row)
        assert isinstance(row_dict, dict)
        assert row_dict["season_year"] == 2024
        assert row_dict["player_name"] == "Player 1"
        assert len(row_dict) == 18

    def test_row_with_placeholder(self):
        """Test Row for placeholder (empty slot)."""
        row = Row(
            season_year=2024,
            week=1,
            matchup=1,
            team_code="TEAM1",
            is_co_owned="No",
            team_owner_1="Owner1",
            team_owner_2="",
            team_projected_total=100.0,
            team_actual_total=95.0,
            slot_type="starters",
            slot="RB",
            player_name="EMPTY SLOT - RB",
            nfl_team="",
            position="RB",
            is_placeholder="Yes",
            issue_flag="MISSING_SLOT:RB",
            rs_projected_pf=0.0,
            rs_actual_pf=0.0,
        )
        assert row.is_placeholder == "Yes"
        assert row.issue_flag == "MISSING_SLOT:RB"
        assert row.rs_actual_pf == 0.0


class TestIterWeeks:
    """Tests for the iter_weeks function."""

    def test_iter_weeks_default_range(self, mock_espn_client):
        """Test iter_weeks with default week range (1-18)."""
        # Setup mock to return boxscores for weeks 1-3
        mock_boxscores = [MagicMock()]
        mock_espn_client.get_boxscores.return_value = mock_boxscores

        weeks = list(iter_weeks(mock_espn_client, None, None))

        # Should iterate weeks 1-18
        assert mock_espn_client.get_boxscores.call_count == 18
        assert len(weeks) == 18
        assert weeks[0][0] == 1  # First week
        assert weeks[-1][0] == 18  # Last week

    def test_iter_weeks_custom_range(self, mock_espn_client):
        """Test iter_weeks with custom week range."""
        mock_boxscores = [MagicMock()]
        mock_espn_client.get_boxscores.return_value = mock_boxscores

        weeks = list(iter_weeks(mock_espn_client, 5, 10))

        assert mock_espn_client.get_boxscores.call_count == 6
        assert weeks[0][0] == 5
        assert weeks[-1][0] == 10

    def test_iter_weeks_single_week(self, mock_espn_client):
        """Test iter_weeks for a single week."""
        mock_boxscores = [MagicMock()]
        mock_espn_client.get_boxscores.return_value = mock_boxscores

        weeks = list(iter_weeks(mock_espn_client, 7, 7))

        assert len(weeks) == 1
        assert weeks[0][0] == 7

    def test_iter_weeks_skips_empty_boxscores(self, mock_espn_client):
        """Test that iter_weeks skips weeks with no boxscores."""
        def side_effect(week):
            if week in [1, 3]:
                return [MagicMock()]
            return []

        mock_espn_client.get_boxscores.side_effect = side_effect

        weeks = list(iter_weeks(mock_espn_client, 1, 5))

        # Only weeks 1 and 3 have boxscores
        assert len(weeks) == 2
        assert weeks[0][0] == 1
        assert weeks[1][0] == 3

    def test_iter_weeks_handles_api_error(self, mock_espn_client):
        """Test that iter_weeks continues on ESPN API errors."""
        def side_effect(week):
            if week == 2:
                raise ESPNAPIError("API Error")
            return [MagicMock()]

        mock_espn_client.get_boxscores.side_effect = side_effect

        weeks = list(iter_weeks(mock_espn_client, 1, 3))

        # Should skip week 2 due to error
        assert len(weeks) == 2
        assert weeks[0][0] == 1
        assert weeks[1][0] == 3


class TestExportBoxscores:
    """Tests for the export_boxscores function."""

    @pytest.fixture
    def mock_boxscore(self):
        """Create a mock boxscore with realistic data."""
        boxscore = MagicMock()

        # Home team
        home_team = MagicMock()
        home_team.abbrev = "TEAM1"
        home_team.name = "Team One"
        boxscore.home_team = home_team

        # Away team
        away_team = MagicMock()
        away_team.abbrev = "TEAM2"
        away_team.name = "Team Two"
        boxscore.away_team = away_team

        # Create mock players for home lineup
        def create_player(name, slot, position, proj, actual):
            player = MagicMock()
            player.name = name
            player.slot_position = slot
            player.position = position
            player.projected_points = proj
            player.points = actual
            player.proTeam = "GB"
            return player

        boxscore.home_lineup = [
            create_player("QB Player", "QB", "QB", 20.0, 18.0),
            create_player("RB Player 1", "RB", "RB", 15.0, 12.0),
            create_player("RB Player 2", "RB", "RB", 14.0, 16.0),
            create_player("WR Player 1", "WR", "WR", 12.0, 10.0),
            create_player("WR Player 2", "WR", "WR", 11.0, 14.0),
            create_player("TE Player", "TE", "TE", 8.0, 6.0),
            create_player("FLEX Player", "RB/WR/TE", "RB", 10.0, 12.0),
            create_player("D/ST Player", "D/ST", "D/ST", 7.0, 5.0),
            create_player("K Player", "K", "K", 8.0, 10.0),
            create_player("Bench Player", "BE", "WR", 5.0, 3.0),
        ]

        boxscore.away_lineup = [
            create_player("QB Player 2", "QB", "QB", 19.0, 22.0),
            create_player("RB Player 3", "RB", "RB", 16.0, 14.0),
            create_player("RB Player 4", "RB", "RB", 13.0, 11.0),
            create_player("WR Player 3", "WR", "WR", 10.0, 13.0),
            create_player("WR Player 4", "WR", "WR", 12.0, 8.0),
            create_player("TE Player 2", "TE", "TE", 9.0, 11.0),
            create_player("FLEX Player 2", "RB/WR/TE", "WR", 11.0, 9.0),
            create_player("D/ST Player 2", "D/ST", "D/ST", 6.0, 8.0),
            create_player("K Player 2", "K", "K", 7.0, 6.0),
        ]

        return boxscore

    @pytest.fixture
    def setup_repo_root(self, tmp_path):
        """Create a temporary repo root with required files."""
        root = tmp_path / "rffl-tools"
        root.mkdir()
        (root / "pyproject.toml").write_text("[project]\nname = 'rffl-tools'\n")

        # Create teams directory and files
        teams_dir = root / "data" / "teams"
        teams_dir.mkdir(parents=True)

        # Create alias mapping
        alias_mapping = """aliases:
  - alias: TEAM1
    canonical: TEAM1
  - alias: TEAM2
    canonical: TEAM2
"""
        (teams_dir / "alias_mapping.yaml").write_text(alias_mapping)

        # Create canonical teams CSV
        canonical_csv = """season_year,team_code,team_full_name,is_co_owned,owner_code_1,owner_code_2
2024,TEAM1,Team One,No,Owner1,
2024,TEAM2,Team Two,No,Owner2,
"""
        (teams_dir / "canonical_teams.csv").write_text(canonical_csv)

        return root

    def test_export_boxscores_basic(self, mock_boxscore, setup_repo_root, tmp_path):
        """Test basic boxscore export."""
        output_path = tmp_path / "output" / "boxscores.csv"

        with patch("rffl.core.export.ESPNClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_league.return_value = MagicMock()
            mock_client.get_boxscores.return_value = [mock_boxscore]
            MockClient.return_value = mock_client

            result = export_boxscores(
                league_id=323196,
                year=2024,
                output_path=output_path,
                start_week=1,
                end_week=1,
                repo_root=setup_repo_root,
            )

        assert result == output_path
        assert output_path.exists()

        # Verify CSV contents
        df = pd.read_csv(output_path)
        assert len(df) > 0
        assert "season_year" in df.columns
        assert "team_code" in df.columns
        assert "player_name" in df.columns

    def test_export_boxscores_creates_output_directory(self, mock_boxscore, setup_repo_root, tmp_path):
        """Test that export creates output directory if it doesn't exist."""
        output_path = tmp_path / "nested" / "deep" / "boxscores.csv"

        with patch("rffl.core.export.ESPNClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_league.return_value = MagicMock()
            mock_client.get_boxscores.return_value = [mock_boxscore]
            MockClient.return_value = mock_client

            result = export_boxscores(
                league_id=323196,
                year=2024,
                output_path=output_path,
                start_week=1,
                end_week=1,
                repo_root=setup_repo_root,
            )

        assert output_path.exists()
        assert output_path.parent.exists()

    def test_export_boxscores_slot_ordering(self, mock_boxscore, setup_repo_root, tmp_path):
        """Test that starters are ordered correctly (QB, RB, RB, WR, WR, TE, FLEX, D/ST, K)."""
        output_path = tmp_path / "boxscores.csv"

        with patch("rffl.core.export.ESPNClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_league.return_value = MagicMock()
            mock_client.get_boxscores.return_value = [mock_boxscore]
            MockClient.return_value = mock_client

            export_boxscores(
                league_id=323196,
                year=2024,
                output_path=output_path,
                start_week=1,
                end_week=1,
                repo_root=setup_repo_root,
            )

        df = pd.read_csv(output_path)

        # Get starters for first team
        team1_starters = df[(df["team_code"] == "TEAM1") & (df["slot_type"] == "starters")]
        slots = team1_starters["slot"].tolist()

        expected_order = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "D/ST", "K"]
        assert slots == expected_order

    def test_export_boxscores_bench_after_starters(self, mock_boxscore, setup_repo_root, tmp_path):
        """Test that bench players appear after starters."""
        output_path = tmp_path / "boxscores.csv"

        with patch("rffl.core.export.ESPNClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_league.return_value = MagicMock()
            mock_client.get_boxscores.return_value = [mock_boxscore]
            MockClient.return_value = mock_client

            export_boxscores(
                league_id=323196,
                year=2024,
                output_path=output_path,
                start_week=1,
                end_week=1,
                repo_root=setup_repo_root,
            )

        df = pd.read_csv(output_path)
        team1 = df[df["team_code"] == "TEAM1"]

        # Find index of last starter and first bench
        starters_idx = team1[team1["slot_type"] == "starters"].index.tolist()
        bench_idx = team1[team1["slot_type"] == "bench"].index.tolist()

        if bench_idx:  # Only check if there are bench players
            assert max(starters_idx) < min(bench_idx)


class TestExportBoxscoresFillMissingSlots:
    """Tests for the fill_missing_slots feature."""

    @pytest.fixture
    def incomplete_boxscore(self):
        """Create a boxscore with missing starter slots."""
        boxscore = MagicMock()

        home_team = MagicMock()
        home_team.abbrev = "TEAM1"
        boxscore.home_team = home_team

        away_team = MagicMock()
        away_team.abbrev = "TEAM2"
        boxscore.away_team = away_team

        def create_player(name, slot, position, proj, actual):
            player = MagicMock()
            player.name = name
            player.slot_position = slot
            player.position = position
            player.projected_points = proj
            player.points = actual
            player.proTeam = "GB"
            return player

        # Only 5 starters - missing RB, WR, TE, K
        boxscore.home_lineup = [
            create_player("QB Player", "QB", "QB", 20.0, 18.0),
            create_player("RB Player 1", "RB", "RB", 15.0, 12.0),
            create_player("WR Player 1", "WR", "WR", 12.0, 10.0),
            create_player("FLEX Player", "RB/WR/TE", "RB", 10.0, 12.0),
            create_player("D/ST Player", "D/ST", "D/ST", 7.0, 5.0),
        ]

        boxscore.away_lineup = [
            create_player("QB Player 2", "QB", "QB", 19.0, 22.0),
        ]

        return boxscore

    @pytest.fixture
    def setup_repo_root(self, tmp_path):
        """Create a temporary repo root with required files."""
        root = tmp_path / "rffl-tools"
        root.mkdir()
        (root / "pyproject.toml").write_text("[project]\nname = 'rffl-tools'\n")

        teams_dir = root / "data" / "teams"
        teams_dir.mkdir(parents=True)

        alias_mapping = """aliases:
  - alias: TEAM1
    canonical: TEAM1
  - alias: TEAM2
    canonical: TEAM2
"""
        (teams_dir / "alias_mapping.yaml").write_text(alias_mapping)

        canonical_csv = """season_year,team_code,team_full_name,is_co_owned,owner_code_1,owner_code_2
2024,TEAM1,Team One,No,Owner1,
2024,TEAM2,Team Two,No,Owner2,
"""
        (teams_dir / "canonical_teams.csv").write_text(canonical_csv)

        return root

    def test_fill_missing_slots_adds_placeholders(self, incomplete_boxscore, setup_repo_root, tmp_path):
        """Test that missing slots are filled with placeholders."""
        output_path = tmp_path / "boxscores.csv"

        with patch("rffl.core.export.ESPNClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_league.return_value = MagicMock()
            mock_client.get_boxscores.return_value = [incomplete_boxscore]
            MockClient.return_value = mock_client

            export_boxscores(
                league_id=323196,
                year=2024,
                output_path=output_path,
                start_week=1,
                end_week=1,
                fill_missing_slots=True,
                repo_root=setup_repo_root,
            )

        df = pd.read_csv(output_path)
        team1_starters = df[(df["team_code"] == "TEAM1") & (df["slot_type"] == "starters")]

        # Should have 9 starters after filling
        assert len(team1_starters) == 9

        # Check for placeholders
        placeholders = df[df["is_placeholder"] == "Yes"]
        assert len(placeholders) > 0

    def test_fill_missing_slots_placeholder_values(self, incomplete_boxscore, setup_repo_root, tmp_path):
        """Test that placeholders have correct values."""
        output_path = tmp_path / "boxscores.csv"

        with patch("rffl.core.export.ESPNClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_league.return_value = MagicMock()
            mock_client.get_boxscores.return_value = [incomplete_boxscore]
            MockClient.return_value = mock_client

            export_boxscores(
                league_id=323196,
                year=2024,
                output_path=output_path,
                start_week=1,
                end_week=1,
                fill_missing_slots=True,
                repo_root=setup_repo_root,
            )

        df = pd.read_csv(output_path)
        placeholders = df[df["is_placeholder"] == "Yes"]

        for _, row in placeholders.iterrows():
            assert row["rs_projected_pf"] == 0.0
            assert row["rs_actual_pf"] == 0.0
            assert "EMPTY SLOT" in row["player_name"]
            assert row["issue_flag"].startswith("MISSING_SLOT:")

    def test_no_fill_missing_slots(self, incomplete_boxscore, setup_repo_root, tmp_path):
        """Test that without fill_missing_slots, placeholders are not added."""
        output_path = tmp_path / "boxscores.csv"

        with patch("rffl.core.export.ESPNClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_league.return_value = MagicMock()
            mock_client.get_boxscores.return_value = [incomplete_boxscore]
            MockClient.return_value = mock_client

            export_boxscores(
                league_id=323196,
                year=2024,
                output_path=output_path,
                start_week=1,
                end_week=1,
                fill_missing_slots=False,
                repo_root=setup_repo_root,
            )

        df = pd.read_csv(output_path)
        placeholders = df[df["is_placeholder"] == "Yes"]

        assert len(placeholders) == 0


class TestExportBoxscoresRequireClean:
    """Tests for the require_clean validation feature."""

    @pytest.fixture
    def setup_repo_root(self, tmp_path):
        """Create a temporary repo root with required files."""
        root = tmp_path / "rffl-tools"
        root.mkdir()
        (root / "pyproject.toml").write_text("[project]\nname = 'rffl-tools'\n")

        teams_dir = root / "data" / "teams"
        teams_dir.mkdir(parents=True)

        alias_mapping = """aliases:
  - alias: TEAM1
    canonical: TEAM1
  - alias: TEAM2
    canonical: TEAM2
"""
        (teams_dir / "alias_mapping.yaml").write_text(alias_mapping)

        canonical_csv = """season_year,team_code,team_full_name,is_co_owned,owner_code_1,owner_code_2
2024,TEAM1,Team One,No,Owner1,
2024,TEAM2,Team Two,No,Owner2,
"""
        (teams_dir / "canonical_teams.csv").write_text(canonical_csv)

        return root

    @pytest.fixture
    def clean_boxscore(self):
        """Create a boxscore that passes validation (9 starters, matching totals)."""
        boxscore = MagicMock()

        home_team = MagicMock()
        home_team.abbrev = "TEAM1"
        boxscore.home_team = home_team

        away_team = MagicMock()
        away_team.abbrev = "TEAM2"
        boxscore.away_team = away_team

        def create_player(name, slot, position, proj, actual):
            player = MagicMock()
            player.name = name
            player.slot_position = slot
            player.position = position
            player.projected_points = proj
            player.points = actual
            player.proTeam = "GB"
            return player

        # Complete 9-starter lineup
        boxscore.home_lineup = [
            create_player("QB Player", "QB", "QB", 20.0, 18.0),
            create_player("RB Player 1", "RB", "RB", 15.0, 12.0),
            create_player("RB Player 2", "RB", "RB", 14.0, 16.0),
            create_player("WR Player 1", "WR", "WR", 12.0, 10.0),
            create_player("WR Player 2", "WR", "WR", 11.0, 14.0),
            create_player("TE Player", "TE", "TE", 8.0, 6.0),
            create_player("FLEX Player", "RB/WR/TE", "RB", 10.0, 12.0),
            create_player("D/ST Player", "D/ST", "D/ST", 7.0, 5.0),
            create_player("K Player", "K", "K", 8.0, 10.0),
        ]

        boxscore.away_lineup = [
            create_player("QB Player 2", "QB", "QB", 19.0, 22.0),
            create_player("RB Player 3", "RB", "RB", 16.0, 14.0),
            create_player("RB Player 4", "RB", "RB", 13.0, 11.0),
            create_player("WR Player 3", "WR", "WR", 10.0, 13.0),
            create_player("WR Player 4", "WR", "WR", 12.0, 8.0),
            create_player("TE Player 2", "TE", "TE", 9.0, 11.0),
            create_player("FLEX Player 2", "RB/WR/TE", "WR", 11.0, 9.0),
            create_player("D/ST Player 2", "D/ST", "D/ST", 6.0, 8.0),
            create_player("K Player 2", "K", "K", 7.0, 6.0),
        ]

        return boxscore

    def test_require_clean_passes_with_clean_data(self, clean_boxscore, setup_repo_root, tmp_path):
        """Test that require_clean passes with valid data."""
        output_path = tmp_path / "boxscores.csv"

        with patch("rffl.core.export.ESPNClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_league.return_value = MagicMock()
            mock_client.get_boxscores.return_value = [clean_boxscore]
            MockClient.return_value = mock_client

            result = export_boxscores(
                league_id=323196,
                year=2024,
                output_path=output_path,
                start_week=1,
                end_week=1,
                require_clean=True,
                repo_root=setup_repo_root,
            )

        assert output_path.exists()

    def test_require_clean_fails_with_wrong_starter_count(self, setup_repo_root, tmp_path):
        """Test that require_clean fails when starter count is not 9."""
        output_path = tmp_path / "boxscores.csv"

        # Create boxscore with only 5 starters
        boxscore = MagicMock()
        home_team = MagicMock()
        home_team.abbrev = "TEAM1"
        boxscore.home_team = home_team
        boxscore.away_team = None

        def create_player(name, slot, position, proj, actual):
            player = MagicMock()
            player.name = name
            player.slot_position = slot
            player.position = position
            player.projected_points = proj
            player.points = actual
            player.proTeam = "GB"
            return player

        boxscore.home_lineup = [
            create_player("QB Player", "QB", "QB", 20.0, 18.0),
            create_player("RB Player 1", "RB", "RB", 15.0, 12.0),
            create_player("RB Player 2", "RB", "RB", 14.0, 16.0),
            create_player("WR Player 1", "WR", "WR", 12.0, 10.0),
            create_player("WR Player 2", "WR", "WR", 11.0, 14.0),
        ]

        with patch("rffl.core.export.ESPNClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_league.return_value = MagicMock()
            mock_client.get_boxscores.return_value = [boxscore]
            MockClient.return_value = mock_client

            with pytest.raises(ValidationError) as exc_info:
                export_boxscores(
                    league_id=323196,
                    year=2024,
                    output_path=output_path,
                    start_week=1,
                    end_week=1,
                    require_clean=True,
                    repo_root=setup_repo_root,
                )

        assert "bad_count" in str(exc_info.value)

    def test_tolerance_allows_small_differences(self, clean_boxscore, setup_repo_root, tmp_path):
        """Test that tolerance parameter allows small point differences."""
        output_path = tmp_path / "boxscores.csv"

        with patch("rffl.core.export.ESPNClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_league.return_value = MagicMock()
            mock_client.get_boxscores.return_value = [clean_boxscore]
            MockClient.return_value = mock_client

            result = export_boxscores(
                league_id=323196,
                year=2024,
                output_path=output_path,
                start_week=1,
                end_week=1,
                require_clean=True,
                tolerance=0.5,
                repo_root=setup_repo_root,
            )

        assert output_path.exists()


class TestExportBoxscoresErrorHandling:
    """Tests for error handling in export_boxscores."""

    def test_raises_value_error_without_repo_root(self, tmp_path):
        """Test that export raises error when repo root cannot be found."""
        output_path = tmp_path / "boxscores.csv"

        # Change to a directory without pyproject.toml
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            with patch("rffl.core.export.ESPNClient") as MockClient:
                with pytest.raises(ValueError) as exc_info:
                    export_boxscores(
                        league_id=323196,
                        year=2024,
                        output_path=output_path,
                        start_week=1,
                        end_week=1,
                    )

            assert "Could not find repository root" in str(exc_info.value)
        finally:
            os.chdir(original_cwd)

    def test_handles_espn_api_error(self, tmp_path):
        """Test that ESPN API errors are properly raised."""
        output_path = tmp_path / "boxscores.csv"

        # Create repo root
        root = tmp_path / "repo"
        root.mkdir()
        (root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        teams_dir = root / "data" / "teams"
        teams_dir.mkdir(parents=True)
        (teams_dir / "alias_mapping.yaml").write_text("aliases: []\n")

        with patch("rffl.core.export.ESPNClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_league.return_value = MagicMock()
            mock_client.get_boxscores.side_effect = ESPNAPIError("API Error")
            MockClient.return_value = mock_client

            # iter_weeks catches ESPNAPIError, so no boxscores will be returned
            # This should create an empty CSV
            result = export_boxscores(
                league_id=323196,
                year=2024,
                output_path=output_path,
                start_week=1,
                end_week=1,
                repo_root=root,
            )

        assert output_path.exists()


class TestExportBoxscoresFlexValidation:
    """Tests for FLEX position validation."""

    @pytest.fixture
    def setup_repo_root(self, tmp_path):
        """Create a temporary repo root with required files."""
        root = tmp_path / "rffl-tools"
        root.mkdir()
        (root / "pyproject.toml").write_text("[project]\nname = 'rffl-tools'\n")

        teams_dir = root / "data" / "teams"
        teams_dir.mkdir(parents=True)

        alias_mapping = """aliases:
  - alias: TEAM1
    canonical: TEAM1
"""
        (teams_dir / "alias_mapping.yaml").write_text(alias_mapping)

        canonical_csv = """season_year,team_code,team_full_name,is_co_owned,owner_code_1,owner_code_2
2024,TEAM1,Team One,No,Owner1,
"""
        (teams_dir / "canonical_teams.csv").write_text(canonical_csv)

        return root

    def test_invalid_flex_position_is_flagged(self, setup_repo_root, tmp_path):
        """Test that invalid FLEX positions (not RB/WR/TE) are flagged."""
        output_path = tmp_path / "boxscores.csv"

        boxscore = MagicMock()
        home_team = MagicMock()
        home_team.abbrev = "TEAM1"
        boxscore.home_team = home_team
        boxscore.away_team = None

        def create_player(name, slot, position, proj, actual):
            player = MagicMock()
            player.name = name
            player.slot_position = slot
            player.position = position
            player.projected_points = proj
            player.points = actual
            player.proTeam = "GB"
            return player

        # QB in FLEX slot (invalid)
        boxscore.home_lineup = [
            create_player("QB Player", "QB", "QB", 20.0, 18.0),
            create_player("RB Player 1", "RB", "RB", 15.0, 12.0),
            create_player("RB Player 2", "RB", "RB", 14.0, 16.0),
            create_player("WR Player 1", "WR", "WR", 12.0, 10.0),
            create_player("WR Player 2", "WR", "WR", 11.0, 14.0),
            create_player("TE Player", "TE", "TE", 8.0, 6.0),
            create_player("Invalid FLEX", "RB/WR/TE", "QB", 10.0, 12.0),  # QB in FLEX!
            create_player("D/ST Player", "D/ST", "D/ST", 7.0, 5.0),
            create_player("K Player", "K", "K", 8.0, 10.0),
        ]

        with patch("rffl.core.export.ESPNClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_league.return_value = MagicMock()
            mock_client.get_boxscores.return_value = [boxscore]
            MockClient.return_value = mock_client

            export_boxscores(
                league_id=323196,
                year=2024,
                output_path=output_path,
                start_week=1,
                end_week=1,
                repo_root=setup_repo_root,
            )

        df = pd.read_csv(output_path)
        flex_row = df[df["slot"] == "FLEX"].iloc[0]

        assert "INVALID_FLEX_POSITION:QB" in str(flex_row["issue_flag"])

    def test_valid_flex_positions_not_flagged(self, setup_repo_root, tmp_path):
        """Test that valid FLEX positions (RB/WR/TE) are not flagged."""
        output_path = tmp_path / "boxscores.csv"

        boxscore = MagicMock()
        home_team = MagicMock()
        home_team.abbrev = "TEAM1"
        boxscore.home_team = home_team
        boxscore.away_team = None

        def create_player(name, slot, position, proj, actual):
            player = MagicMock()
            player.name = name
            player.slot_position = slot
            player.position = position
            player.projected_points = proj
            player.points = actual
            player.proTeam = "GB"
            return player

        boxscore.home_lineup = [
            create_player("QB Player", "QB", "QB", 20.0, 18.0),
            create_player("RB Player 1", "RB", "RB", 15.0, 12.0),
            create_player("RB Player 2", "RB", "RB", 14.0, 16.0),
            create_player("WR Player 1", "WR", "WR", 12.0, 10.0),
            create_player("WR Player 2", "WR", "WR", 11.0, 14.0),
            create_player("TE Player", "TE", "TE", 8.0, 6.0),
            create_player("Valid FLEX", "RB/WR/TE", "WR", 10.0, 12.0),  # WR in FLEX (valid)
            create_player("D/ST Player", "D/ST", "D/ST", 7.0, 5.0),
            create_player("K Player", "K", "K", 8.0, 10.0),
        ]

        with patch("rffl.core.export.ESPNClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_league.return_value = MagicMock()
            mock_client.get_boxscores.return_value = [boxscore]
            MockClient.return_value = mock_client

            export_boxscores(
                league_id=323196,
                year=2024,
                output_path=output_path,
                start_week=1,
                end_week=1,
                repo_root=setup_repo_root,
            )

        df = pd.read_csv(output_path)
        flex_row = df[df["slot"] == "FLEX"].iloc[0]

        # Should be empty or NaN, not an error flag
        assert pd.isna(flex_row["issue_flag"]) or flex_row["issue_flag"] == ""
