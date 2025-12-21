# Orphaned Team Files Cleanup

**Date**: 2025-12-21  
**Status**: ✅ Complete

## Problem

The repository contained **17 orphaned team data files** that:

1. **Used non-canonical team codes** - Codes like `COCK`, `AC`, `DKGG`, `GOW`, `PTB` instead of canonical codes (`PCX`, `CHLK`, `DKEG`, `JAGB`, `PITB`)
2. **Were never used by codebase** - No code references these files
3. **Had inconsistent formatting** - Some had "#" prefixes, team names with numbers, inconsistent spacing
4. **Created confusion** - Multiple sources of truth conflicted with canonical registry
5. **Included extra fields** - `team_id` fields not present in canonical registry

## Files Archived

All files archived to `data/teams/archive/orphaned_20251221/`:

### Per-Season Files (14 files)
- `teams_2011.csv` through `teams_2024.csv`
- Each contained 12-13 rows with historical team codes

### Aggregated Files (3 files)
- `teams_all.csv` - Combined version of all per-season files
- `canonicals.yaml` - Unused scaffold file
- `all_abbrevs.csv` - Audit/summary file

## Examples of Data Issues

### Non-Canonical Codes
- `COCK` → Should be `PCX` (Gypsy Peacocks)
- `AC` → Should be `CHLK` (Alpha Chalkers)
- `DKGG` → Should be `DKEG` (Da Keggers)
- `GOW` → Should be `JAGB` (Jag Bombers)
- `PTB` → Should be `PITB` (Raging Pitbulls)
- `MJI` → Should be `MRYJ` (Mary Jane)
- `BBRS` → Should be `BALL` (Blue Ballers)

### Inconsistent Formatting
- Some team names had "#" prefixes: `#2 Drew Peacocks`
- Some had numbers: `5 Drew Peacocks`
- Some had inconsistent spacing: ` Drew Peacocks`
- Some had special characters: `Jagbombers !!`

### Extra Fields
- `team_id` field not in canonical registry
- Team names varied significantly from canonical full names

## Solution

1. **Archived all orphaned files** to preserve historical data
2. **Created archive README** explaining why files were archived
3. **Updated documentation** to reflect cleanup
4. **No data loss** - All data preserved in Python registry (`src/rffl/core/registry.py`)

## Current Clean State

### Active Files (SOT)
- ✅ `src/rffl/core/registry.py` - Python registry (RFFL_REG_TEAMS_001)
- ✅ `canonical_teams.csv` - Generated from Python registry
- ✅ `alias_mapping.yaml` - Maps historical codes to canonical

### Archived Files
- 📦 `data/teams/archive/orphaned_20251221/` - All orphaned files preserved

## Verification

✅ No code references orphaned files:
```bash
grep -r "teams_\d{4}\.csv\|teams_all\.csv" src/
# No matches found
```

✅ All team data accessible via Python registry:
```python
from rffl.core.registry import get_teams_by_season
teams_2011 = get_teams_by_season(2011)  # Returns canonical data
```

## Recovery

If you need to recover archived files:
1. Files are preserved in `data/teams/archive/orphaned_20251221/`
2. **DO NOT restore to main teams directory** - They conflict with canonical registry
3. Use Python registry instead: `from rffl.core.registry import get_teams_by_season`

## Scripts Created

- `scripts/archive_orphaned_team_files.py` - Archive script with dry-run support
- Can be reused if more orphaned files are discovered

## Impact

- ✅ **Cleaner repository** - No conflicting data sources
- ✅ **Clear SOT** - Single source of truth (Python registry)
- ✅ **No breaking changes** - All code continues to work
- ✅ **Data preserved** - All data archived, not deleted
- ✅ **Better documentation** - Clear explanation of what's active vs archived

