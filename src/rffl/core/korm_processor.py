"""KORM (King of Rage Mountain) historical results processor.

This module processes historical KORM competition results from season data,
applying the official KORM rules to determine strikes, eliminations, and
final standings.

KORM Rules:
- Two-strike elimination: Teams accumulate strikes, 2 strikes = eliminated
- Strike mode: 5+ active teams = 2-strike mode, 4 or fewer = 1-strike mode
- Ties: All teams tied at strike threshold receive strikes
- Season window: 2018-2020 (weeks 1-13), 2021+ (weeks 1-14)
"""

import csv
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pandas as pd  # type: ignore[import-untyped]


# Season configuration
SEASON_CONFIG = {
    2018: {"weeks": (1, 13), "entry_fee": 40, "pool": 480, "note": "Pilot year"},
    2019: {"weeks": (1, 13), "entry_fee": 100, "pool": 1200},
    2020: {"weeks": (1, 13), "entry_fee": 100, "pool": 1200},
    2021: {"weeks": (1, 14), "entry_fee": 100, "pool": 1200},
    2022: {"weeks": (1, 14), "entry_fee": 100, "pool": 1200},
    2023: {"weeks": (1, 14), "entry_fee": 100, "pool": 1200},
    2024: {"weeks": (1, 14), "entry_fee": 100, "pool": 1200},
    2025: {"weeks": (1, 14), "entry_fee": 100, "pool": 1200},
}

# Payout structure (2019+)
PAYOUTS = {
    1: 800,  # 1st place
    2: 300,  # 2nd place
    3: 100,  # 3rd place
}

# 2018 pilot year payouts (scaled from $480 pool)
PAYOUTS_2018 = {
    1: 320,  # 66.7%
    2: 120,  # 25%
    3: 40,   # 8.3%
}


@dataclass
class KORMStrike:
    """Records a single strike event."""
    week: int
    score: float


@dataclass
class KORMTeamResult:
    """Final result for a team in KORM competition."""
    team_code: str
    strikes: list[KORMStrike] = field(default_factory=list)
    status: str = "active"  # "active", "on_notice", "eliminated"
    elimination_week: int | None = None
    final_place: int | None = None
    payout: int = 0

    @property
    def strike_count(self) -> int:
        return len(self.strikes)

    @property
    def strike_weeks(self) -> list[int]:
        return [s.week for s in self.strikes]


@dataclass
class KORMWeekResult:
    """Results from processing a single KORM week."""
    week: int
    active_count_start: int
    strike_mode: str  # "2-strike" or "1-strike"
    scores: list[dict[str, Any]]  # [{team: str, score: float}, ...]
    strikes_given: list[str]  # team codes that received strikes
    eliminations: list[str]  # team codes eliminated this week
    active_count_end: int


@dataclass
class KORMSeasonResult:
    """Complete KORM results for a season."""
    season: int
    korm_window: tuple[int, int]
    entry_fee: int
    pool: int
    teams: list[str]
    weeks: list[KORMWeekResult]
    team_results: dict[str, KORMTeamResult]
    winner: str | None = None
    ended_early: bool = False  # True if 1 team remained before final week


def load_weekly_scores_from_h2h(h2h_path: Path, max_week: int) -> dict[int, dict[str, float]]:
    """
    Load weekly scores from h2h.csv format (2018).

    Args:
        h2h_path: Path to h2h.csv file
        max_week: Maximum week to include (KORM window end)

    Returns:
        {week: {team_code: actual_score}}
    """
    df = pd.read_csv(h2h_path)
    weekly_scores: dict[int, dict[str, float]] = {}

    for _, row in df.iterrows():
        week = int(row["week"])
        if week > max_week:
            continue

        if week not in weekly_scores:
            weekly_scores[week] = {}

        # Extract home team score
        home_team = row["home_team"]
        home_score = float(row["home_score"])
        weekly_scores[week][home_team] = home_score

        # Extract away team score
        away_team = row["away_team"]
        away_score = float(row["away_score"])
        weekly_scores[week][away_team] = away_score

    return weekly_scores


