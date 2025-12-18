"""KORM (King of the Red Marks) competition tracking and reporting.

This module handles the KORM elimination competition logic, including:
- Strike tracking and elimination rules
- Live score analysis and projections
- Historical data loading
- Report generation with dramatic formatting
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json


@dataclass
class KORMTeam:
    """Represents a team in the KORM competition."""

    name: str
    abbreviation: str
    team_id: int
    strikes: int = 0
    strike_weeks: List[int] = None
    eliminated: bool = False
    eliminated_week: Optional[int] = None

    def __post_init__(self):
        if self.strike_weeks is None:
            self.strike_weeks = []

    @property
    def status(self) -> str:
        """Get team status (Active, On Notice, Eliminated)."""
        if self.eliminated:
            return f"ELIMINATED W{self.eliminated_week}"
        elif self.strikes == 1:
            return "On Notice"
        else:
            return "Active"

    @property
    def status_emoji(self) -> str:
        """Get emoji for team status."""
        if self.eliminated:
            return "☠️"
        elif self.strikes == 1:
            return "⚠️"
        else:
            return "-"


@dataclass
class WeekScore:
    """Represents a team's score for a specific week."""

    team_name: str
    week: int
    actual_score: float
    projected_score: float
    baseline_projection: float
    completion_pct: float
    players_remaining: int
    total_players: int

    @property
    def is_complete(self) -> bool:
        """Check if team's week is complete."""
        return self.completion_pct >= 100.0

    @property
    def projection_change(self) -> float:
        """Calculate change from baseline projection."""
        return self.projected_score - self.baseline_projection


@dataclass
class KORMWeekResult:
    """Results for a complete KORM week."""

    week: int
    scores: List[WeekScore]
    strike_recipients: List[str]
    eliminations: List[str]
    active_teams: int
    teams_on_notice: int
    strike_mode: str  # "2-strike" or "1-strike"

    def get_bottom_teams(self, count: int = 2) -> List[WeekScore]:
        """Get the bottom N teams by projected score."""
        sorted_scores = sorted(self.scores, key=lambda s: s.projected_score)
        return sorted_scores[:count]

    def get_rank(self, team_name: str) -> int:
        """Get team's rank (1-based) for the week."""
        sorted_scores = sorted(self.scores, key=lambda s: s.projected_score, reverse=True)
        for i, score in enumerate(sorted_scores, 1):
            if score.team_name == team_name:
                return i
        return -1


class KORMTracker:
    """Tracks KORM competition state across weeks."""

    def __init__(self, history_dir: Optional[Path] = None):
        """Initialize KORM tracker.

        Args:
            history_dir: Directory containing historical KORM result files
        """
        self.teams: Dict[str, KORMTeam] = {}
        self.week_results: Dict[int, KORMWeekResult] = {}
        self.history_dir = history_dir

        if history_dir:
            self.load_history()

    def load_history(self) -> None:
        """Load historical KORM results from markdown files."""
        if not self.history_dir or not self.history_dir.exists():
            return

        # Load each week's results
        for week_file in sorted(self.history_dir.glob("2025_KORM_week_*_results.md")):
            week_num = self._extract_week_number(week_file.name)
            if week_num:
                self._parse_week_file(week_file, week_num)

    def _extract_week_number(self, filename: str) -> Optional[int]:
        """Extract week number from filename."""
        import re
        match = re.search(r'week_(\d+)_results', filename)
        if match:
            return int(match.group(1))
        return None

    def _parse_week_file(self, filepath: Path, week: int) -> None:
        """Parse a week results markdown file."""
        # This is a simplified parser - in production you'd want more robust parsing
        content = filepath.read_text()

        # Extract strike recipients and eliminations from the content
        # This is a placeholder - you'd implement full markdown parsing here
        pass

    def add_team(self, name: str, abbr: str, team_id: int) -> None:
        """Add a team to KORM tracking."""
        self.teams[name] = KORMTeam(name, abbr, team_id)

    def record_strike(self, team_name: str, week: int) -> None:
        """Record a strike for a team."""
        if team_name not in self.teams:
            return

        team = self.teams[team_name]
        team.strikes += 1
        team.strike_weeks.append(week)

        if team.strikes >= 2:
            team.eliminated = True
            team.eliminated_week = week

    def get_active_teams(self) -> List[KORMTeam]:
        """Get list of active (non-eliminated) teams."""
        return [t for t in self.teams.values() if not t.eliminated]

    def get_teams_on_notice(self) -> List[KORMTeam]:
        """Get list of teams with 1 strike (on notice)."""
        return [t for t in self.teams.values() if t.strikes == 1 and not t.eliminated]

    def get_strike_mode(self) -> str:
        """Determine current strike mode based on active teams."""
        active_count = len(self.get_active_teams())
        return "2-strike" if active_count >= 6 else "1-strike"

    def get_strikes_awarded(self) -> int:
        """Get number of strikes awarded per week based on mode."""
        return 2 if self.get_strike_mode() == "2-strike" else 1


