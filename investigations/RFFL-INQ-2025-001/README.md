# RFFL-INQ-2025-001: Return TD "Double Dip" Forensic Validation

## Status

**Scaffold Complete** ✅  
**Implementation Pending** ⏳

## What's Been Scaffolded

The complete forensic investigation agent structure has been created:

1. **Module Structure** (`src/rffl/forensic/`)
   - `schemas.py` - Investigation configuration schemas (enums, dataclasses)
   - `tools.py` - ESPNAPITool and DataAnalysisTool (stubs with NotImplementedError)
   - `investigations.py` - ReturnTDDoubleDipInvestigation class (structure ready)
   - `reporter.py` - Legal memo format report generator
   - `agent.py` - ForensicAgent orchestrator
   - `__init__.py` - Module exports

2. **CLI Commands** (`rffl forensic`)
   - `investigate <case-id>` - Execute investigation
   - `list` - List all investigations
   - `approve <case-id>` - Mark as commissioner-approved

3. **Investigation Configuration**
   - `investigation.yaml` - Complete configuration for RFFL-INQ-2025-001

## What Needs Implementation

### Critical: ESPN Stat ID Mapping

The core implementation work is in `ESPNAPITool.get_scoring_plays()`:

**Location:** `src/rffl/forensic/tools.py`

**What's Needed:**
1. Identify ESPN stat IDs for:
   - Kick Return TD
   - Punt Return TD

2. Extract return TD events from ESPN API:
   - Query boxscores using `ESPNClient.get_boxscores(week)`
   - Iterate through players in each boxscore
   - Check `player.stats.appliedStats` for return TD stat IDs
   - Extract: player_id, player_name, proTeamId, points, lineup_slot
   - Map proTeamId to NFL team abbreviation
   - Resolve RFFL team_code from team registry

3. Extract D/ST return TD scoring:
   - Find D/ST players (position == "D/ST")
   - Check if D/ST scoring includes return TD component
   - Map to RFFL team_code

**Research Required:**
- ESPN API stat ID reference documentation
- Example boxscore data structure inspection
- Testing with actual ESPN API responses

### Other Implementation Tasks

1. **ESPNAPITool.get_dst_scoring()** - Extract D/ST scoring with return TD flags
2. **ESPNAPITool.get_rosters()** - Extract roster composition
3. **ESPNAPITool.map_player_to_dst()** - Map player to D/ST team
4. **ReturnTDDoubleDipInvestigation.counterfactual_analysis()** - Identify missed opportunities

## Testing the Scaffold

```bash
# List investigations
rffl forensic list

# Dry run (shows investigation plan)
rffl forensic investigate RFFL-INQ-2025-001 --dry-run --force

# Approve investigation
rffl forensic approve RFFL-INQ-2025-001

# Run investigation (will fail with NotImplementedError until ESPN API is implemented)
rffl forensic investigate RFFL-INQ-2025-001 --season 2024 --force
```

## Next Steps

1. Research ESPN API stat IDs for return TDs
2. Implement `ESPNAPITool.get_scoring_plays()` with actual API calls
3. Test with a single season (2024) to verify data extraction
4. Implement remaining tool methods
5. Complete counterfactual analysis logic
6. Generate final report

