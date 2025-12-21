# Cursor Prompt: Double-Dip Forensic Detection (Full Attribution)

## Context

You are implementing forensic tooling for the RFFL League Inquiry System. The first investigation (RFFL-INQ-2025-001) requires detecting "double-dip" events where an RFFL owner benefits from both:
- Individual player points (6 pts) for a kick/punt return TD
- D/ST unit points (6 pts) for the same play

**Reference Spec:** `rffl_double_dip_extraction_spec.md` (add to project context)

**Attribution Method:** Full Attribution (Option A) — We must explicitly match stat IDs on BOTH the player AND the D/ST to confirm a double-dip. Temporal correlation alone is insufficient.

---

## Task 1: Stat ID Discovery (Player + D/ST)

### Objective
Discover ESPN stat IDs for return TDs on both individual players AND D/ST units.

### Known Test Case
- **Player:** Rashid Shaheed (WR, SEA)
- **Event:** Kick return TD
- **Week:** 16, Season 2025 (if available) or use 2024 for testing
- **Expected:** Player has kick return TD stat, Seattle D/ST has matching kick return TD stat

### Implementation

Create `investigations/RFFL-INQ-2025-001/discover_stat_ids.py`:

```python
"""
ESPN Stat ID Discovery Script
Discover stat IDs for return TDs (player and D/ST)
"""

from rffl.core.api import ESPNClient
import json

def discover_stat_ids(season: int = 2024, week: int = 16):
    """
    Fetch boxscores and inspect player/D/ST stat structures.
    
    Goals:
    1. Find a player with a kick/punt return TD
    2. Extract their appliedStats dictionary
    3. Identify which stat ID represents the return TD
    4. Find the corresponding D/ST and verify matching stat
    """
    client = ESPNClient(league_id=323196, year=season)
    boxscores = client.get_boxscores(week=week)
    
    print(f"=== Season {season}, Week {week} ===\n")
    
    for matchup in boxscores:
        for side in ['home', 'away']:
            lineup = getattr(matchup, f'{side}_lineup', [])
            team = getattr(matchup, f'{side}_team', None)
            
            print(f"\n--- {team.team_name if team else 'Unknown'} ---")
            
            for player in lineup:
                # Check if this is a D/ST
                is_dst = player.slot_position == 'D/ST' or 'D/ST' in player.name
                
                # Get applied stats
                stats = getattr(player, 'stats', {})
                applied_stats = None
                
                # Stats structure varies - explore it
                if isinstance(stats, dict):
                    # Try to find appliedStats
                    for key, value in stats.items():
                        if hasattr(value, 'get'):
                            applied_stats = value.get('appliedStats', {})
                            break
                
                # Print players with significant points (potential return TD)
                points = getattr(player, 'points', 0)
                if points >= 6 or is_dst:
                    print(f"\nPlayer: {player.name}")
                    print(f"Position: {player.slot_position}")
                    print(f"Points: {points}")
                    print(f"Pro Team: {getattr(player, 'proTeam', 'N/A')}")
                    
                    if applied_stats:
                        print(f"Applied Stats: {json.dumps(applied_stats, indent=2)}")
                    else:
                        print(f"Raw Stats Object: {stats}")
                    
                    # Look for return-related stat IDs (likely in 70-80 range based on patterns)
                    if applied_stats:
                        for stat_id, value in applied_stats.items():
                            if value > 0:
                                print(f"  Stat {stat_id}: {value}")

def explore_raw_api(season: int = 2024, week: int = 16):
    """
    If espn_api library abstracts too much, fetch raw JSON.
    """
    from rffl.live.scores import LiveScoreClient
    
    client = LiveScoreClient(league_id=323196, season=season)
    data = client.fetch_scoreboard(scoring_period=week, include_boxscore=True)
    
    # Save for manual inspection
    with open(f"raw_boxscore_s{season}_w{week}.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved raw data to raw_boxscore_s{season}_w{week}.json")
    print("Search for 'appliedStats' in the JSON to find stat structure")

if __name__ == "__main__":
    # Try library approach first
    print("=== Using espn_api library ===")
    discover_stat_ids(season=2024, week=16)
    
    # If needed, dump raw API response
    print("\n\n=== Fetching raw API data ===")
    explore_raw_api(season=2024, week=16)
```

### Expected Output

Create `src/rffl/forensic/stat_ids.py` with discovered values:

