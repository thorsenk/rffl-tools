"""Generate live fantasy matchup reports using ESPN API data."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import LM_API_BASE_URL, LiveScoreClient, LiveScoringError

PRO_SCHEDULE_HEADERS = {
    "User-Agent": "rffl-recipes/1.0",
    "Accept": "application/json, text/plain, */*",
    "Connection": "keep-alive",
    "X-Fantasy-Source": "kona",
    "x-fantasy-platform": "kona",
}

EVENT_HEADERS = {
    "User-Agent": "rffl-recipes/1.0",
    "Accept": "application/json, text/plain, */*",
}

STARTER_SLOT_ORDER: Tuple[int, ...] = (0, 2, 2, 4, 4, 6, 23, 16, 17)
SLOT_LABELS: Dict[int, str] = {
    0: "QB",
    2: "RB",
    4: "WR",
    6: "TE",
    16: "D/ST",
    17: "K",
    23: "FLEX",
}
POSITION_LABELS: Dict[int, str] = {
    1: "QB",
    2: "RB",
    3: "WR",
    4: "TE",
    5: "K",
    16: "D/ST",
}
PLAYER_SUFFIXES = {"Jr.", "Sr.", "II", "III", "IV", "V"}


@dataclass(slots=True)
class EventStatus:
    """Parsed event status payload."""

    state: str
    detail: str
    short_detail: str
    clock: float | None
    period: int | None
    start_time: datetime | None


@dataclass(slots=True)
class GameStatusView:
    """Normalized view of an event status for display and calculations."""

    label: str
    state: str
    time_pct: float
    minutes_remaining: float


@dataclass(slots=True)
class PlayerCard:
    slot_label: str
    name: str
    nfl_team: str
    position: str
    baseline: float
    actual: float
    performance_pct: float
    time_played_pct: float
    minutes_remaining: float
    game_status: str
    pace_indicator: str
    game_state: str


@dataclass(slots=True)
class TeamReport:
    name: str
    actual_points: float
    live_projection: float
    baseline_projection: float
    minutes_remaining: float
    players: List[PlayerCard]

    @property
    def projection_delta(self) -> float:
        return self.live_projection - self.baseline_projection

    @property
    def minutes_used(self) -> float:
        return max(0.0, 540.0 - self.minutes_remaining)

    @property
    def minutes_used_pct(self) -> float:
        used = self.minutes_used
        return min(100.0, max(0.0, (used / 540.0) * 100.0))

    @property
    def score_pace_pct(self) -> float:
        if self.baseline_projection <= 0.0:
            return 0.0
        return max(0.0, (self.actual_points / self.baseline_projection) * 100.0)


def fetch_pro_team_data(season: int, timeout: float) -> dict[str, Any]:
    """Return the pro team schedule payload for the requested season."""

    url = f"{LM_API_BASE_URL}/seasons/{season}?view=proTeamSchedules_wl"
    request = Request(url, headers=PRO_SCHEDULE_HEADERS)
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except HTTPError as exc:  # pragma: no cover - network failure
        raise LiveScoringError(
            f"Pro team schedule request failed with status {exc.code}"
        ) from exc
    except URLError as exc:  # pragma: no cover - network failure
        raise LiveScoringError(f"Pro team schedule request failed: {exc.reason}") from exc

    try:
        return json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - invalid payload
        raise LiveScoringError("Failed to parse pro team schedule payload") from exc


def build_pro_lookups(
    pro_data: dict[str, Any]
) -> tuple[Dict[int, str], Dict[tuple[int, int], dict[str, Any]]]:
    """Build lookup maps for pro team abbreviations and weekly games."""

    settings = pro_data.get("settings") or {}
    pro_teams = settings.get("proTeams") or []
    abbrev_by_team: Dict[int, str] = {}
    games_by_team_week: Dict[tuple[int, int], dict[str, Any]] = {}

    for team in pro_teams:
        team_id = team.get("id")
        if team_id is None:
            continue
        abbrev = (team.get("abbrev") or str(team_id)).upper()
        abbrev_by_team[int(team_id)] = abbrev

        games = team.get("proGamesByScoringPeriod") or {}
        for period_key, contests in games.items():
            try:
                period = int(period_key)
            except (TypeError, ValueError):  # pragma: no cover - malformed payload
                continue
            for contest in contests or []:
                games_by_team_week[(int(team_id), period)] = contest

    return abbrev_by_team, games_by_team_week


class EventStatusFetcher:
    """Fetch and cache event status payloads."""

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        self._cache: Dict[int, EventStatus | None] = {}

    def get(self, event_id: int | None) -> EventStatus | None:
        if event_id is None:
            return None
        if event_id in self._cache:
            return self._cache[event_id]

        status = self._fetch_status(event_id)
        self._cache[event_id] = status
        return status

    def _fetch_status(self, event_id: int) -> EventStatus | None:
        event_url = (
            f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{event_id}"
        )
        try:
            with urlopen(Request(event_url, headers=EVENT_HEADERS), timeout=self.timeout) as resp:
                event_payload = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError):  # pragma: no cover - network failure
            return None

        competitions: Iterable[dict[str, Any]] = event_payload.get("competitions") or []
        competition_ref = None
        for comp in competitions:
            ref = comp.get("$ref")
            if ref:
                competition_ref = ref
                break
        if not competition_ref:
            return None

        try:
            with urlopen(Request(competition_ref, headers=EVENT_HEADERS), timeout=self.timeout) as resp:
                competition = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError):  # pragma: no cover - network failure
            return None

        status_info = competition.get("status") or {}
        status_ref = status_info.get("$ref")
        if not status_ref:
            return None

        try:
            with urlopen(Request(status_ref, headers=EVENT_HEADERS), timeout=self.timeout) as resp:
                status_payload = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError):  # pragma: no cover - network failure
            return None

        status_type = status_payload.get("type") or {}
        state = (status_type.get("state") or "pre").lower()
        detail = status_type.get("detail") or ""
        short_detail = status_type.get("shortDetail") or detail
        clock_value = status_payload.get("clock")
        period_value = status_payload.get("period")
        start_time = parse_iso_datetime(competition.get("date"))

        return EventStatus(
            state=state,
            detail=str(detail),
            short_detail=str(short_detail),
            clock=float(clock_value) if clock_value is not None else None,
            period=int(period_value) if period_value is not None else None,
            start_time=start_time,
        )


def parse_iso_datetime(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:  # pragma: no cover - malformed payload
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone()


def extract_projection(player: dict[str, Any], scoring_period: int) -> float:
    for stat in player.get("stats", []) or []:
        if stat.get("statSourceId") == 1 and stat.get("scoringPeriodId") == scoring_period:
            return float(stat.get("appliedTotal") or 0.0)
    return 0.0


def extract_actual(player: dict[str, Any], scoring_period: int) -> float:
    for stat in player.get("stats", []) or []:
        if stat.get("statSourceId") == 0 and stat.get("scoringPeriodId") == scoring_period:
            return float(stat.get("appliedTotal") or 0.0)
    return 0.0


def resolve_event_id(
    player: dict[str, Any],
    scoring_period: int,
    pro_games: Dict[tuple[int, int], dict[str, Any]],
) -> int | None:
    for stat in player.get("stats", []) or []:
        if stat.get("statSourceId") == 0 and stat.get("scoringPeriodId") == scoring_period:
            ext = stat.get("externalId")
            if ext is None:
                continue
            try:
                return int(ext)
            except (TypeError, ValueError):  # pragma: no cover - malformed payload
                continue

    team_id = player.get("proTeamId")
    if team_id is None:
        return None
    game = pro_games.get((int(team_id), scoring_period))
    if not game:
        return None
    try:
        return int(game.get("id"))
    except (TypeError, ValueError):  # pragma: no cover - malformed payload
        return None


def calculate_minutes_remaining(status: EventStatus | None) -> float:
    if status is None:
        return 60.0
    if status.state == "pre":
        return 60.0
    if status.state == "post":
        return 0.0

    period = status.period or 1
    clock_seconds = status.clock if status.clock is not None else 0.0
    if clock_seconds < 0.0:
        clock_seconds = 0.0

    if period <= 4:
        elapsed_before = (period - 1) * 15.0
    else:
        elapsed_before = 60.0 + (period - 5) * 15.0

    elapsed_current = 15.0 - (clock_seconds / 60.0)
    if elapsed_current < 0.0:
        elapsed_current = 0.0
    minutes_elapsed = max(0.0, elapsed_before + elapsed_current)
    if minutes_elapsed >= 60.0:
        return 0.0
    return max(0.0, 60.0 - minutes_elapsed)


def tidy_status_label(label: str) -> str:
    if not label:
        return "TBD"

    text = label.replace(" - ", " ").strip()
    if text.upper() in {"FINAL", "POSTPONED"}:
        return text.upper()

    end_of_quarter = re.match(r"End of (\d+)(st|nd|rd|th) Quarter", text, flags=re.IGNORECASE)
    if end_of_quarter:
        ordinal = end_of_quarter.group(1)
        return f"End {ordinal}"

    if "Quarter" in text:
        text = text.replace("Quarter", "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def format_game_status(status: EventStatus | None) -> GameStatusView:
    if status is None:
        return GameStatusView(label="TBD", state="pre", time_pct=0.0, minutes_remaining=60.0)

    minutes_remaining = calculate_minutes_remaining(status)

    if status.state == "pre":
        if status.start_time:
            formatted = status.start_time.strftime("%a %I:%M %p")
            if len(formatted) > 4 and formatted[4] == "0":
                formatted = formatted[:4] + formatted[5:]
            label = formatted
        else:
            label = "TBD"
        return GameStatusView(
            label=label,
            state="pre",
            time_pct=0.0,
            minutes_remaining=minutes_remaining,
        )

    if status.state == "post":
        return GameStatusView(label="FINAL", state="post", time_pct=100.0, minutes_remaining=0.0)

    detail = status.short_detail or status.detail or "Live"
    label = tidy_status_label(detail)
    time_played_pct = min(100.0, max(0.0, 100.0 - (minutes_remaining / 60.0 * 100.0)))
    return GameStatusView(
        label=label,
        state="in",
        time_pct=time_played_pct,
        minutes_remaining=minutes_remaining,
    )


def performance_percentage(actual: float, baseline: float) -> float:
    if baseline <= 0.0:
        return 100.0 if actual > 0.0 else 0.0
    return (actual / baseline) * 100.0


def resolve_pace_indicator(state: str, perf_pct: float, time_pct: float) -> str:
    if state == "post":
        return "✅ Over Projection" if perf_pct >= 100.0 else "❌ Under Projection"
    if state == "pre":
        return "(Yet to Start)"
    if perf_pct >= time_pct + 10.0:
        return "▲ Exceeding Pace"
    if perf_pct <= time_pct - 10.0:
        return "▼ Behind Pace"
    return "~ On Pace"


def progress_bar(value: float) -> str:
    capped = max(0.0, min(100.0, value))
    filled = int(capped // 10)
    if filled > 10:
        filled = 10
    return "[" + "█" * filled + "░" * (10 - filled) + "]"


def format_percentage(value: float) -> str:
    return f"{value:.1f}%"


def format_points(value: float, decimals: int = 2) -> str:
    fmt = f"{{:.{decimals}f}}"
    return fmt.format(value)


def short_player_name(full_name: str) -> str:
    parts = full_name.strip().split()
    if not parts:
        return full_name
    first = parts[0]
    last = parts[-1]
    if last in PLAYER_SUFFIXES and len(parts) >= 2:
        last = parts[-2]
    initial = next((char for char in first if char.isalpha()), first[:1])
    if not initial:
        initial = first[:1]
    return f"{initial.upper()}. {last}"


def format_player_cell(card: PlayerCard) -> str:
    if card.position == "D/ST":
        team_name = card.name.replace("D/ST", "").replace("Dst", "").strip()
        team_name = team_name.rstrip(",")
        if not team_name:
            team_name = card.name
        return f"{team_name}, {card.nfl_team} {card.position}"
    return f"{short_player_name(card.name)}, {card.nfl_team} {card.position}"


def render_markdown_table(
    headers: List[str],
    rows: List[List[str]],
    aligns: List[str],
) -> List[str]:
    widths: List[int] = []
    for idx, header in enumerate(headers):
        width = len(header)
        for row in rows:
            width = max(width, len(row[idx]))
        widths.append(width)

    header_line = "| " + " | ".join(
        _pad_cell(headers[idx], widths[idx], "left") for idx in range(len(headers))
    ) + " |"

    align_line = "| " + " | ".join(
        _alignment_cell(widths[idx], aligns[idx]) for idx in range(len(headers))
    ) + " |"

    data_lines = []
    for row in rows:
        data_lines.append(
            "| "
            + " | ".join(
                _pad_cell(row[idx], widths[idx], aligns[idx])
                for idx in range(len(headers))
            )
            + " |"
        )

    return [header_line, align_line, *data_lines]


def _pad_cell(value: str, width: int, align: str) -> str:
    if align == "right":
        return value.rjust(width)
    if align == "center":
        return value.center(width)
    return value.ljust(width)


def _alignment_cell(width: int, align: str) -> str:
    width = max(width, 3)
    if align == "center":
        return ":" + "-" * (width - 2) + ":"
    if align == "right":
        return "-" * (width - 1) + ":"
    return ":" + "-" * (width - 1)


def render_summary_table(teams: List[TeamReport]) -> List[str]:
    headers = [
        "Team",
        "Actual",
        "Live Proj",
        "Baseline",
        "Change",
        "Mins Used",
        "Score Pace",
    ]
    rows = []
    for team in teams:
        rows.append(
            [
                team.name,
                format_points(team.actual_points, 2),
                format_points(team.live_projection, 1),
                format_points(team.baseline_projection, 2),
                format_projection_delta(team.projection_delta),
                f"{progress_bar(team.minutes_used_pct)} {format_percentage(team.minutes_used_pct)}",
                f"{progress_bar(team.score_pace_pct)} {format_percentage(team.score_pace_pct)}",
            ]
        )

    aligns = ["left", "right", "right", "right", "right", "left", "left"]
    return render_markdown_table(headers, rows, aligns)


def render_player_table(players: List[PlayerCard]) -> List[str]:
    headers = [
        "Slot",
        "Player",
        "Status",
        "FPTS / Proj",
        "Time Played",
        "Performance",
        "Pace/Result",
    ]
    rows: List[List[str]] = []
    for card in players:
        player_cell = format_player_cell(card)
        fpts_proj = f"{format_points(card.actual, 2)} / {format_points(card.baseline, 1)}"
        time_played = f"{progress_bar(card.time_played_pct)} {format_percentage(card.time_played_pct)}"
        performance = f"{progress_bar(card.performance_pct)} {format_percentage(card.performance_pct)}"
        rows.append(
            [
                card.slot_label,
                player_cell,
                card.game_status,
                fpts_proj,
                time_played,
                performance,
                card.pace_indicator,
            ]
        )

    aligns = ["center", "left", "left", "right", "left", "left", "left"]
    return render_markdown_table(headers, rows, aligns)


def serialize_player_card(card: PlayerCard) -> dict[str, Any]:
    return {
        "slot": card.slot_label,
        "name": card.name,
        "nfl_team": card.nfl_team,
        "position": card.position,
        "baseline": card.baseline,
        "actual": card.actual,
        "performance_pct": card.performance_pct,
        "time_played_pct": card.time_played_pct,
        "minutes_remaining": card.minutes_remaining,
        "game_status": card.game_status,
        "pace_indicator": card.pace_indicator,
        "game_state": card.game_state,
    }


def serialize_team_report(team: TeamReport) -> dict[str, Any]:
    return {
        "name": team.name,
        "actual_points": team.actual_points,
        "live_projection": team.live_projection,
        "baseline_projection": team.baseline_projection,
        "projection_delta": team.projection_delta,
        "minutes_remaining": team.minutes_remaining,
        "minutes_used": team.minutes_used,
        "minutes_used_pct": team.minutes_used_pct,
        "score_pace_pct": team.score_pace_pct,
        "players": [serialize_player_card(card) for card in team.players],
    }


def render_team_section(report: TeamReport) -> List[str]:
    lines: List[str] = ["---", f"### {report.name} - Live Player Cards", ""]
    lines.extend(render_player_table(report.players))
    return lines


def ensure_matchup(
    schedule: Iterable[dict[str, Any]],
    scoring_period: int,
    matchup_id: int | None,
    team_id: int | None,
) -> dict[str, Any]:
    candidates = [m for m in schedule if m.get("matchupPeriodId") == scoring_period]
    if not candidates:
        raise LiveScoringError(f"No matchups found for scoring period {scoring_period}")

    if matchup_id is not None:
        for candidate in candidates:
            if candidate.get("id") == matchup_id:
                return candidate
        raise LiveScoringError(f"Matchup {matchup_id} not found in scoring period {scoring_period}")

    if team_id is not None:
        for candidate in candidates:
            home = candidate.get("home") or {}
            away = candidate.get("away") or {}
            if home.get("teamId") == team_id or away.get("teamId") == team_id:
                return candidate
        raise LiveScoringError(f"Team {team_id} not scheduled in scoring period {scoring_period}")

    return candidates[0]


def format_projection_delta(delta: float) -> str:
    threshold = 0.05
    if delta > threshold:
        return f"↑ {delta:.2f}"
    if delta < -threshold:
        return f"↓ {abs(delta):.2f}"
    return f"→ {abs(delta):.2f}"


def build_team_report(
    side: dict[str, Any],
    team_lookup: Dict[int, dict[str, Any]],
    scoring_period: int,
    pro_abbrev: Dict[int, str],
    pro_games: Dict[tuple[int, int], dict[str, Any]],
    status_fetcher: EventStatusFetcher,
) -> TeamReport:
    team_id = side.get("teamId")
    team_info = team_lookup.get(team_id or -1, {})
    team_name = team_info.get("name") or f"Team {team_id}"

    roster = side.get("rosterForCurrentScoringPeriod") or {}
    entries = roster.get("entries") or []

    slot_buckets: Dict[int, List[dict[str, Any]]] = {}
    for entry in entries:
        slot = entry.get("lineupSlotId")
        if slot is None:
            continue
        slot_buckets.setdefault(int(slot), []).append(entry)

    players: List[PlayerCard] = []
    for slot_id in STARTER_SLOT_ORDER:
        bucket = slot_buckets.get(slot_id)
        if not bucket:
            continue
        entry = bucket.pop(0)
        players.append(
            build_player_card(
                entry=entry,
                slot_id=slot_id,
                scoring_period=scoring_period,
                pro_abbrev=pro_abbrev,
                pro_games=pro_games,
                status_fetcher=status_fetcher,
            )
        )

    actual_points = float(roster.get("appliedStatTotal") or 0.0)
    live_projection = float(side.get("totalProjectedPointsLive") or 0.0)
    baseline_projection = sum(player.baseline for player in players)
    minutes_remaining = sum(player.minutes_remaining for player in players)

    return TeamReport(
        name=team_name,
        actual_points=actual_points,
        live_projection=live_projection,
        baseline_projection=baseline_projection,
        minutes_remaining=minutes_remaining,
        players=players,
    )


def build_player_card(
    entry: dict[str, Any],
    slot_id: int,
    scoring_period: int,
    pro_abbrev: Dict[int, str],
    pro_games: Dict[tuple[int, int], dict[str, Any]],
    status_fetcher: EventStatusFetcher,
) -> PlayerCard:
    pool_entry = entry.get("playerPoolEntry") or {}
    player = pool_entry.get("player") or {}

    name = player.get("fullName") or (
        f"{player.get('firstName', 'Unknown')} {player.get('lastName', '').strip()}"
    ).strip()
    pro_team_id = player.get("proTeamId")
    nfl_team = (
        pro_abbrev.get(int(pro_team_id), str(pro_team_id))
        if pro_team_id is not None
        else "FA"
    )

    default_position = player.get("defaultPositionId")
    position = POSITION_LABELS.get(int(default_position), SLOT_LABELS.get(slot_id, ""))

    baseline = extract_projection(player, scoring_period)
    actual = extract_actual(player, scoring_period)
    perf_pct = performance_percentage(actual, baseline)

    event_id = resolve_event_id(player, scoring_period, pro_games)
    status = status_fetcher.get(event_id)
    status_view = format_game_status(status)
    pace_indicator = resolve_pace_indicator(status_view.state, perf_pct, status_view.time_pct)

    return PlayerCard(
        slot_label=SLOT_LABELS.get(slot_id, str(slot_id)),
        name=name,
        nfl_team=nfl_team,
        position=position,
        baseline=baseline,
        actual=actual,
        performance_pct=perf_pct,
        time_played_pct=status_view.time_pct,
        minutes_remaining=status_view.minutes_remaining,
        game_status=status_view.label,
        pace_indicator=pace_indicator,
        game_state=status_view.state,
    )


def _build_matchup_report(
    matchup: dict[str, Any],
    period: int,
    team_lookup: dict[int, dict[str, Any]],
    pro_abbrev: Dict[int, str],
    pro_games: Dict[tuple[int, int], dict[str, Any]],
    status_fetcher: EventStatusFetcher,
) -> tuple[dict[str, Any], TeamReport, TeamReport]:
    home_side = matchup.get("home") or {}
    away_side = matchup.get("away") or {}

    home_report = build_team_report(
        side=home_side,
        team_lookup=team_lookup,
        scoring_period=period,
        pro_abbrev=pro_abbrev,
        pro_games=pro_games,
        status_fetcher=status_fetcher,
    )
    away_report = build_team_report(
        side=away_side,
        team_lookup=team_lookup,
        scoring_period=period,
        pro_abbrev=pro_abbrev,
        pro_games=pro_games,
        status_fetcher=status_fetcher,
    )

    matchup_meta = {
        "matchup_id": matchup.get("id"),
        "scoring_period": period,
        "home_team_id": home_side.get("teamId"),
        "away_team_id": away_side.get("teamId"),
        "home_total_points": float(home_side.get("totalPoints", 0.0) or 0.0),
        "away_total_points": float(away_side.get("totalPoints", 0.0) or 0.0),
        "home_total_live": float(home_side.get("totalPointsLive", 0.0) or 0.0),
        "away_total_live": float(away_side.get("totalPointsLive", 0.0) or 0.0),
        "winner": (matchup.get("winner") or "UNDECIDED").upper(),
        "home_team_name": home_report.name,
        "away_team_name": away_report.name,
    }

    return matchup_meta, away_report, home_report


def fetch_all_matchup_reports(
    *,
    league_id: int,
    season: int,
    scoring_period: int | None = None,
    timeout: float = 10.0,
    espn_s2: str | None = None,
    swid: str | None = None,
) -> tuple[int, list[tuple[dict[str, Any], TeamReport, TeamReport]]]:
    """Return matchup reports for every matchup in the scoring period."""

    client = LiveScoreClient(
        league_id=league_id,
        season=season,
        timeout=timeout,
        espn_s2=espn_s2,
        swid=swid,
    )

    period = scoring_period or client.get_current_scoring_period()
    data = client.fetch_scoreboard(
        period,
        include_boxscore=True,
        include_live=True,
    )

    schedule = [
        matchup
        for matchup in (data.get("schedule") or [])
        if matchup.get("matchupPeriodId") == period
    ]

    teams_payload = data.get("teams") or []
    team_lookup = {
        team.get("id"): team for team in teams_payload if team.get("id") is not None
    }

    pro_data = fetch_pro_team_data(season, timeout)
    pro_abbrev, pro_games = build_pro_lookups(pro_data)
    status_fetcher = EventStatusFetcher(timeout)

    matchup_reports = [
        _build_matchup_report(
            matchup,
            period,
            team_lookup,
            pro_abbrev,
            pro_games,
            status_fetcher,
        )
        for matchup in schedule
    ]

    return period, matchup_reports


def fetch_matchup_reports(
    *,
    league_id: int,
    season: int,
    scoring_period: int | None = None,
    team_id: int | None = None,
    matchup_id: int | None = None,
    timeout: float = 10.0,
    espn_s2: str | None = None,
    swid: str | None = None,
) -> tuple[int, dict[str, Any], TeamReport, TeamReport]:
    """Return the scoring period, matchup metadata, and team reports."""

    period, matchup_reports = fetch_all_matchup_reports(
        league_id=league_id,
        season=season,
        scoring_period=scoring_period,
        timeout=timeout,
        espn_s2=espn_s2,
        swid=swid,
    )

    if not matchup_reports:
        raise LiveScoringError(f"No matchups found for scoring period {period}")

    if matchup_id is not None:
        for meta, away, home in matchup_reports:
            if meta.get("matchup_id") == matchup_id:
                return period, meta, away, home
        raise LiveScoringError(
            f"Matchup {matchup_id} not found in scoring period {period}"
        )

    if team_id is not None:
        for meta, away, home in matchup_reports:
            if meta.get("home_team_id") == team_id or meta.get("away_team_id") == team_id:
                return period, meta, away, home
        raise LiveScoringError(
            f"Team {team_id} not scheduled in scoring period {period}"
        )

    meta, away, home = matchup_reports[0]
    return period, meta, away, home


def generate_live_matchup_report(
    *,
    league_id: int,
    season: int,
    scoring_period: int | None = None,
    team_id: int | None = None,
    matchup_id: int | None = None,
    timeout: float = 10.0,
    espn_s2: str | None = None,
    swid: str | None = None,
    all_matchups: bool = False,
) -> str:
    """Build a live matchup report as a formatted text block."""

    if all_matchups:
        period, matchup_reports = fetch_all_matchup_reports(
            league_id=league_id,
            season=season,
            scoring_period=scoring_period,
            timeout=timeout,
            espn_s2=espn_s2,
            swid=swid,
        )

        if not matchup_reports:
            return "```\nNo matchups found.\n```"

        lines: List[str] = [f"### Live Matchup Report - Week {period}", ""]
        for meta, away_report, home_report in matchup_reports:
            header = f"#### {away_report.name} @ {home_report.name} (Matchup {meta.get('matchup_id', '-')})"
            lines.append(header)
            lines.extend(render_summary_table([away_report, home_report]))
            lines.append("")
            for report in (away_report, home_report):
                lines.extend(render_team_section(report))
                lines.append("")
        if lines and lines[-1] == "":
            lines.pop()
        content = "\n".join(lines)
        return f"```\n{content}\n```"

    period, _meta, away_report, home_report = fetch_matchup_reports(
        league_id=league_id,
        season=season,
        scoring_period=scoring_period,
        team_id=team_id,
        matchup_id=matchup_id,
        timeout=timeout,
        espn_s2=espn_s2,
        swid=swid,
    )

    lines: List[str] = ["### Live Matchup Report", ""]
    lines.extend(render_summary_table([away_report, home_report]))
    lines.append("")
    for report in (away_report, home_report):
        lines.extend(render_team_section(report))
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()

    content = "\n".join(lines)
    return f"```\n{content}\n```"