def load_weekly_scores_from_teamweek(
    teamweek_path: Path,
    max_week: int
) -> dict[int, dict[str, float]]:
    """
    Load weekly scores from teamweek_unified.csv format (2019+).

    Args:
        teamweek_path: Path to teamweek_unified.csv file
        max_week: Maximum week to include (KORM window end)

    Returns:
        {week: {team_code: actual_score}}
    """
    df = pd.read_csv(teamweek_path)
    weekly_scores: dict[int, dict[str, float]] = {}

    for _, row in df.iterrows():
        week = int(row["week"])
        if week > max_week:
            continue

        if week not in weekly_scores:
            weekly_scores[week] = {}

        team_code = row["team_code"]
        score = float(row["team_actual_total"])
        weekly_scores[week][team_code] = score

    return weekly_scores


def load_weekly_scores(year: int, repo_root: Path) -> dict[int, dict[str, float]]:
    """
    Load weekly scores for a season from appropriate data source.

    Args:
        year: Season year
        repo_root: Repository root path

    Returns:
        {week: {team_code: actual_score}}

    Raises:
        FileNotFoundError: If data file doesn't exist
    """
    season_dir = repo_root / "data" / "seasons" / str(year)
    config = SEASON_CONFIG.get(year, {"weeks": (1, 14), "entry_fee": 100, "pool": 1200})
    weeks_tuple = cast(tuple[int, int], config["weeks"])
    max_week = weeks_tuple[1]

    if year == 2018:
        # Use h2h.csv format
        h2h_path = season_dir / "h2h.csv"
        if not h2h_path.exists():
            raise FileNotFoundError(f"h2h.csv not found for {year}")
        return load_weekly_scores_from_h2h(h2h_path, max_week)
    else:
        # Use teamweek_unified.csv format
        teamweek_path = season_dir / "reports" / "teamweek_unified.csv"
        if not teamweek_path.exists():
            raise FileNotFoundError(f"teamweek_unified.csv not found for {year}")
        return load_weekly_scores_from_teamweek(teamweek_path, max_week)


def process_korm_week(
    week: int,
    scores: dict[str, float],
    team_results: dict[str, KORMTeamResult],
) -> KORMWeekResult:
    """
    Process a single week of KORM competition.

    Args:
        week: Week number
        scores: {team_code: actual_score} for ALL teams
        team_results: Current state of all teams (will be modified)

    Returns:
        KORMWeekResult with week's outcomes
    """
    # Step 1: Get active teams at start of week
    active_teams = [
        code for code, result in team_results.items()
        if result.status != "eliminated"
    ]
    active_count_start = len(active_teams)

    # Filter scores to active teams only
    active_scores = {team: scores[team] for team in active_teams if team in scores}

    # Step 2: Determine strike mode
    # 5 or more active = 2-strike mode, 4 or fewer = 1-strike mode
    strike_mode = "2-strike" if active_count_start >= 5 else "1-strike"
    strike_count = 2 if strike_mode == "2-strike" else 1

    # Step 3: Sort teams by score (low to high)
    sorted_teams = sorted(active_scores.items(), key=lambda x: x[1])

    # Step 4: Identify teams to strike (handle ties)
    teams_to_strike = []

    if len(sorted_teams) >= strike_count:
        # Get threshold score (2nd lowest for 2-strike, lowest for 1-strike)
        threshold_idx = strike_count - 1
        threshold_score = sorted_teams[threshold_idx][1]

        # Strike ALL teams at or below threshold
        teams_to_strike = [
            team for team, score in sorted_teams
            if score <= threshold_score
        ]

    # Step 5: Build scores list for output
    scores_list = [
        {"team": team, "score": score}
        for team, score in sorted(active_scores.items(), key=lambda x: -x[1])
    ]

    # Step 6: Assign strikes and check eliminations
    eliminations = []
    for team_code in teams_to_strike:
        result = team_results[team_code]
        strike = KORMStrike(week=week, score=scores[team_code])
        result.strikes.append(strike)

        if result.strike_count >= 2:
            result.status = "eliminated"
            result.elimination_week = week
            eliminations.append(team_code)
        elif result.strike_count == 1:
            result.status = "on_notice"

    # Count active at end of week
    active_count_end = sum(
        1 for r in team_results.values() if r.status != "eliminated"
    )

    return KORMWeekResult(
        week=week,
        active_count_start=active_count_start,
        strike_mode=strike_mode,
        scores=scores_list,
        strikes_given=teams_to_strike,
        eliminations=eliminations,
        active_count_end=active_count_end,
    )


