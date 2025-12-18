"""Utilities for fetching live ESPN fantasy scoring data."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from rich.console import Console
from rich.table import Table

LM_API_BASE_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"

console = Console()


class LiveScoringError(RuntimeError):
    """Raised when live scoring data cannot be retrieved or parsed."""


@dataclass(slots=True)
class LiveScoreClient:
    """Client for fetching live scoreboard and roster data from ESPN."""

    league_id: int
    season: int
    segment_id: int = 0
    timeout: float = 10.0
    espn_s2: str | None = None
    swid: str | None = None

    def _league_url(self) -> str:
        return (
            f"{LM_API_BASE_URL}/seasons/{self.season}/segments/{self.segment_id}/"
            f"leagues/{self.league_id}"
        )

    def _get(self, params: Iterable[tuple[str, Any]]) -> dict[str, Any]:
        """Execute a GET request with common settings."""
        query = urlencode(list(params), doseq=True)
        headers = {"Accept": "application/json", "User-Agent": "rffl-recipes/1.0"}
        cookie_header = self._build_cookie_header()
        if cookie_header:
            headers["Cookie"] = cookie_header

        request = Request(url=f"{self._league_url()}?{query}", headers=headers)

        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = response.read()
        except HTTPError as exc:  # pragma: no cover - network failure scenario
            error_detail = getattr(exc, "reason", "") or "HTTP error"
            raise LiveScoringError(
                f"ESPN API returned status {exc.code}: {error_detail}"
            ) from exc
        except URLError as exc:  # pragma: no cover - network failure scenario
            raise LiveScoringError(f"HTTP request failed: {exc.reason}") from exc

        try:
            return json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - invalid payload scenario
            raise LiveScoringError("Failed to parse JSON payload") from exc

    def _build_cookie_header(self) -> str | None:
        """Create cookie header for private leagues when credentials provided."""
        parts: list[str] = []
        if self.espn_s2:
            parts.append(f"espn_s2={self.espn_s2}")
        if self.swid:
            parts.append(f"SWID={self.swid}")
        if not parts:
            return None
        return "; ".join(parts)

    def fetch_settings(self) -> dict[str, Any]:
        """Fetch league settings including current scoring period."""
        return self._get([("view", "mSettings")])

    def get_current_scoring_period(self) -> int:
        """Return the current scoring period for the league."""
        settings = self.fetch_settings()
        status = settings.get("status") or {}
        scoring_period = (
            status.get("currentScoringPeriod")
            or status.get("currentMatchupPeriod")
            or status.get("latestScoringPeriod")
        )
        if scoring_period is None:
            raise LiveScoringError("currentScoringPeriod not found in settings response")
        return int(scoring_period)

    def fetch_scoreboard(
        self,
        scoring_period: int,
        include_boxscore: bool = False,
        include_live: bool = False,
    ) -> dict[str, Any]:
        """Fetch scoreboard (and optionally roster) data for a scoring period."""
        params: list[tuple[str, Any]] = [
            ("view", "mMatchupScore"),
            ("view", "mTeam"),
            ("view", "mSettings"),
            ("scoringPeriodId", scoring_period),
        ]
        if include_boxscore:
            params.append(("view", "mRoster"))
        if include_live:
            params.append(("view", "mLiveScoring"))
            params.append(("view", "mScoreboard"))
        return self._get(params)


LiveCommandMode = Literal["scoreboard", "boxscore", "combined"]
LIVE_COMMAND_MODES: tuple[LiveCommandMode, ...] = (
    "scoreboard",
    "boxscore",
    "combined",
)


def fetch_and_render_live_scores(
    league_id: int,
    season: int,
    scoring_period: int | None,
    mode: LiveCommandMode,
    timeout: float = 10.0,
    espn_s2: str | None = None,
    swid: str | None = None,
) -> dict[str, Any]:
    """Fetch and render live scores, returning the raw payload."""
    client = LiveScoreClient(
        league_id=league_id,
        season=season,
        timeout=timeout,
        espn_s2=espn_s2,
        swid=swid,
    )

    period = scoring_period or client.get_current_scoring_period()

    include_boxscore = mode in ("boxscore", "combined")
    data = client.fetch_scoreboard(
        period,
        include_boxscore=include_boxscore,
        include_live=True,
    )

    teams = data.get("teams") or []
    team_lookup = {team.get("id"): team for team in teams if team.get("id") is not None}
    slot_names = _build_slot_map(data)

    if mode in ("scoreboard", "combined"):
        console.print(build_scoreboard_table(data, team_lookup, period))

    if mode in ("boxscore", "combined"):
        _print_boxscore_summary(data, team_lookup, slot_names, period)

    return data


def build_scoreboard_table(
    data: dict[str, Any],
    team_lookup: dict[int, dict[str, Any]],
    scoring_period: int,
) -> Table:
    """Build a Rich table summarizing matchup scores."""
    schedule = [
        matchup
        for matchup in data.get("schedule", [])
        if matchup.get("matchupPeriodId") == scoring_period
    ]

    table = Table(title=f"Live Matchup Scores - Week {scoring_period}")
    table.add_column("Matchup", style="cyan")
    table.add_column("Home", style="green")
    table.add_column("Home Score", justify="right")
    table.add_column("Away", style="magenta")
    table.add_column("Away Score", justify="right")
    table.add_column("Status", style="yellow")

    if not schedule:
        table.add_row("-", "-", "-", "-", "-", "No matchups found")
        return table

    for matchup in schedule:
        home = matchup.get("home") or {}
        away = matchup.get("away") or {}

        home_team = _format_team(home, team_lookup)
        away_team = _format_team(away, team_lookup)

        home_score = _format_score(home, scoring_period)
        away_score = _format_score(away, scoring_period)

        raw_status = matchup.get("winner") or "UNDECIDED"
        status = raw_status.replace("_", " ").title()

        table.add_row(
            str(matchup.get("matchupPeriodId", "-")),
            home_team,
            home_score,
            away_team,
            away_score,
            status,
        )

    return table


def _format_team(entry: dict[str, Any], team_lookup: dict[int, dict[str, Any]]) -> str:
    team_id = entry.get("teamId")
    team = team_lookup.get(team_id, {})
    name = team.get("name") or f"Team {team_id}"
    abbrev = team.get("abbrev")
    if abbrev:
        return f"{name} ({abbrev})"
    return name


def _format_score(entry: dict[str, Any], scoring_period: int) -> str:
    points_by_period = entry.get("pointsByScoringPeriod") or {}
    score = (
        points_by_period.get(str(scoring_period))
        or points_by_period.get(scoring_period)
        or entry.get("totalPoints")
        or 0.0
    )
    return f"{float(score):.2f}"


def _build_slot_map(data: dict[str, Any]) -> dict[int, str]:
    slot_items = (data.get("settings") or {}).get("slotCategoryItems") or []
    slot_map: dict[int, str] = {}
    for item in slot_items:
        slot_id = item.get("id")
        name = item.get("name")
        if slot_id is None or not name:
            continue
        slot_map[int(slot_id)] = str(name)
    return slot_map


def _print_boxscore_summary(
    data: dict[str, Any],
    team_lookup: dict[int, dict[str, Any]],
    slot_names: dict[int, str],
    scoring_period: int,
) -> None:
    """Print a condensed summary of player-level scoring if present."""
    schedule = [
        matchup
        for matchup in data.get("schedule", [])
        if matchup.get("matchupPeriodId") == scoring_period
    ]

    if not schedule:
        console.print("[yellow]No matchups to display boxscores for.[/yellow]")
        return

    rosters = {
        team_id: (team.get("roster") or {}).get("entries") or []
        for team_id, team in team_lookup.items()
    }

    for matchup in schedule:
        matchup_id = matchup.get("matchupPeriodId", "-")
        console.print(f"\n[bold]Matchup Period {matchup_id}[/bold]")
        for side_key in ("home", "away"):
            team_entry = matchup.get(side_key) or {}
            team_id = team_entry.get("teamId")
            team_label = _format_team(team_entry, team_lookup)
            console.print(f"  [green]{team_label}[/green]")

            entries = rosters.get(team_id) or []
            if not entries:
                console.print("    [yellow]No roster data available.[/yellow]")
                continue

            for entry in entries:
                player = entry.get("playerPoolEntry", {}).get("player", {})
                name = (
                    player.get("fullName")
                    or f"{player.get('firstName', 'Unknown')} {player.get('lastName', '').strip()}"
                ).strip()
                slot_id = entry.get("lineupSlotId")
                slot_name = slot_names.get(slot_id, str(slot_id))
                points = entry.get("appliedStatTotal") or 0.0
                console.print(f"    {slot_name}: {name} - {float(points):.2f} pts")