```python
"""
ESPN Fantasy Football Stat IDs
Discovered via RFFL-INQ-2025-001 investigation
"""

class PlayerStatID:
    """Individual player stat IDs."""
    # Offensive stats
    PASSING_TD: int = 4
    RUSHING_TD: int = 25
    RECEIVING_TD: int = 43
    
    # Return stats (DISCOVERED)
    KICK_RETURN_TD: int = ???  # TODO: Fill from discovery
    PUNT_RETURN_TD: int = ???  # TODO: Fill from discovery
    
    # Return yards (for reference, not used in RFFL scoring)
    KICK_RETURN_YARDS: int = ???
    PUNT_RETURN_YARDS: int = ???


class DSTStatID:
    """D/ST unit stat IDs."""
    # Defensive stats
    SACKS: int = ???
    INTERCEPTIONS: int = ???
    FUMBLE_RECOVERIES: int = ???
    SAFETIES: int = ???
    BLOCKED_KICKS: int = ???
    
    # TD stats (DISCOVERED - Phase 1 Priority)
    KICK_RETURN_TD: int = ???  # TODO: Fill from discovery
    PUNT_RETURN_TD: int = ???  # TODO: Fill from discovery
    
    # TD stats (Phase 2)
    PICK_SIX: int = ???  # INT returned for TD
    FUMBLE_RETURN_TD: int = ???
    BLOCKED_KICK_TD: int = ???
    
    # Points allowed tiers
    POINTS_ALLOWED_0: int = ???
    POINTS_ALLOWED_1_6: int = ???
    # ... etc
```

---

## Task 2: Implement Core Extraction Functions

### File: `src/rffl/forensic/tools.py`

Update `ESPNAPITool` class with these methods:

```python
from rffl.forensic.stat_ids import PlayerStatID, DSTStatID
from dataclasses import dataclass
from typing import Optional
import pandas as pd

@dataclass
class ReturnTDEvent:
    season: int
    week: int
    nfl_player_id: int
    nfl_player_name: str
    nfl_team: str
    return_type: str  # "kick" or "punt"
    points_awarded: float
    stat_id: int

@dataclass
class DoubleDipEvent:
    season: int
    week: int
    rffl_team_code: str
    player_name: str
    player_slot: str
    player_points: float
    player_stat_id: int
    nfl_team: str
    dst_slot: str
    dst_total_points: float
    dst_return_td_points: float
    dst_stat_id: int
    total_benefit: float
    return_type: str
    attribution_method: str = "explicit_stat_match"


class ESPNAPITool:
    """ESPN API tool for forensic data extraction."""
    
    def __init__(self, league_id: int = 323196):
        self.league_id = league_id
    
    def extract_return_td_events(self, season: int, week: int = None) -> list[ReturnTDEvent]:
        """
        Extract all return TD events from boxscores.
        
        If week is None, scans entire season.
        """
        # Implementation per spec Section "Step 1"
        pass
    
    def build_lineup_index(self, season: int) -> dict[tuple[int, str], list]:
        """
        Build indexed lookup of all RFFL lineups.
        
        Key: (week, rffl_team_code)
        Value: list of lineup slots with applied_stats preserved
        """
        # Implementation per spec Section "Step 2"
        pass
    
    def detect_double_dips(
        self, 
        season: int,
        return_events: list[ReturnTDEvent] = None,
        lineup_index: dict = None
    ) -> list[DoubleDipEvent]:
        """
        Detect double-dip events using FULL ATTRIBUTION.
        
        Requires explicit stat ID match on both player AND D/ST.
        """
        # Implementation per spec Section "Step 3"
        pass
    
    def verify_dst_return_td(
        self, 
        dst_applied_stats: dict, 
        return_type: str
    ) -> Optional[dict]:
        """
        Verify D/ST has matching return TD stat.
        
        Returns dict with stat_id and count if found, None otherwise.
        """
        if return_type == "kick":
            target_stat_id = DSTStatID.KICK_RETURN_TD
        elif return_type == "punt":
            target_stat_id = DSTStatID.PUNT_RETURN_TD
        else:
            raise ValueError(f"Unknown return type: {return_type}")
        
        stat_value = dst_applied_stats.get(target_stat_id, 0)
        
        if stat_value > 0:
            return {
                "stat_id": target_stat_id,
                "count": int(stat_value),
                "points": stat_value * 6
            }
        return None
```

---

## Task 3: RFFL Team Code Resolution

### File: `src/rffl/forensic/tools.py` (add to ESPNAPITool)