class KORMReportGenerator:
    """Generates formatted KORM reports."""

    def __init__(self, tracker: KORMTracker):
        """Initialize report generator.

        Args:
            tracker: KORMTracker instance with current state
        """
        self.tracker = tracker

    def generate_live_report(
        self,
        week: int,
        scores: List[WeekScore],
        output_path: Optional[Path] = None
    ) -> str:
        """Generate a live KORM update report.

        Args:
            week: Current week number
            scores: List of WeekScore objects for active teams
            output_path: Optional path to write report

        Returns:
            Formatted markdown report
        """
        # Sort teams by projected score (high to low)
        sorted_scores = sorted(scores, key=lambda s: s.projected_score, reverse=True)

        # Determine bottom teams (strike recipients)
        strikes_awarded = self.tracker.get_strikes_awarded()
        bottom_teams = sorted_scores[-strikes_awarded:]
        safe_teams = sorted_scores[:-strikes_awarded]

        # Build report sections
        report_parts = [
            self._generate_header(week),
            self._generate_standings_table(safe_teams, bottom_teams),
            self._generate_storylines(sorted_scores, bottom_teams),
            self._generate_live_game_updates(scores),
            self._generate_scenarios(sorted_scores, bottom_teams),
            self._generate_current_standings(),
            self._generate_implications(week, bottom_teams),
            self._generate_footer(week)
        ]

        report = "\n\n---\n\n".join(filter(None, report_parts))

        if output_path:
            output_path.write_text(report)

        return report

    def _generate_header(self, week: int) -> str:
        """Generate report header."""
        timestamp = datetime.now().strftime("%A, %B %d, %Y")
        return f"""# 🔴 LIVE KORM Week {week} Update - RFFL 2025

**⏰ Status: IN PROGRESS** | Updated {timestamp}"""

    def _generate_standings_table(
        self,
        safe_teams: List[WeekScore],
        bottom_teams: List[WeekScore]
    ) -> str:
        """Generate standings table with safe zone and danger zone."""
        lines = ["## 🎯 **PROJECTED KORM Standings (Active Teams Only)**"]
        lines.append("")
        lines.append("### ✅ SAFE ZONE")
        lines.append("")
        lines.append("| Rank | Team | Current | Projected | Complete | KORM Status |")
        lines.append("|------|------|---------|-----------|----------|-------------|")

        for i, score in enumerate(safe_teams, 1):
            team = self.tracker.teams.get(score.team_name)
            status = team.status if team else "Unknown"
            complete_str = "✓" if score.is_complete else f"{score.completion_pct:.1f}%"

            lines.append(
                f"| {i}️⃣ | **{score.team_name}** | {score.actual_score:.2f} | "
                f"**{score.projected_score:.1f}** | {complete_str} | {status} |"
            )

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("### 🚨 DANGER ZONE (Strike Recipients)")
        lines.append("")
        lines.append("| Rank | Team | Current | Projected | Complete | KORM Status |")
        lines.append("|------|------|---------|-----------|----------|-------------|")

        start_rank = len(safe_teams) + 1
        for i, score in enumerate(bottom_teams, start_rank):
            team = self.tracker.teams.get(score.team_name)
            status = "⚠️ **PROJECTED STRIKE**"
            complete_str = "✓" if score.is_complete else f"{score.completion_pct:.1f}%"

            lines.append(
                f"| {i}️⃣ | **{score.team_name}** | {score.actual_score:.2f} | "
                f"**{score.projected_score:.1f}** | {complete_str} | {status} |"
            )

        return "\n".join(lines)

    def _generate_storylines(
        self,
        all_scores: List[WeekScore],
        bottom_teams: List[WeekScore]
    ) -> str:
        """Generate key storylines section."""
        lines = ["## 🔥 **Key Storylines to Watch**"]
        lines.append("")

        # Find biggest gainers and fallers
        sorted_by_change = sorted(all_scores, key=lambda s: s.projection_change, reverse=True)
        biggest_gainer = sorted_by_change[0] if sorted_by_change else None
        biggest_faller = sorted_by_change[-1] if sorted_by_change else None

        # Teams on the bubble
        if len(all_scores) > len(bottom_teams):
            bubble_team = all_scores[-(len(bottom_teams) + 1)]
            lines.append(f"### 🎯 **Bubble Watch**")
            lines.append(f"- **{bubble_team.team_name}** at {bubble_team.projected_score:.1f} pts")
            lines.append(f"- Only {bubble_team.projected_score - bottom_teams[0].projected_score:.1f} pts ahead of danger zone")
            lines.append("")

        return "\n".join(lines)

    def _generate_live_game_updates(self, scores: List[WeekScore]) -> str:
        """Generate live game updates section."""
        incomplete_scores = [s for s in scores if not s.is_complete]

        if not incomplete_scores:
            return "## ✅ **All Games Complete**\n\nAll teams have finished their week."

        lines = ["## 🏈 **Live Game Updates**"]
        lines.append("")
        lines.append(f"**{len(incomplete_scores)} teams still have players in action**")
        lines.append("")

        return "\n".join(lines)

    def _generate_scenarios(
        self,
        all_scores: List[WeekScore],
        bottom_teams: List[WeekScore]
    ) -> str:
        """Generate possible scenarios section."""
        lines = ["## 🔮 **Possible Scenarios**"]
        lines.append("")
        lines.append("### Scenario 1: Current Projections Hold ✅ (Most Likely)")
        lines.append("- **Strike Recipients:** " + ", ".join(s.team_name for s in bottom_teams))
        lines.append("")

        return "\n".join(lines)

    def _generate_current_standings(self) -> str:
        """Generate current KORM standings table."""
        lines = ["## 🏆 **Current KORM Standings**"]
        lines.append("")
        lines.append("| Team | Strikes | Status | Strike History |")
        lines.append("|------|---------|--------|----------------|")

        # Active teams
        active_teams = sorted(
            self.tracker.get_active_teams(),
            key=lambda t: (t.strikes, t.name)
        )

        for team in active_teams:
            strike_history = ", ".join(f"W{w}" for w in team.strike_weeks) if team.strike_weeks else "-"
            lines.append(
                f"| {team.name} | {team.status_emoji} | {team.status} | {strike_history} |"
            )

        # Eliminated teams
        eliminated = [t for t in self.tracker.teams.values() if t.eliminated]
        for team in sorted(eliminated, key=lambda t: t.eliminated_week):
            strike_history = ", ".join(f"W{w}" for w in team.strike_weeks)
            lines.append(
                f"| **{team.name}** | {team.status_emoji} | **{team.status}** | {strike_history} |"
            )

        return "\n".join(lines)

    def _generate_implications(self, week: int, bottom_teams: List[WeekScore]) -> str:
        """Generate implications section."""
        active_count = len(self.tracker.get_active_teams())
        on_notice = len(self.tracker.get_teams_on_notice())

        lines = [f"## ⚠️ **Week {week} Implications**"]
        lines.append("")
        lines.append(f"- **{active_count} teams remain active**")
        lines.append(f"- **{on_notice} teams on notice** (1 strike)")
        lines.append(f"- **Strike mode**: {self.tracker.get_strike_mode()}")
        lines.append("")

        return "\n".join(lines)

    def _generate_footer(self, week: int) -> str:
        """Generate report footer."""
        timestamp = datetime.now().strftime("%A, %B %d, %Y %I:%M %p ET")
        return f"""---

*🔴 LIVE Data from ESPN API • Year: 2025 • Week: {week}*
*⏰ Last Updated: {timestamp}*
*⚠️ Projections subject to change based on remaining games*"""