def process_korm_season(year: int, weekly_scores: dict[int, dict[str, float]]) -> KORMSeasonResult:
    """
    Process complete KORM season.

    Args:
        year: Season year
        weekly_scores: {week: {team_code: actual_score}}

    Returns:
        KORMSeasonResult with complete season results
    """
    config = SEASON_CONFIG.get(year, {"weeks": (1, 14), "entry_fee": 100, "pool": 1200})
    weeks_tuple = cast(tuple[int, int], config["weeks"])
    start_week, end_week = weeks_tuple
    entry_fee_raw = config.get("entry_fee", 100)
    pool_raw = config.get("pool", 1200)
    entry_fee = cast(int, entry_fee_raw) if entry_fee_raw is not None else 100
    pool = cast(int, pool_raw) if pool_raw is not None else 1200

    # Get all teams from week 1 data
    if 1 not in weekly_scores:
        raise ValueError(f"No week 1 data for {year}")

    teams = list(weekly_scores[1].keys())

    # Initialize team results
    team_results: dict[str, KORMTeamResult] = {
        team: KORMTeamResult(team_code=team)
        for team in teams
    }

    # Process each week
    week_results: list[KORMWeekResult] = []
    ended_early = False

    for week in range(start_week, end_week + 1):
        if week not in weekly_scores:
            continue

        # Check if competition already ended
        active_count = sum(
            1 for r in team_results.values() if r.status != "eliminated"
        )
        if active_count <= 1:
            ended_early = True
            break

        week_result = process_korm_week(week, weekly_scores[week], team_results)
        week_results.append(week_result)

    # Determine final standings
    _assign_final_standings(team_results, weekly_scores, year)

    # Get winner
    winner = None
    for code, result in team_results.items():
        if result.final_place == 1:
            winner = code
            break

    return KORMSeasonResult(
        season=year,
        korm_window=(int(start_week), int(end_week)),
        entry_fee=int(entry_fee),
        pool=int(pool),
        teams=teams,
        weeks=week_results,
        team_results=team_results,
        winner=winner,
        ended_early=ended_early,
    )


def _assign_final_standings(
    team_results: dict[str, KORMTeamResult],
    weekly_scores: dict[int, dict[str, float]],
    year: int,
) -> None:
    """
    Assign final standings and payouts to all teams.

    Ranking rules:
    1. Active teams ranked by fewest strikes
    2. Eliminated teams ranked by elimination week (later = better)
    3. Ties broken by total season points
    """
    payouts = PAYOUTS_2018 if year == 2018 else PAYOUTS

    # Calculate total season points for tiebreaking
    total_points: dict[str, float] = {}
    for team in team_results:
        total_points[team] = sum(
            scores.get(team, 0)
            for scores in weekly_scores.values()
        )

    # Separate active and eliminated
    active = [r for r in team_results.values() if r.status != "eliminated"]
    eliminated = [r for r in team_results.values() if r.status == "eliminated"]

    # Sort active by strikes (fewer = better), then by total points (higher = better)
    active.sort(key=lambda r: (r.strike_count, -total_points.get(r.team_code, 0)))

    # Sort eliminated by elimination week (later = better), then total points
    eliminated.sort(key=lambda r: (-r.elimination_week if r.elimination_week else 0,
                                   -total_points.get(r.team_code, 0)))

    # Assign places
    place = 1
    for result in active:
        result.final_place = place
        result.payout = payouts.get(place, 0)
        place += 1

    for result in eliminated:
        result.final_place = place
        result.payout = payouts.get(place, 0)
        place += 1


