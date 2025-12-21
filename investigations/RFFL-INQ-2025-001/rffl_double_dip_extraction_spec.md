# Double-Dip Detection: Refined Extraction Logic Spec

> **Purpose:** Specification for detecting return TD "double-dip" events where the same RFFL owner benefits from both individual player points AND D/ST points on a single play
> **For:** Cursor implementation of `ESPNAPITool.get_scoring_plays()` and related forensic tooling
> **Case Reference:** RFFL-INQ-2025-001
> **Attribution Method:** Full Attribution (Option A) — Explicit stat ID matching for both player AND D/ST

---

## Problem Statement

When a player scores a kick/punt return TD:
1. The **individual player** receives 6 fantasy points (Return TD)
2. The **D/ST unit** for that player's NFL team receives 6 fantasy points (Defensive/ST TD)

A "double-dip" occurs when the **same RFFL owner** has both the player AND the corresponding D/ST unit in their starting lineup for that week.

**Goal:** Detect all historical double-dip events in RFFL (2011-2025) to answer whether this mechanic is exploitable.

---

## Stat ID Discovery Requirements

### Individual Player Stats (Offensive/Return)

| Stat Category | Stat ID | Points | Notes |
|---------------|---------|--------|-------|
| Kick Return TD | `[TBD]` | 6 | Player returned kickoff for TD |
| Punt Return TD | `[TBD]` | 6 | Player returned punt for TD |

### D/ST Stats (Special Teams TDs)

| Stat Category | Stat ID | Points | Notes |
|---------------|---------|--------|-------|
| D/ST Kick Return TD | `[TBD]` | 6 | Team's kick returner scored |
| D/ST Punt Return TD | `[TBD]` | 6 | Team's punt returner scored |
| D/ST Pick-Six | `[TBD]` | 6 | Interception returned for TD |
| D/ST Fumble Return TD | `[TBD]` | 6 | Fumble recovered and returned for TD |
| D/ST Blocked Kick TD | `[TBD]` | 6 | Blocked punt/FG returned for TD |

### Discovery Priority

**Phase 1 (Required for Investigation):**
1. Player Kick Return TD
2. Player Punt Return TD  
3. D/ST Kick Return TD
4. D/ST Punt Return TD

**Phase 2 (Complete D/ST Taxonomy):**
5. D/ST Pick-Six
6. D/ST Fumble Return TD
7. D/ST Blocked Kick TD

### Discovery Script Output

```python
# Target output: src/rffl/forensic/stat_ids.py

class PlayerStatID:
    """Individual player stat IDs."""
    KICK_RETURN_TD: int = None  # TBD - discover from API
    PUNT_RETURN_TD: int = None  # TBD - discover from API

class DSTStatID:
    """D/ST unit stat IDs."""
    KICK_RETURN_TD: int = None  # TBD - may be same as player or different
    PUNT_RETURN_TD: int = None  # TBD
    PICK_SIX: int = None        # TBD
    FUMBLE_RETURN_TD: int = None # TBD
    BLOCKED_KICK_TD: int = None  # TBD
```

---

## Data Model

### Core Entities

```
ReturnTDEvent
├── season: int (2011-2025)
├── week: int (1-17)
├── nfl_player_id: int (ESPN player ID)
├── nfl_player_name: str
├── nfl_team: str (3-letter NFL team code, e.g., "SEA")
├── return_type: enum ("kick" | "punt")
├── points_awarded: float (should be 6.0)
└── stat_id: int (ESPN stat ID for the return TD)

DSTScoringEvent
├── season: int
├── week: int
├── nfl_team: str (3-letter NFL team code)
├── total_points: float (total D/ST fantasy points)
├── td_breakdown: DSTTDBreakdown (detailed TD attribution)
└── applied_stats: dict[int, float] (raw stat ID → value mapping)

DSTTDBreakdown
├── kick_return_tds: int (count from D/ST Kick Return TD stat)
├── punt_return_tds: int (count from D/ST Punt Return TD stat)
├── pick_sixes: int (count from Pick-Six stat)
├── fumble_return_tds: int (count from Fumble Return TD stat)
├── blocked_kick_tds: int (count from Blocked Kick TD stat)
└── total_tds: int (sum of all above)

RFFLLineupSlot
├── season: int
├── week: int
├── rffl_team_code: str (e.g., "GFM", "PCX")
├── slot_position: str (e.g., "QB", "RB", "WR", "FLEX", "D/ST")
├── nfl_player_id: int (or nfl_team for D/ST)
├── nfl_player_name: str
├── nfl_team: str
├── points_scored: float
├── is_starter: bool
└── applied_stats: dict[int, float] (raw stat breakdown for forensic analysis)

DoubleDipEvent
├── season: int
├── week: int
├── rffl_team_code: str
├── player_name: str
├── player_slot: str (lineup position of the player)
├── player_points: float (6.0 for return TD)
├── player_stat_id: int (which stat ID triggered the player points)
├── nfl_team: str
├── dst_slot: str (should be "D/ST")
├── dst_total_points: float (total D/ST points that week)
├── dst_return_td_points: float (specifically the 6 pts from matching return TD)
├── dst_stat_id: int (which D/ST stat ID confirms the return TD)
├── total_benefit: float (player_points + dst_return_td_points = 12.0)
├── return_type: enum ("kick" | "punt")
└── attribution_method: str ("explicit_stat_match")
```