```python
def resolve_rffl_team_code(self, espn_team, season: int) -> str:
    """
    Map ESPN team object to RFFL team code.
    
    Uses canonical registry from RFFL_REG_TEAMS_001.
    """
    from RFFL_REG_TEAMS_001 import get_teams_by_season
    
    season_teams = get_teams_by_season(season)
    espn_name = espn_team.team_name.lower() if hasattr(espn_team, 'team_name') else ''
    
    # Strategy 1: Exact match on team name
    for team in season_teams:
        if team.team_full_name.lower() == espn_name:
            return team.team_code
    
    # Strategy 2: Fuzzy match on team name
    for team in season_teams:
        if team.team_full_name.lower() in espn_name or espn_name in team.team_full_name.lower():
            return team.team_code
    
    # Strategy 3: Match by owner (if available)
    if hasattr(espn_team, 'owners'):
        for owner in espn_team.owners:
            owner_name = owner.get('firstName', '') + '_' + owner.get('lastName', '')
            owner_name = owner_name.upper()
            for team in season_teams:
                if owner_name in team.owner_code_1 or (team.owner_code_2 and owner_name in team.owner_code_2):
                    return team.team_code
    
    # Fallback
    logger.warning(f"Could not resolve RFFL team code for {espn_name}")
    return espn_name or "UNKNOWN"
```

---

## Task 4: CLI Integration

### File: `src/rffl/cli/forensic.py`

```python
import click
from rffl.forensic.tools import ESPNAPITool

@click.group()
def forensic():
    """Forensic investigation commands."""
    pass

@forensic.command()
@click.argument('case_id')
@click.option('--season', '-s', type=int, help='Season to analyze')
@click.option('--week', '-w', type=int, help='Specific week (optional)')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def investigate(case_id: str, season: int, week: int, output: str):
    """Run forensic investigation for a case."""
    
    if case_id == "RFFL-INQ-2025-001":
        tool = ESPNAPITool()
        
        click.echo(f"Investigating double-dip events for season {season}...")
        
        # Extract return TDs
        events = tool.extract_return_td_events(season, week)
        click.echo(f"Found {len(events)} return TD events")
        
        # Build lineup index
        lineup_index = tool.build_lineup_index(season)
        click.echo(f"Built lineup index for {len(lineup_index)} team-weeks")
        
        # Detect double-dips
        double_dips = tool.detect_double_dips(season, events, lineup_index)
        click.echo(f"Detected {len(double_dips)} double-dip events")
        
        # Output results
        if output:
            import pandas as pd
            df = pd.DataFrame([vars(dd) for dd in double_dips])
            df.to_csv(output, index=False)
            click.echo(f"Results saved to {output}")
        else:
            for dd in double_dips:
                click.echo(f"  {dd.season} W{dd.week}: {dd.rffl_team_code} - {dd.player_name} ({dd.return_type}) +{dd.total_benefit} pts")
    else:
        click.echo(f"Unknown case ID: {case_id}")

@forensic.command()
@click.option('--season', '-s', type=int, default=2024)
@click.option('--week', '-w', type=int, default=16)
def discover_stats(season: int, week: int):
    """Discover ESPN stat IDs from boxscore data."""
    # Run discovery script
    from investigations.RFFL_INQ_2025_001.discover_stat_ids import discover_stat_ids
    discover_stat_ids(season, week)
```

---

## Validation Checklist

Run these checks before marking complete:

### Phase 1: Stat ID Discovery
- [ ] `discover_stat_ids.py` runs without error
- [ ] Player kick return TD stat ID identified
- [ ] Player punt return TD stat ID identified
- [ ] D/ST kick return TD stat ID identified
- [ ] D/ST punt return TD stat ID identified
- [ ] `stat_ids.py` created with discovered values

### Phase 2: Extraction Logic
- [ ] `extract_return_td_events()` returns valid events
- [ ] `build_lineup_index()` captures all 12 teams
- [ ] `applied_stats` preserved on lineup slots
- [ ] D/ST slots correctly identified

### Phase 3: Double-Dip Detection
- [ ] `verify_dst_return_td()` correctly matches stats
- [ ] `detect_double_dips()` uses full attribution
- [ ] Anomalies logged (not crashed)
- [ ] Output DataFrame has all required columns

### Phase 4: Integration Test
- [ ] `rffl forensic investigate RFFL-INQ-2025-001 -s 2024` runs
- [ ] Results match expected (based on known events)
- [ ] CSV output valid

---

## Success Criteria

Investigation is complete when:

1. **Stat IDs documented** in `src/rffl/forensic/stat_ids.py`
2. **Extraction pipeline working** for seasons 2019-2025
3. **Double-dip events identified** with full attribution
4. **CLI command functional**: `rffl forensic investigate RFFL-INQ-2025-001 -s 2024`
5. **Results exportable** to CSV for case study documentation

---

## Reference Files

- `rffl_double_dip_extraction_spec.md` — Full specification
- `RFFL_REG_TEAMS_001.py` — Team/owner registry for team code resolution
- `RFFL-INQ-2025-001_Return_TD_Double_Scoring.md` — Case study document (to be updated with findings)
