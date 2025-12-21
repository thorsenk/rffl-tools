# ESPN Stat ID Mapping Plan (Updated)

## Objective

Identify ESPN's stat IDs for **Kick Return TD** and **Punt Return TD** for both **individual players AND D/ST units** to enable Full Attribution detection of double-dip events.

**Attribution Method:** **Full Attribution (Option A)** — Explicit stat ID matching required on BOTH player AND D/ST to confirm double-dip.

## Key Specifications from Inbox

### Full Attribution Requirements

From `rffl_double_dip_extraction_spec.md`:
- Must explicitly verify D/ST's `appliedStats` contains matching return TD stat ID
- Cannot rely on temporal correlation alone
- Stat ID values must match between player and D/ST
- Type must match exactly (kick ↔ kick, punt ↔ punt)

### Data Models Required

**ReturnTDEvent:**
- season, week, nfl_player_id, nfl_player_name, nfl_team
- return_type ("kick" | "punt")
- points_awarded, stat_id

**DoubleDipEvent:**
- All ReturnTDEvent fields plus:
- rffl_team_code, player_slot, player_points, player_stat_id
- dst_slot, dst_total_points, dst_return_td_points, dst_stat_id
- total_benefit, attribution_method ("explicit_stat_match")

### Discovery Priority

**Phase 1 (Required):**
1. Player Kick Return TD stat ID
2. Player Punt Return TD stat ID
3. D/ST Kick Return TD stat ID
4. D/ST Punt Return TD stat ID

**Phase 2 (Complete D/ST Taxonomy):**
5. D/ST Pick-Six stat ID
6. D/ST Fumble Return TD stat ID
7. D/ST Blocked Kick TD stat ID

## Discovery Script Template

Based on `cursor_prompt_double_dip_forensics.md`, create:

**File:** `investigations/RFFL-INQ-2025-001/discover_stat_ids.py`

**Key Features:**
- Fetch Week 16, 2024 (known Shaheed return TD)
- Inspect both player AND D/ST stat structures
- Export raw JSON for manual inspection
- Identify stat IDs for both player and D/ST return TDs

## Stat IDs Module Structure

**File:** `src/rffl/forensic/stat_ids.py`

```python
class PlayerStatID:
    """Individual player stat IDs."""
    KICK_RETURN_TD: int = None  # TBD
    PUNT_RETURN_TD: int = None  # TBD

class DSTStatID:
    """D/ST unit stat IDs."""
    KICK_RETURN_TD: int = None  # TBD - may differ from player
    PUNT_RETURN_TD: int = None  # TBD
    PICK_SIX: int = None  # Phase 2
    FUMBLE_RETURN_TD: int = None  # Phase 2
    BLOCKED_KICK_TD: int = None  # Phase 2
```

## Implementation Updates Required

### 1. Update `ESPNAPITool.get_scoring_plays()`

Must extract return TDs with stat IDs preserved for Full Attribution matching.

### 2. Add `verify_dst_return_td()` Method

**From spec:**
```python
def verify_dst_return_td(dst_slot, return_type: str) -> dict | None:
    """
    Verify D/ST has matching return TD stat.
    
    Returns dict with stat_id and count if found, None otherwise.
    """
    # Check dst_slot.applied_stats for matching stat ID
    # Return type must match exactly (kick ↔ kick, punt ↔ punt)
```

### 3. Update `detect_double_dips()` Logic

**Full Attribution Flow:**
1. Find player return TD event
2. Find which RFFL team started that player
3. Check if same team started corresponding D/ST
4. **EXPLICITLY VERIFY:** D/ST's `appliedStats` contains matching return TD stat ID
5. If stat match confirmed → Double-dip with `attribution_method="explicit_stat_match"`
6. If no stat match → Log anomaly, do NOT count as double-dip

### 4. Edge Cases (New from Spec)

**Edge Case 8: Stat Mismatch Anomaly**
- Player shows return TD but D/ST stat is 0
- Log as anomaly, exclude from double-dip count

**Edge Case 9: Punt vs Kick Mismatch**
- Player has punt return TD, D/ST only has kick return TD
- Type must match exactly, log anomaly if mismatch

## Updated Implementation Sequence

1. ✅ **Create discovery script** (`discover_stat_ids.py`)
   - Use template from cursor_prompt
   - Focus on Week 16, 2024 (Shaheed event)
   - Inspect BOTH player AND D/ST structures

2. ⏳ **Run discovery and document stat IDs**
   - Identify all 4 Phase 1 stat IDs
   - Create `stat_ids.py` with discovered values
   - Test with known event

3. ⏳ **Implement Full Attribution extraction**
   - Update `get_scoring_plays()` to preserve stat IDs
   - Add `verify_dst_return_td()` method
   - Update `detect_double_dips()` with explicit stat matching

4. ⏳ **Handle anomalies**
   - Log stat mismatches
   - Log type mismatches
   - Exclude anomalies from double-dip count

5. ⏳ **Test with known event**
   - Week 16, 2024 Shaheed return TD
   - Verify Full Attribution works
   - Confirm double-dip detection

## Key Differences from Original Plan

1. **Full Attribution Required:** Cannot use temporal correlation, must match stat IDs explicitly
2. **D/ST Stat IDs Needed:** Not just player stat IDs, need D/ST stat IDs too
3. **Anomaly Handling:** Must log and exclude mismatches, not just count them
4. **Type Matching:** Kick vs punt must match exactly between player and D/ST
5. **Data Models:** More detailed data structures required (ReturnTDEvent, DoubleDipEvent)

## Next Steps

1. Create `discover_stat_ids.py` using template from inbox
2. Run discovery script with Week 16, 2024 data
3. Document discovered stat IDs in `stat_ids.py`
4. Update `tools.py` with Full Attribution logic
5. Test with known Shaheed event
6. Implement anomaly logging

## Reference Documents

- `inbox/cursor_prompt_double_dip_forensics.md` - Implementation tasks
- `inbox/rffl_double_dip_extraction_spec.md` - Full specification
- `investigations/RFFL-INQ-2025-001/README.md` - Investigation overview