---

## Detection Algorithm

### Step 1: Extract All Return TD Events (Season-Wide)

```python
def extract_return_td_events(season: int) -> list[ReturnTDEvent]:
    """
    Scan all weeks of a season for individual player return TDs.
    
    Process:
    1. For each week in season (1-17 for modern era, 1-16 for pre-2021)
    2. Get all boxscores for that week
    3. For each player in each lineup (home + away)
    4. Check player.appliedStats for return TD stat IDs
    5. If found, create ReturnTDEvent record
    
    Returns:
        List of all return TD events for the season
    """
    events = []
    
    for week in get_season_weeks(season):
        boxscores = client.get_boxscores(week)
        
        for matchup in boxscores:
            for lineup in [matchup.home_lineup, matchup.away_lineup]:
                for player in lineup:
                    # Check for return TD stats
                    kick_return_td = get_stat_value(player, KICK_RETURN_TD_STAT_ID)
                    punt_return_td = get_stat_value(player, PUNT_RETURN_TD_STAT_ID)
                    
                    if kick_return_td > 0:
                        events.append(ReturnTDEvent(
                            season=season,
                            week=week,
                            nfl_player_id=player.playerId,
                            nfl_player_name=player.name,
                            nfl_team=player.proTeam,  # NFL team abbreviation
                            return_type="kick",
                            points_awarded=kick_return_td * 6,  # or raw points
                            stat_id=KICK_RETURN_TD_STAT_ID
                        ))
                    
                    if punt_return_td > 0:
                        events.append(ReturnTDEvent(
                            season=season,
                            week=week,
                            nfl_player_id=player.playerId,
                            nfl_player_name=player.name,
                            nfl_team=player.proTeam,
                            return_type="punt",
                            points_awarded=punt_return_td * 6,
                            stat_id=PUNT_RETURN_TD_STAT_ID
                        ))
    
    return events
```

### Step 2: Build RFFL Lineup Index (Season-Wide)

```python
def build_lineup_index(season: int) -> dict[tuple[int, str], list[RFFLLineupSlot]]:
    """
    Create indexed lookup of all RFFL lineups by (week, rffl_team_code).
    
    Returns:
        Dictionary mapping (week, team_code) to list of lineup slots
    """
    index = {}
    
    for week in get_season_weeks(season):
        boxscores = client.get_boxscores(week)
        
        for matchup in boxscores:
            # Process home team
            home_code = resolve_rffl_team_code(matchup.home_team, season)
            index[(week, home_code)] = extract_lineup_slots(
                matchup.home_lineup, week, season, home_code
            )
            
            # Process away team
            away_code = resolve_rffl_team_code(matchup.away_team, season)
            index[(week, away_code)] = extract_lineup_slots(
                matchup.away_lineup, week, season, away_code
            )
    
    return index

def extract_lineup_slots(lineup, week, season, rffl_team_code) -> list[RFFLLineupSlot]:
    """Extract structured lineup slot data from raw lineup."""
    slots = []
    
    for player in lineup:
        slots.append(RFFLLineupSlot(
            season=season,
            week=week,
            rffl_team_code=rffl_team_code,
            slot_position=player.slot_position,  # "QB", "RB", "D/ST", etc.
            nfl_player_id=player.playerId,
            nfl_player_name=player.name,
            nfl_team=player.proTeam,
            points_scored=player.points,
            is_starter=player.slot_position != "BE"  # Not on bench
        ))
    
    return slots
```

