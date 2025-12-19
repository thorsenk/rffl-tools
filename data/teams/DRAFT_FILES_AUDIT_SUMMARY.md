# RFFL Draft Files Audit Summary

**Date:** December 18, 2025  
**Files Audited:**
- Source A: `SourceA_rffl_canonicals_drafts_snake_all [Validate Clean SOT_].xlsx`
- Source B: `RFFL Draft Results (Source B) (1).xlsx`

---

## Executive Summary

Both files contain RFFL draft data from 2011-2024, with Source A also including 2025. While the overall structure is consistent (192 rows per year), there are significant data quality issues that need resolution:

- **384 team code mismatches** across 14 common years
- **136 player name mismatches** across 14 common years
- **192 records** exist only in Source A (2025 season)
- Source A has richer metadata (owner info, team full names, player IDs)
- Source B has keeper information that Source A lacks

---

## File Structure Comparison

### Source A (Source of Truth)
- **Years:** 2011-2025 (15 years)
- **Total Rows:** 2,880
- **Columns:** 14
- **Key Features:**
  - Complete owner information (owner_1, owner_2)
  - Team full names
  - Player IDs (ESPN)
  - Co-ownership flags
  - Round pick numbers
  - **Missing:** Keeper information

### Source B (AI Extracted)
- **Years:** 2011-2024 (14 years)
- **Total Rows:** 2,688
- **Columns:** 8 (expanded to 14 after normalization)
- **Key Features:**
  - Keeper information (36 keeper picks identified)
  - Simpler structure
  - **Missing:** Owner information, team full names, player IDs, co-ownership flags

---

## Data Quality Issues

### 1. Team Code Mismatches (384 total)

**Pattern:** Team codes differ between sources for the same draft pick.

**Examples:**
- 2011, Round 1, Pick 3: `2SCM` (Source A) vs `TJCH` (Source B)
- 2011, Round 1, Pick 4: `BBWZ` (Source A) vs `JFWO` (Source B)
- 2024: Consistent pattern with `SSBB` (Source A) vs `SSS` (Source B) - appears to be abbreviation difference

**Impact:** High - Team codes are critical for data integrity

**Recommendation:** 
- Investigate team code mapping between sources
- Determine canonical team codes (likely Source A based on "canonicals" in filename)
- Update Source B to match Source A team codes

### 2. Player Name Mismatches (136 total)

**Patterns Identified:**

1. **Spacing Issues:**
   - `BenJarvus Green-Ellis` vs `Ben Jarvus Green-Ellis`
   - `Knowshon Moreno` vs `KnoWASon Moreno` (appears to be typo in Source B)

2. **Missing Data:**
   - Source A has `nan` where Source B has player names (e.g., "Adrian Peterson", "Empty Spot")
   - Source A has 38 null player names total

3. **Empty Spot Handling:**
   - Source A: `nan`
   - Source B: `Empty Spot` (more explicit)

**Impact:** Medium - Affects player-level analysis

**Recommendation:**
- Standardize player name formatting (use Source A as base, fix typos)
- Replace `nan` with explicit "Empty Spot" or similar placeholder
- Cross-reference with ESPN API data to resolve discrepancies

### 3. Missing Year Coverage

**Issue:** Source B lacks 2025 season data

**Impact:** Low - Expected since Source B may not have been updated

**Recommendation:** Add 2025 data to Source B if needed

### 4. Missing Metadata

**Source A Missing:**
- Keeper information (Source B has 36 keeper picks identified)

**Source B Missing:**
- Owner information (100% null)
- Team full names (100% null)
- Player IDs (100% null)
- Co-ownership flags (100% null)
- Round pick numbers (100% null)

**Impact:** Medium - Limits analysis capabilities

**Recommendation:**
- Merge keeper information from Source B into Source A
- Source A should be considered the primary source for metadata

---

## Record Matching Analysis

**Match Rate:** 93.3% (2,688 of 2,880 records match on year/round/overall_pick)

**Breakdown:**
- ✅ Records in both: 2,688
- ⚠️ Only in Source A: 192 (2025 season)
- ✅ Only in Source B: 0

**Conclusion:** Excellent structural match - all records align on draft position, but data values differ.

---

## Recommendations

### Priority 1: Resolve Team Code Mismatches
1. **Create team code mapping table** documenting differences
2. **Determine canonical team codes** (recommend Source A as source of truth)
3. **Update Source B** to use canonical team codes
4. **Validate** against `canonical_teams.csv` if available

### Priority 2: Standardize Player Names
1. **Fix typos** in Source B (e.g., "KnoWASon Moreno" → "Knowshon Moreno")
2. **Standardize spacing** (e.g., "BenJarvus" → "Ben Jarvus")
3. **Handle null values** consistently (use "Empty Spot" or similar)
4. **Cross-reference** with ESPN API player data

### Priority 3: Merge Keeper Information
1. **Extract keeper flags** from Source B
2. **Merge into Source A** based on year/round/overall_pick
3. **Validate** keeper counts match expectations

### Priority 4: Data Completeness
1. **Fill missing player names** in Source A (38 nulls)
2. **Add 2025 data** to Source B if needed
3. **Document** any intentional data differences

---

## Next Steps

1. **Review team code mismatches** - Determine which source is correct
2. **Create reconciliation script** to merge best data from both sources
3. **Validate against ESPN API** where possible
4. **Create unified canonical file** combining strengths of both sources

---

## Technical Notes

- Both files use consistent structure: 192 rows per year (12 teams × 16 rounds)
- Source A appears to be manually curated ("User built our and edit")
- Source B appears to be AI-extracted ("Extracted from AI")
- Script used: `scripts/audit_draft_files.py`
- Full audit report: `DRAFT_FILES_AUDIT_REPORT.txt`

