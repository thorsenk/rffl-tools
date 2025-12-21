"""Tests for the KORM processor module."""

import json
from pathlib import Path

import pytest

from rffl.core.korm_processor import (
    KORMStrike,
    KORMTeamResult,
    KORMWeekResult,
    KORMSeasonResult,
    process_korm_week,
    process_korm_season,
    generate_korm_markdown,
    generate_korm_json,
    load_weekly_scores_from_h2h,
    load_weekly_scores_from_teamweek,
    SEASON_CONFIG,
)


class TestKORMStrikeMode:
    """Test strike mode determination."""

    def test_2_strike_mode_with_5_teams(self):
        """5+ active teams should use 2-strike mode."""
        team_results = {
            f"TEAM{i}": KORMTeamResult(team_code=f"TEAM{i}")
            for i in range(5)
        }
        scores = {f"TEAM{i}": 100.0 - i * 10 for i in range(5)}

        result = process_korm_week(1, scores, team_results)

        assert result.strike_mode == "2-strike"
        assert len(result.strikes_given) == 2

    def test_1_strike_mode_with_4_teams(self):
        """4 or fewer active teams should use 1-strike mode."""
        team_results = {
            f"TEAM{i}": KORMTeamResult(team_code=f"TEAM{i}")
            for i in range(4)
        }
        scores = {f"TEAM{i}": 100.0 - i * 10 for i in range(4)}

        result = process_korm_week(1, scores, team_results)

        assert result.strike_mode == "1-strike"
        assert len(result.strikes_given) == 1

    def test_2_strike_mode_with_12_teams(self):
        """Standard 12-team league should use 2-strike mode."""
        team_results = {
            f"TEAM{i}": KORMTeamResult(team_code=f"TEAM{i}")
            for i in range(12)
        }
        scores = {f"TEAM{i}": 100.0 - i * 5 for i in range(12)}

        result = process_korm_week(1, scores, team_results)

        assert result.strike_mode == "2-strike"
        assert len(result.strikes_given) == 2


class TestKORMStrikeAssignment:
    """Test strike assignment logic."""

    def test_bottom_2_teams_get_strikes(self):
        """Bottom 2 teams should receive strikes in 2-strike mode."""
        team_results = {
            "A": KORMTeamResult(team_code="A"),
            "B": KORMTeamResult(team_code="B"),
            "C": KORMTeamResult(team_code="C"),
            "D": KORMTeamResult(team_code="D"),
            "E": KORMTeamResult(team_code="E"),
        }
        scores = {"A": 100, "B": 90, "C": 80, "D": 70, "E": 60}

        result = process_korm_week(1, scores, team_results)

        # D (70) and E (60) are bottom 2
        assert set(result.strikes_given) == {"D", "E"}
        assert team_results["D"].strike_count == 1
        assert team_results["E"].strike_count == 1

    def test_strike_increments_count(self):
        """Strike should increment team's strike count."""
        team_results = {
            "A": KORMTeamResult(team_code="A"),
            "B": KORMTeamResult(team_code="B"),
            "C": KORMTeamResult(team_code="C"),
            "D": KORMTeamResult(team_code="D"),
            "E": KORMTeamResult(team_code="E"),
        }
        scores = {"A": 100, "B": 90, "C": 80, "D": 70, "E": 60}

        # Week 1
        process_korm_week(1, scores, team_results)
        assert team_results["E"].strike_count == 1
        assert team_results["E"].status == "on_notice"

        # Week 2 - E is still lowest
        process_korm_week(2, scores, team_results)
        assert team_results["E"].strike_count == 2
        assert team_results["E"].status == "eliminated"


class TestKORMTieHandling:
    """Test tie handling at strike threshold."""

    def test_ties_at_lowest_all_get_strikes(self):
        """All teams tied at lowest score should get strikes."""
        team_results = {
            "A": KORMTeamResult(team_code="A"),
            "B": KORMTeamResult(team_code="B"),
            "C": KORMTeamResult(team_code="C"),
            "D": KORMTeamResult(team_code="D"),
            "E": KORMTeamResult(team_code="E"),
        }
        # D and E tie for lowest
        scores = {"A": 100, "B": 90, "C": 80, "D": 60, "E": 60}

        result = process_korm_week(1, scores, team_results)

        # Both D and E should get strikes (tied for lowest)
        assert "D" in result.strikes_given
        assert "E" in result.strikes_given

    def test_ties_at_2nd_lowest_all_get_strikes(self):
        """In 2-strike mode, ties at 2nd lowest also get strikes."""
        team_results = {
            f"TEAM{i}": KORMTeamResult(team_code=f"TEAM{i}")
            for i in range(6)
        }
        # 3 teams tie for 2nd lowest
        scores = {
            "TEAM0": 100,
            "TEAM1": 90,
            "TEAM2": 70,  # Tied for 2nd lowest
            "TEAM3": 70,  # Tied for 2nd lowest
            "TEAM4": 70,  # Tied for 2nd lowest
            "TEAM5": 50,  # Lowest
        }

        result = process_korm_week(1, scores, team_results)

        # All 4 should get strikes (TEAM5 + 3 tied at 70)
        assert "TEAM5" in result.strikes_given
        assert "TEAM2" in result.strikes_given
        assert "TEAM3" in result.strikes_given
        assert "TEAM4" in result.strikes_given
        assert len(result.strikes_given) == 4