### Step 3: Detect Double-Dip Events (Full Attribution)

```python
def detect_double_dips(
    return_events: list[ReturnTDEvent],
    lineup_index: dict[tuple[int, str], list[RFFLLineupSlot]]
) -> list[DoubleDipEvent]:
    """
    Cross-reference return TD events with RFFL lineups to find double-dips.
    
    FULL ATTRIBUTION METHOD (Option A):
    For each return TD event:
    1. Find which RFFL team had this player in their STARTING lineup
    2. Check if that same RFFL team also had the corresponding D/ST STARTING
    3. EXPLICITLY VERIFY: D/ST's appliedStats contains matching return TD stat
    4. If all conditions met → Double-Dip confirmed with explicit attribution
    
    Returns:
        List of all double-dip events with full stat attribution
    """
    double_dips = []
    
    for event in return_events:
        # Find RFFL team that started this player
        player_owner = find_player_owner(
            event.nfl_player_id,
            event.week,
            lineup_index,
            require_starter=True
        )
        
        if player_owner is None:
            # Player scored return TD but wasn't in any RFFL starting lineup
            continue
        
        rffl_team_code, player_slot = player_owner
        
        # Check if same RFFL team also started the corresponding D/ST
        dst_slot = find_dst_in_lineup(
            event.nfl_team,  # NFL team whose D/ST we're looking for
            event.week,
            rffl_team_code,
            lineup_index,
            require_starter=True
        )
        
        if dst_slot is None:
            # Owner had the player but not the D/ST (or D/ST was benched)
            continue
        
        # FULL ATTRIBUTION: Verify D/ST stat breakdown confirms the return TD
        dst_confirmation = verify_dst_return_td(
            dst_slot=dst_slot,
            return_type=event.return_type
        )
        
        if dst_confirmation is None:
            # D/ST stats don't show a matching return TD - log anomaly
            logger.warning(
                f"Player {event.nfl_player_name} has {event.return_type} return TD "
                f"but D/ST {event.nfl_team} lacks matching stat. Week {event.week}, {event.season}"
            )
            continue
        
        # DOUBLE-DIP CONFIRMED WITH FULL ATTRIBUTION
        double_dips.append(DoubleDipEvent(
            season=event.season,
            week=event.week,
            rffl_team_code=rffl_team_code,
            player_name=event.nfl_player_name,
            player_slot=player_slot.slot_position,
            player_points=event.points_awarded,
            player_stat_id=event.stat_id,
            nfl_team=event.nfl_team,
            dst_slot="D/ST",
            dst_total_points=dst_slot.points_scored,
            dst_return_td_points=6.0,  # Confirmed via stat match
            dst_stat_id=dst_confirmation['stat_id'],
            total_benefit=event.points_awarded + 6.0,
            return_type=event.return_type,
            attribution_method="explicit_stat_match"
        ))
    
    return double_dips


def verify_dst_return_td(dst_slot: RFFLLineupSlot, return_type: str) -> dict | None:
    """
    Verify D/ST has a matching return TD in their stat breakdown.
    
    Args:
        dst_slot: The D/ST lineup slot with applied_stats
        return_type: "kick" or "punt"
    
    Returns:
        Dict with stat_id and count if found, None if not found
    """
    from rffl.forensic.stat_ids import DSTStatID
    
    if return_type == "kick":
        target_stat_id = DSTStatID.KICK_RETURN_TD
    elif return_type == "punt":
        target_stat_id = DSTStatID.PUNT_RETURN_TD
    else:
        raise ValueError(f"Unknown return type: {return_type}")
    
    # Check D/ST's applied_stats for the matching stat
    applied_stats = dst_slot.applied_stats or {}
    
    stat_value = applied_stats.get(target_stat_id, 0)
    
    if stat_value > 0:
        return {
            "stat_id": target_stat_id,
            "count": int(stat_value),
            "points": stat_value * 6  # Each return TD = 6 pts
        }
    
    return None


def extract_dst_td_breakdown(dst_slot: RFFLLineupSlot) -> DSTTDBreakdown:
    """
    Parse D/ST applied_stats into structured TD breakdown.
    
    Useful for forensic analysis and debugging.
    """
    from rffl.forensic.stat_ids import DSTStatID
    
    stats = dst_slot.applied_stats or {}
    
    return DSTTDBreakdown(
        kick_return_tds=int(stats.get(DSTStatID.KICK_RETURN_TD, 0)),
        punt_return_tds=int(stats.get(DSTStatID.PUNT_RETURN_TD, 0)),
        pick_sixes=int(stats.get(DSTStatID.PICK_SIX, 0)),
        fumble_return_tds=int(stats.get(DSTStatID.FUMBLE_RETURN_TD, 0)),
        blocked_kick_tds=int(stats.get(DSTStatID.BLOCKED_KICK_TD, 0)),
        total_tds=sum([
            int(stats.get(DSTStatID.KICK_RETURN_TD, 0)),
            int(stats.get(DSTStatID.PUNT_RETURN_TD, 0)),
            int(stats.get(DSTStatID.PICK_SIX, 0)),
            int(stats.get(DSTStatID.FUMBLE_RETURN_TD, 0)),
            int(stats.get(DSTStatID.BLOCKED_KICK_TD, 0)),
        ])
    )
```