def generate_korm_markdown(result: KORMSeasonResult) -> str:
    """
    Generate markdown report for a KORM season.

    Args:
        result: KORMSeasonResult to format

    Returns:
        Formatted markdown string
    """
    lines = [
        f"# KORM History - {result.season} Season",
        "",
        "## Season Info",
        f"- **Entry Fee:** ${result.entry_fee}/team",
        f"- **Pool:** ${result.pool:,}",
        f"- **Window:** Weeks {result.korm_window[0]}-{result.korm_window[1]}",
        f"- **Teams:** {len(result.teams)}",
    ]

    if result.ended_early:
        lines.append("- **Status:** Ended early (Last Team Standing)")

    lines.extend(["", "---", "", "## Week-by-Week Results"])

    # Track cumulative strikes for each team as we iterate through weeks
    cumulative_strikes: dict[str, int] = {team: 0 for team in result.teams}

    # Week-by-week results
    for week in result.weeks:
        lines.extend([
            "",
            f"### Week {week.week}",
            f"- **Active:** {week.active_count_start} | **Mode:** {week.strike_mode}",
            "",
            "| Rank | Team | Score | Status |",
            "|------|------|-------|--------|",
        ])

        # Update cumulative strikes for this week's strikes
        for team in week.strikes_given:
            cumulative_strikes[team] += 1

        for i, score_entry in enumerate(week.scores, 1):
            team = score_entry["team"]
            score = score_entry["score"]

            if team in week.eliminations:
                status = "☠️ ELIMINATED"
            elif team in week.strikes_given:
                strike_num = cumulative_strikes[team]
                if strike_num == 1:
                    status = "⚠️ Strike 1"
                else:
                    status = "⚠️ Strike 2"
            else:
                status = "Safe"

            lines.append(f"| {i} | {team} | {score:.2f} | {status} |")

        if week.eliminations:
            lines.append("")
            lines.append(f"**Eliminations:** {', '.join(week.eliminations)}")

    # Final standings
    lines.extend([
        "",
        "---",
        "",
        "## Final Standings",
        "",
        "| Place | Team | Strikes | Strike History | Prize |",
        "|-------|------|---------|----------------|-------|",
    ])

    sorted_results = sorted(
        result.team_results.values(),
        key=lambda r: r.final_place if r.final_place else 999
    )

    for team_result in sorted_results:
        place = team_result.final_place or "-"
        strikes = team_result.strike_count
        strike_history = ", ".join(f"W{w}" for w in team_result.strike_weeks) or "-"
        payout = f"${team_result.payout}" if team_result.payout else "-"

        if team_result.status == "eliminated":
            team_display = f"~~{team_result.team_code}~~"
        else:
            team_display = f"**{team_result.team_code}**"

        lines.append(f"| {place} | {team_display} | {strikes} | {strike_history} | {payout} |")

    # Champion
    if result.winner:
        lines.extend([
            "",
            "---",
            "",
            f"## Champion: {result.winner} 🏆",
        ])

    # Footer
    lines.extend([
        "",
        "---",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "*RFFL League ID: 323196*",
    ])

    return "\n".join(lines)


def generate_korm_json(result: KORMSeasonResult) -> dict[str, Any]:
    """
    Generate JSON structure for a KORM season.

    Args:
        result: KORMSeasonResult to format

    Returns:
        JSON-serializable dictionary
    """
    return {
        "season": result.season,
        "korm_window": {"start": result.korm_window[0], "end": result.korm_window[1]},
        "entry_fee": result.entry_fee,
        "pool": result.pool,
        "teams": result.teams,
        "ended_early": result.ended_early,
        "weeks": [
            {
                "week": w.week,
                "active_count": w.active_count_start,
                "strike_mode": w.strike_mode,
                "scores": w.scores,
                "strikes": w.strikes_given,
                "eliminations": w.eliminations,
            }
            for w in result.weeks
        ],
        "final_standings": [
            {
                "place": r.final_place,
                "team": r.team_code,
                "strikes": r.strike_count,
                "strike_weeks": r.strike_weeks,
                "status": r.status,
                "elimination_week": r.elimination_week,
                "payout": r.payout,
            }
            for r in sorted(
                result.team_results.values(),
                key=lambda x: x.final_place if x.final_place else 999
            )
        ],
        "winner": result.winner,
        "generated": datetime.now().isoformat(),
    }


def process_and_save_korm_season(
    year: int,
    repo_root: Path,
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """
    Process KORM for a season and save results.

    Args:
        year: Season year
        repo_root: Repository root path
        output_dir: Output directory (defaults to season directory)

    Returns:
        Tuple of (json_path, markdown_path)

    Raises:
        FileNotFoundError: If required data files don't exist
    """
    # Load scores
    weekly_scores = load_weekly_scores(year, repo_root)

    # Process KORM
    result = process_korm_season(year, weekly_scores)

    # Determine output directory
    if output_dir is None:
        output_dir = repo_root / "data" / "seasons" / str(year)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_path = output_dir / "korm_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(generate_korm_json(result), f, indent=2)

    # Save Markdown
    md_path = output_dir / "korm_history.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(generate_korm_markdown(result))

    return json_path, md_path
