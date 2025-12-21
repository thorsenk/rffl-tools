# Team Registry Migration: CSV → Python SOT

**Date**: 2025-12-20  
**Status**: ✅ Complete

## Problem Statement

The codebase had inconsistent team data usage:
- `canonical_teams.csv` was treated as SOT but used historical codes
- `teams_YYYY.csv` files existed but were never loaded by code
- `canonicals.yaml` existed but wasn't used
- Multiple sources of truth created confusion and potential data drift

## Solution

Established **`src/rffl/core/registry.py` (RFFL_REG_TEAMS_001)** as the single Source of Truth:

1. **Python Registry Module** - Structured, type-safe, validated
2. **Backward Compatible** - `load_canonical_meta()` still works
3. **CSV Generation** - Script generates CSV from Python registry
4. **Clear Documentation** - Architecture documented in `data/teams/README.md`

## Changes Made

### 1. Created Python Registry (`src/rffl/core/registry.py`)
- 278 team records (2002-2025)
- Structured dataclasses (`TeamSeason`, `Ironman`, `Sabbatical`)
- Query functions: `get_team()`, `get_teams_by_season()`, `get_owner_history()`, etc.
- Built-in validation: `validate_registry()`

### 2. Updated `load_canonical_meta()` (`src/rffl/core/utils.py`)
- Now reads from Python registry instead of CSV
- Maintains same return format for backward compatibility
- No code changes required in consuming modules

### 3. Created CSV Generation Script (`scripts/generate_canonical_teams_csv.py`)
- Generates `canonical_teams.csv` from Python registry
- Ensures CSV stays in sync with SOT
- Can be run manually or in CI/CD

### 4. Updated Exports (`src/rffl/core/__init__.py`)
- Exports registry functions for easy import
- Makes registry accessible throughout codebase

### 5. Documentation (`data/teams/README.md`)
- Documents architecture and file roles
- Explains usage patterns
- Identifies deprecated/orphaned files

## Validation

✅ Registry validates correctly:
- 278 total records (expected: 278)
- 50 founding era (2002-2006) - 10 teams/season
- 228 modern era (2007-2025) - 12 teams/season
- All seasons have correct team counts
- `load_canonical_meta()` works correctly

## Migration Impact

### ✅ No Breaking Changes
- All existing code continues to work
- `load_canonical_meta()` interface unchanged
- CSV file still exists for external tooling

### ✅ Benefits
- Single Source of Truth eliminates confusion
- Type safety with Python dataclasses
- Built-in validation prevents data errors
- Easier to query and analyze team data
- Clear documentation of architecture

## Next Steps (Optional)

1. **Archive Orphaned Files**:
   - `teams_YYYY.csv` files (2011-2024) - not used by codebase
   - `canonicals.yaml` - not used by codebase
   - `all_abbrevs.csv` - audit file only

2. **Update External Tools**:
   - If any external tools depend on CSV format, ensure they use generated CSV
   - Consider migrating external tools to use Python registry directly

3. **CI/CD Integration**:
   - Add validation step: `python -c "from rffl.core.registry import validate_registry; assert validate_registry()['all_valid']"`
   - Regenerate CSV on registry changes: `python scripts/generate_canonical_teams_csv.py`

## Usage Examples

```python
# Get all teams in a season
from rffl.core.registry import get_teams_by_season
teams_2025 = get_teams_by_season(2025)

# Get specific team-season
from rffl.core.registry import get_team
team = get_team("GFM", 2025)

# Get owner history
from rffl.core.registry import get_owner_history
pcx_history = get_owner_history("THORSEN_KYLE")

# Backward compatible (still works)
from rffl.core.utils import load_canonical_meta
meta = load_canonical_meta()
team_info = meta.get((2025, "GFM"), {})
```

## Files Modified

- ✅ `src/rffl/core/registry.py` (NEW)
- ✅ `src/rffl/core/utils.py` (UPDATED)
- ✅ `src/rffl/core/__init__.py` (UPDATED)
- ✅ `scripts/generate_canonical_teams_csv.py` (NEW)
- ✅ `data/teams/canonical_teams.csv` (REGENERATED)
- ✅ `data/teams/README.md` (NEW)
- ✅ `docs/TEAM_REGISTRY_MIGRATION.md` (THIS FILE)

## Conclusion

The migration successfully establishes a single Source of Truth for team data while maintaining backward compatibility. The Python registry provides type safety, validation, and better query capabilities, while the CSV remains available for external tooling.