def find_player_owner(
    nfl_player_id: int,
    week: int,
    lineup_index: dict,
    require_starter: bool = True
) -> tuple[str, RFFLLineupSlot] | None:
    """Find which RFFL team owns a player in a given week."""
    
    for (w, team_code), slots in lineup_index.items():
        if w != week:
            continue
        
        for slot in slots:
            if slot.nfl_player_id == nfl_player_id:
                if require_starter and not slot.is_starter:
                    continue
                return (team_code, slot)
    
    return None

def find_dst_in_lineup(
    nfl_team: str,
    week: int,
    rffl_team_code: str,
    lineup_index: dict,
    require_starter: bool = True
) -> RFFLLineupSlot | None:
    """Find if an RFFL team has a specific NFL D/ST in their lineup."""
    
    slots = lineup_index.get((week, rffl_team_code), [])
    
    for slot in slots:
        if slot.slot_position == "D/ST" and slot.nfl_team == nfl_team:
            if require_starter and not slot.is_starter:
                continue
            return slot
    
    return None
```

---

## Edge Cases

### Edge Case 1: Multiple Return TDs Same Game

**Scenario:** Player scores 2 kick return TDs in one game.

**Handling:** Each return TD is a separate event. D/ST's `kick_return_tds` stat should show value of 2. If owner has both player + D/ST, they get 24 points (12 × 2). Count as 2 double-dip events.

**Full Attribution Check:** Player stat shows 2 TDs, D/ST stat shows 2 TDs. Values must match.

### Edge Case 2: D/ST Has Multiple TD Types

**Scenario:** D/ST scores a pick-six AND a return TD in same game.

**Handling:** Full attribution separates these cleanly:
- `pick_sixes = 1` (6 pts)
- `kick_return_tds = 1` (6 pts)

Only the return TD triggers double-dip detection. Pick-six is irrelevant.

### Edge Case 3: Player on Bench

**Scenario:** Owner has both player and D/ST but player is on bench.

**Handling:** Not a double-dip. The player must be in a STARTING slot (not "BE") to count. Bench players score points but don't contribute to matchup score.

### Edge Case 4: D/ST on Bench

**Scenario:** Owner starts the player but has the D/ST benched.

**Handling:** Not a double-dip. Same logic—D/ST must be in the starting "D/ST" slot.

### Edge Case 5: Different NFL Teams

**Scenario:** Owner has Rashid Shaheed (SEA) and Dallas Cowboys D/ST.

**Handling:** Not a double-dip. The D/ST must match the player's NFL team. `event.nfl_team == dst_slot.nfl_team` must be true.

### Edge Case 6: Traded Player Mid-Season

**Scenario:** Shaheed traded from NO to SEA mid-season. Return TD comes after trade.

**Handling:** Use the player's `proTeam` at time of the game (from boxscore), not draft-time team. ESPN API should reflect current NFL team at game time.

### Edge Case 7: Historical Data Gaps

**Scenario:** Pre-2019 boxscores may lack stat-level detail.

**Handling:** 
- If `appliedStats` not available, mark season/week as `[DATA UNAVAILABLE]`
- Log which seasons have complete vs incomplete data
- Report findings with data coverage disclaimer

### Edge Case 8: Stat Mismatch Anomaly (NEW - Full Attribution)

**Scenario:** Player shows kick return TD in their stats, but D/ST's `kick_return_tds` stat is 0.

**Handling:** 
- Log as anomaly for investigation
- Do NOT count as double-dip (can't confirm with full attribution)
- Include in report's "data quality" section
- Possible causes: ESPN data error, stat correction pending, API inconsistency

### Edge Case 9: Punt vs Kick Mismatch (NEW - Full Attribution)

**Scenario:** Player has `punt_return_td = 1`, but D/ST only has `kick_return_tds = 1`.

**Handling:**
- Type must match exactly (punt ↔ punt, kick ↔ kick)
- If mismatch, log anomaly and skip
- This would indicate ESPN data inconsistency

---

## RFFL Team Code Resolution

The lineup data uses ESPN's internal team representation. We need to map to RFFL team codes.

```python
def resolve_rffl_team_code(espn_team, season: int) -> str:
    """
    Map ESPN team object to RFFL team code.
    
    Options:
    1. ESPN team.team_name → fuzzy match to RFFL registry
    2. ESPN team.team_id → maintain ESPN-to-RFFL mapping table
    3. ESPN team.owners → match owner names to registry
    
    Returns:
        RFFL team code (e.g., "GFM", "PCX")
    """
    # Import from canonical registry
    from RFFL_REG_TEAMS_001 import get_teams_by_season
    
    season_teams = get_teams_by_season(season)
    
    # Strategy 1: Match by team name
    for team in season_teams:
        if fuzzy_match(espn_team.team_name, team.team_full_name):
            return team.team_code
    
    # Strategy 2: Match by owner name (if available)
    if hasattr(espn_team, 'owners'):
        for owner in espn_team.owners:
            for team in season_teams:
                if owner_name_match(owner, team.owner_code_1, team.owner_code_2):
                    return team.team_code
    
    # Fallback: Log warning and return ESPN team name
    logger.warning(f"Could not resolve RFFL team code for {espn_team.team_name}")
    return espn_team.team_name