class TestKORMElimination:
    """Test elimination logic."""

    def test_two_strikes_eliminates_team(self):
        """Team with 2 strikes should be eliminated."""
        team_results = {
            "A": KORMTeamResult(team_code="A", strikes=[KORMStrike(1, 60.0)]),
            "B": KORMTeamResult(team_code="B"),
            "C": KORMTeamResult(team_code="C"),
            "D": KORMTeamResult(team_code="D"),
            "E": KORMTeamResult(team_code="E"),
        }
        team_results["A"].status = "on_notice"

        scores = {"A": 50, "B": 100, "C": 90, "D": 80, "E": 70}

        result = process_korm_week(2, scores, team_results)

        assert "A" in result.eliminations
        assert team_results["A"].status == "eliminated"
        assert team_results["A"].elimination_week == 2

    def test_eliminated_teams_excluded_from_future_weeks(self):
        """Eliminated teams should not participate in future weeks."""
        team_results = {
            "A": KORMTeamResult(team_code="A", status="eliminated", elimination_week=2),
            "B": KORMTeamResult(team_code="B"),
            "C": KORMTeamResult(team_code="C"),
            "D": KORMTeamResult(team_code="D"),
            "E": KORMTeamResult(team_code="E"),
        }
        team_results["A"].strikes = [KORMStrike(1, 60.0), KORMStrike(2, 55.0)]

        scores = {"A": 40, "B": 100, "C": 90, "D": 80, "E": 70}

        result = process_korm_week(3, scores, team_results)

        # Only 4 active teams, so 1-strike mode
        assert result.active_count_start == 4
        assert "A" not in result.strikes_given  # A is already eliminated


class TestKORMSeasonProcessing:
    """Test full season processing."""

    def test_season_ends_when_one_team_remains(self):
        """Competition should end when only 1 team remains."""
        # Create scenario where teams are eliminated quickly
        weekly_scores = {}

        # 5 teams, 2 strikes per week = ends in ~2-3 weeks
        for week in range(1, 14):
            weekly_scores[week] = {
                "A": 100.0,
                "B": 90.0 - week,  # Gets worse each week
                "C": 80.0 - week,
                "D": 70.0 - week,
                "E": 60.0 - week,
            }

        result = process_korm_season(2024, weekly_scores)

        assert result.ended_early
        assert result.winner is not None

    def test_season_config_respected(self):
        """Season configuration (weeks, fees) should be respected."""
        result = process_korm_season.__wrapped__ if hasattr(process_korm_season, '__wrapped__') else process_korm_season

        # Test 2018 config
        assert SEASON_CONFIG[2018]["weeks"] == (1, 13)
        assert SEASON_CONFIG[2018]["entry_fee"] == 40
        assert SEASON_CONFIG[2018]["pool"] == 480

        # Test 2021+ config
        assert SEASON_CONFIG[2024]["weeks"] == (1, 14)
        assert SEASON_CONFIG[2024]["entry_fee"] == 100
        assert SEASON_CONFIG[2024]["pool"] == 1200


class TestKORMDataLoading:
    """Test data loading from different formats."""

    def test_load_from_h2h_format(self, tmp_path):
        """Test loading scores from h2h.csv format."""
        h2h_csv = """week,matchup,home_team,away_team,home_score,away_score,winner,margin
1,1,TEAM_A,TEAM_B,100.5,90.25,TEAM_A,10.25
1,2,TEAM_C,TEAM_D,85.0,95.5,TEAM_D,-10.5
2,1,TEAM_A,TEAM_C,110.0,88.0,TEAM_A,22.0
"""
        h2h_path = tmp_path / "h2h.csv"
        h2h_path.write_text(h2h_csv)

        scores = load_weekly_scores_from_h2h(h2h_path, max_week=13)

        assert 1 in scores
        assert 2 in scores
        assert scores[1]["TEAM_A"] == 100.5
        assert scores[1]["TEAM_B"] == 90.25
        assert scores[1]["TEAM_C"] == 85.0
        assert scores[1]["TEAM_D"] == 95.5

    def test_load_from_teamweek_format(self, tmp_path):
        """Test loading scores from teamweek_unified.csv format."""
        teamweek_csv = """season_year,week,matchup,team_code,is_co_owned?,team_owner_1,team_owner_2,opponent_code,opp_is_co_owned?,opp_owner_1,opp_owner_2,team_projected_total,team_actual_total,opp_actual_total,result,margin
2024,1,1,TEAM_A,,Owner1,,TEAM_B,,Owner2,,95.0,100.5,90.25,W,10.25
2024,1,1,TEAM_B,,Owner2,,TEAM_A,,Owner1,,92.0,90.25,100.5,L,-10.25
2024,2,1,TEAM_A,,Owner1,,TEAM_C,,Owner3,,100.0,110.0,88.0,W,22.0
"""
        teamweek_path = tmp_path / "teamweek_unified.csv"
        teamweek_path.write_text(teamweek_csv)

        scores = load_weekly_scores_from_teamweek(teamweek_path, max_week=14)

        assert 1 in scores
        assert 2 in scores
        assert scores[1]["TEAM_A"] == 100.5
        assert scores[1]["TEAM_B"] == 90.25

    def test_respects_max_week(self, tmp_path):
        """Test that max_week is respected."""
        h2h_csv = """week,matchup,home_team,away_team,home_score,away_score,winner,margin
1,1,A,B,100,90,A,10
14,1,A,B,100,90,A,10
15,1,A,B,100,90,A,10
"""
        h2h_path = tmp_path / "h2h.csv"
        h2h_path.write_text(h2h_csv)

        scores = load_weekly_scores_from_h2h(h2h_path, max_week=13)

        assert 1 in scores
        assert 14 not in scores  # Beyond max_week
        assert 15 not in scores


