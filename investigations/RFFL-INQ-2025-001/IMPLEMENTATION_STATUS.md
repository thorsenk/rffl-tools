# Implementation Status: RFFL-INQ-2025-001

## ✅ Completed

### 1. Stat ID Discovery
- **Kick Return TD Stat ID: 102** ✅ DISCOVERED
  - Confirmed via Week 16, 2025 - Rashid Shaheed (SEA) kick return TD
  - Same stat ID (102) used for both player AND D/ST
- **Punt Return TD Stat ID: TBD** ⏳ (Not yet discovered - no punt return TD events found in test data)

### 2. Core Infrastructure
- ✅ `src/rffl/forensic/stat_ids.py` - Stat ID constants module
- ✅ `src/rffl/forensic/tools.py` - ESPNAPITool with:
  - ✅ `get_scoring_plays()` - Extract player return TDs using raw API
  - ✅ `get_dst_scoring()` - Extract D/ST scoring with return TD flags
  - ✅ `verify_dst_return_td()` - Full Attribution verification method
- ✅ `src/rffl/forensic/investigations.py` - ReturnTDDoubleDipInvestigation class structure
- ✅ `src/rffl/forensic/agent.py` - ForensicAgent orchestrator
- ✅ `src/rffl/forensic/reporter.py` - Legal memo report generator
- ✅ CLI commands (`rffl forensic investigate`, `list`, `approve`)

### 3. Discovery Scripts
- ✅ `discover_stat_ids.py` - Initial discovery script
- ✅ `analyze_stat_ids.py` - Analysis script that found Stat ID 102

## ⏳ In Progress / Needs Work

### 1. Full Attribution Verification
The `cross_reference_double_dips()` method needs to:
- Access raw appliedStats dictionaries for D/ST units
- Explicitly verify matching stat IDs (not just temporal correlation)
- Log anomalies when player has return TD but D/ST doesn't

**Current Status**: Basic join implemented, but Full Attribution verification needs access to raw stats at cross-reference time.

### 2. RFFL Team Code Resolution
The team code resolution logic needs refinement:
- Currently uses `resolve_canonical()` but may need fallback strategies
- Should handle ESPN team name variations
- May need owner-based matching for edge cases

### 3. Lineup Index Building
`build_lineup_index()` method needs implementation:
- Extract all lineup slots with appliedStats preserved
- Map to RFFL team codes
- Determine starter vs bench status

### 4. Counterfactual Analysis
`counterfactual_analysis()` needs implementation:
- Identify missed double-dip opportunities
- Check if D/ST was available but not rostered

## 🔍 Testing Needed

1. **Test Stat ID 102 extraction**:
   ```bash
   # Should find Shaheed's Week 16, 2025 return TD
   python -c "from rffl.forensic.tools import ESPNAPITool; tool = ESPNAPITool(); df = tool.get_scoring_plays(2025, 16); print(df[df['player_name'].str.contains('Shaheed')])"
   ```

2. **Test D/ST extraction**:
   ```bash
   # Should find Seattle D/ST Week 16, 2025 with return TD
   python -c "from rffl.forensic.tools import ESPNAPITool; tool = ESPNAPITool(); df = tool.get_dst_scoring(2025, 16); print(df[df['dst_team'] == 'SEA'])"
   ```

3. **Test Full Investigation**:
   ```bash
   rffl forensic investigate RFFL-INQ-2025-001 --season 2025 --force
   ```

## 📝 Notes

- Stat ID 102 confirmed for kick return TD (both player and D/ST)
- Raw API approach works - `LiveScoreClient` provides access to `appliedStats`
- Team code resolution may need refinement based on actual ESPN team name formats
- Full Attribution verification requires preserving appliedStats through the pipeline

## Next Steps

1. Test `get_scoring_plays()` with Week 16, 2025 data
2. Test `get_dst_scoring()` with Week 16, 2025 data  
3. Implement Full Attribution verification in cross-reference logic
4. Test full investigation pipeline
5. Discover punt return TD stat ID (when event occurs)