def load_historical_korm_state(history_dir: Path) -> KORMTracker:
    """Load KORM state from historical markdown files.

    Args:
        history_dir: Directory containing KORM history files

    Returns:
        Initialized KORMTracker with historical data
    """
    tracker = KORMTracker(history_dir)

    # Manually initialize known teams and state
    # This would be extracted from historical files in production
    teams_data = {
        "Great Fantasy Minds": ("GFM", 1),
        "PKMC Unhinged": ("PKMC", 2),
        "Least Needlish Ones": ("LNO", 3),
        "Mex Banese": ("MXLB", 4),
        "Gypsy PCX": ("PCX", 5),
        "White Wizards": ("WZRD", 6),
        "Tactical Tacticians": ("TACT", 7),
        "Alpha Chalkers": ("CHLK", 8),
        "Mary Jane": ("MRYJ", 9),
        "Jag Bombers": ("JAGB", 10),
        "Tennessee Typicals": ("TNT", 11),
        "Brimstone Bohemians": ("BRIM", 12),
    }

    for name, (abbr, team_id) in teams_data.items():
        tracker.add_team(name, abbr, team_id)

    # Record historical strikes (from Week 1-5 files)
    historical_strikes = [
        ("Tennessee Typicals", 1),
        ("Brimstone Bohemians", 1),
        ("Least Needlish Ones", 2),
        ("Brimstone Bohemians", 2),  # Eliminated W2
        ("Jag Bombers", 3),
        ("White Wizards", 3),
        ("Mary Jane", 4),
        ("Tennessee Typicals", 4),  # Eliminated W4
        ("Gypsy PCX", 5),
        ("Jag Bombers", 5),  # Eliminated W5
    ]

    for team_name, week in historical_strikes:
        tracker.record_strike(team_name, week)

    return tracker