```

---

## Output Format

### Investigation Report DataFrame

```python
def generate_investigation_report(double_dips: list[DoubleDipEvent]) -> pd.DataFrame:
    """Generate analysis-ready DataFrame."""
    
    df = pd.DataFrame([
        {
            "Season": dd.season,
            "Week": dd.week,
            "RFFL Team": dd.rffl_team_code,
            "Player": dd.player_name,
            "Player Slot": dd.player_slot,
            "Player Points": dd.player_points,
            "NFL Team": dd.nfl_team,
            "D/ST Points": dd.dst_points,
            "Return Type": dd.return_type,
            "Double-Dip Benefit": dd.total_benefit,
        }
        for dd in double_dips
    ])
    
    return df
```

### Summary Statistics

```python
def generate_summary(double_dips: list[DoubleDipEvent], total_seasons: int) -> dict:
    """Generate summary statistics for case study."""
    
    return {
        "total_double_dips": len(double_dips),
        "seasons_analyzed": total_seasons,
        "seasons_with_double_dips": len(set(dd.season for dd in double_dips)),
        "teams_benefited": list(set(dd.rffl_team_code for dd in double_dips)),
        "total_bonus_points": sum(dd.total_benefit for dd in double_dips),
        "avg_per_season": len(double_dips) / total_seasons if total_seasons > 0 else 0,
        "by_return_type": {
            "kick": len([dd for dd in double_dips if dd.return_type == "kick"]),
            "punt": len([dd for dd in double_dips if dd.return_type == "punt"]),
        },
    }