class TestKORMOutputGeneration:
    """Test output generation (markdown and JSON)."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample KORM result for testing."""
        team_results = {
            "WINNER": KORMTeamResult(
                team_code="WINNER",
                strikes=[],
                status="active",
                final_place=1,
                payout=800,
            ),
            "SECOND": KORMTeamResult(
                team_code="SECOND",
                strikes=[KORMStrike(5, 70.0), KORMStrike(8, 65.0)],
                status="eliminated",
                elimination_week=8,
                final_place=2,
                payout=300,
            ),
            "THIRD": KORMTeamResult(
                team_code="THIRD",
                strikes=[KORMStrike(1, 60.0)],
                status="on_notice",
                final_place=3,
                payout=100,
            ),
            "FOURTH": KORMTeamResult(
                team_code="FOURTH",
                strikes=[KORMStrike(1, 55.0)],
                status="on_notice",
                final_place=4,
                payout=0,
            ),
        }

        weeks = [
            KORMWeekResult(
                week=1,
                active_count_start=4,
                strike_mode="1-strike",
                scores=[
                    {"team": "WINNER", "score": 100.0},
                    {"team": "SECOND", "score": 95.0},
                    {"team": "THIRD", "score": 60.0},
                    {"team": "FOURTH", "score": 55.0},
                ],
                strikes_given=["THIRD", "FOURTH"],
                eliminations=[],
                active_count_end=4,
            ),
        ]

        return KORMSeasonResult(
            season=2024,
            korm_window=(1, 14),
            entry_fee=100,
            pool=1200,
            teams=["WINNER", "SECOND", "THIRD", "FOURTH"],
            weeks=weeks,
            team_results=team_results,
            winner="WINNER",
            ended_early=True,
        )

    def test_markdown_contains_season_info(self, sample_result):
        """Markdown should contain season info."""
        md = generate_korm_markdown(sample_result)

        assert "# KORM History - 2024 Season" in md
        assert "$100/team" in md
        assert "$1,200" in md
        assert "Weeks 1-14" in md

    def test_markdown_contains_week_results(self, sample_result):
        """Markdown should contain week-by-week results."""
        md = generate_korm_markdown(sample_result)

        assert "### Week 1" in md
        assert "1-strike" in md  # 4 teams = 1-strike mode
        assert "WINNER" in md

    def test_markdown_contains_final_standings(self, sample_result):
        """Markdown should contain final standings."""
        md = generate_korm_markdown(sample_result)

        assert "## Final Standings" in md
        assert "Champion: WINNER" in md

    def test_json_structure(self, sample_result):
        """JSON output should have correct structure."""
        json_data = generate_korm_json(sample_result)

        assert json_data["season"] == 2024
        assert json_data["korm_window"] == {"start": 1, "end": 14}
        assert json_data["entry_fee"] == 100
        assert json_data["pool"] == 1200
        assert json_data["winner"] == "WINNER"
        assert "weeks" in json_data
        assert "final_standings" in json_data

    def test_json_is_serializable(self, sample_result):
        """JSON output should be serializable."""
        json_data = generate_korm_json(sample_result)

        # Should not raise
        serialized = json.dumps(json_data)
        assert isinstance(serialized, str)

        # Should be able to parse back
        parsed = json.loads(serialized)
        assert parsed["season"] == 2024


class TestKORMTeamResult:
    """Test KORMTeamResult dataclass."""

    def test_strike_count_property(self):
        """Strike count should match number of strikes."""
        result = KORMTeamResult(team_code="TEST")
        assert result.strike_count == 0

        result.strikes.append(KORMStrike(1, 60.0))
        assert result.strike_count == 1

        result.strikes.append(KORMStrike(3, 55.0))
        assert result.strike_count == 2

    def test_strike_weeks_property(self):
        """Strike weeks should list weeks with strikes."""
        result = KORMTeamResult(team_code="TEST")
        result.strikes = [KORMStrike(1, 60.0), KORMStrike(5, 55.0)]

        assert result.strike_weeks == [1, 5]