```

---

## Validation Checkpoints

### Checkpoint 1: Stat ID Verification (Player)

Before running full analysis:
- [ ] Confirm KICK_RETURN_TD_STAT_ID is correct (PlayerStatID)
- [ ] Confirm PUNT_RETURN_TD_STAT_ID is correct (PlayerStatID)
- [ ] Test with known event (Shaheed Week 16, 2025)

### Checkpoint 2: Stat ID Verification (D/ST)

Before running full analysis:
- [ ] Confirm D/ST KICK_RETURN_TD_STAT_ID is correct
- [ ] Confirm D/ST PUNT_RETURN_TD_STAT_ID is correct
- [ ] Confirm D/ST PICK_SIX_STAT_ID is correct
- [ ] Confirm D/ST FUMBLE_RETURN_TD_STAT_ID is correct
- [ ] Confirm D/ST BLOCKED_KICK_TD_STAT_ID is correct
- [ ] Test D/ST stat breakdown parsing with known multi-TD game

### Checkpoint 3: Single Week Test

Test extraction with Week 16, 2025 (Shaheed event):
- [ ] Player return TD event extracted correctly
- [ ] NFL team code populated ("SEA")
- [ ] Points match expected (6.0)
- [ ] Player stat ID captured

### Checkpoint 4: D/ST Stat Breakdown Test

Test D/ST parsing with Shaheed event:
- [ ] Seattle D/ST `applied_stats` accessible
- [ ] `kick_return_tds` shows value ≥ 1
- [ ] Other TD types correctly parsed
- [ ] `extract_dst_td_breakdown()` returns valid object

### Checkpoint 5: Lineup Index Test

Test lineup building:
- [ ] All 12 RFFL teams present
- [ ] Starter vs bench correctly identified
- [ ] D/ST slots correctly captured
- [ ] `applied_stats` preserved on lineup slots

### Checkpoint 6: Double-Dip Detection Test

Test correlation logic with explicit stat matching:
- [ ] Known double-dip detected (if Shaheed + SEA D/ST same owner)
- [ ] `verify_dst_return_td()` confirms stat match
- [ ] `attribution_method = "explicit_stat_match"` populated
- [ ] False positives excluded (player started, D/ST benched)
- [ ] NFL team matching works correctly

### Checkpoint 7: Anomaly Detection Test

Test anomaly handling:
- [ ] Player return TD without matching D/ST stat logs warning
- [ ] Type mismatch (punt vs kick) logs warning
- [ ] Anomalies excluded from double-dip count

### Checkpoint 8: Full Season Test

Run full 2024 season:
- [ ] All return TDs captured (both player and D/ST level)
- [ ] Double-dips correctly identified with full attribution
- [ ] Anomalies logged and documented
- [ ] Output DataFrame valid with all new fields

---

## Implementation Sequence

1. **Stat ID Discovery - Players** (current Cursor task)
   - Run discovery script
   - Document player KICK_RETURN_TD and PUNT_RETURN_TD stat IDs

2. **Stat ID Discovery - D/ST** (NEW for Option A)
   - Extend discovery script for D/ST entities
   - Document all 5 D/ST TD stat IDs
   - Create `src/rffl/forensic/stat_ids.py` with constants

3. **ReturnTDEvent Extraction**
   - Implement `extract_return_td_events()`
   - Capture player stat ID for full attribution
   - Test with single week

4. **Lineup Index Building**
   - Implement `build_lineup_index()`
   - Preserve `applied_stats` on each lineup slot
   - Integrate RFFL team code resolution

5. **D/ST TD Breakdown Parsing**
   - Implement `extract_dst_td_breakdown()`
   - Implement `verify_dst_return_td()`
   - Test with multi-TD D/ST games

6. **Double-Dip Detection (Full Attribution)**
   - Implement `detect_double_dips()` with explicit stat matching
   - Handle anomaly cases (log, don't crash)
   - Populate all new DoubleDipEvent fields

7. **Reporting**
   - Generate DataFrame with full attribution columns
   - Calculate summary statistics
   - Include anomaly summary
   - Format for case study

8. **Historical Analysis**
   - Run for all seasons (2019-2025 first, best data)
   - Document data gaps for 2011-2018
   - Generate final findings

---

## Commissioner Clarifications (Resolved)

| Question | Answer | Impact |
|----------|--------|--------|
| Bench scoring visibility | Yes, bench players show FPTS in boxscores | Filter on `is_starter=True` works correctly |
| Priority seasons | 2019-2025 (detailed boxscore data available) | Start with modern era, backfill if possible |
| Attribution method | Full Attribution (Option A) selected | Explicit stat ID matching required for both player AND D/ST |

---

**Document ID:** RFFL-INQ-2025-001-SPEC-001
**Version:** 1.1.0
**Created:** 2025-12-20
**Updated:** 2025-12-20
**Purpose:** Implementation specification for Cursor Forensic Agent
**Attribution Method:** Full Attribution (Option A) — Explicit stat ID matching
