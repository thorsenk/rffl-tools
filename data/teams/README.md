# RFFL Team Data Architecture

## Source of Truth (SOT)

**`src/rffl/core/registry.py` (RFFL_REG_TEAMS_001)** is the canonical Source of Truth for all team and owner data.

- **Version**: 1.0.0
- **Status**: Canonical
- **Authority**: Commissioner (PCX)
- **Last Validated**: 2025-12-19
- **Coverage**: 2002-2025 (24 seasons, 278 records)

## File Roles

### Primary SOT
- **`src/rffl/core/registry.py`** - Python module with structured data types (`TeamSeason`, `Ironman`, `Sabbatical`)
  - Used by all code in the codebase
  - Provides query functions: `get_team()`, `get_teams_by_season()`, `get_owner_history()`, etc.
  - Validated with `validate_registry()` function

### Generated Files (Derived from SOT)
- **`canonical_teams.csv`** - CSV export for backward compatibility and external tooling
  - Generated from Python registry via `scripts/generate_canonical_teams_csv.py`
  - Format: `season_year,team_code,team_full_name,is_co_owned,owner_code_1,owner_code_2`
  - **DO NOT EDIT MANUALLY** - Always regenerate from Python registry

### Supporting Files
- **`alias_mapping.yaml`** - Maps historical/alternate team codes to canonical codes
  - Used by `resolve_canonical()` function in `src/rffl/core/utils.py`
  - Handles ESPN API variations (e.g., `AC` → `CHLK`, `DKGG` → `DKEG`)

### Deprecated/Orphaned Files ⚠️ ARCHIVED

These files have been archived to `data/teams/archive/orphaned_YYYYMMDD/`:

- **`teams_YYYY.csv`** (2011-2024) - **ARCHIVED** - Legacy files with non-canonical team codes
  - Used historical codes (`COCK`, `AC`, `DKGG`, `GOW`, `PTB`) instead of canonical codes
  - Included `team_id` fields not in canonical registry
  - Had inconsistent formatting (some with "#" prefixes, team names with numbers)
  - **NOT USED** by any code in the codebase
- **`teams_all.csv`** - **ARCHIVED** - Aggregated version of above files
- **`canonicals.yaml`** - **ARCHIVED** - Unused scaffold/audit file
- **`all_abbrevs.csv`** - **ARCHIVED** - Summary/audit file only

**Why archived**: These files conflict with the canonical registry and create confusion about the Source of Truth. All data from these files is preserved in the Python registry (`src/rffl/core/registry.py`).

**To archive**: Run `python scripts/archive_orphaned_team_files.py`

## Usage

### In Python Code

```python
from rffl.core.registry import (
    get_team,
    get_teams_by_season,
    get_owner_history,
    REGISTRY
)

# Get all teams in 2011
teams_2011 = get_teams_by_season(2011)

# Get a specific team-season
team = get_team("GFM", 2025)

# Get owner history
pcx_history = get_owner_history("THORSEN_KYLE")
```

### Loading Metadata (for backward compatibility)

```python
from rffl.core.utils import load_canonical_meta

# Returns dict[(year, team_code), metadata]
meta = load_canonical_meta()
team_info = meta.get((2025, "GFM"), {})
```

## Updating Team Data

1. **Edit `src/rffl/core/registry.py`** - Update the `REGISTRY` tuple
2. **Run validation**: `python -c "from rffl.core.registry import validate_registry; print(validate_registry())"`
3. **Regenerate CSV**: `python scripts/generate_canonical_teams_csv.py`
4. **Commit changes** to both files

## Architecture Principles

1. **Single Source of Truth**: Python registry is authoritative
2. **Derived Files**: CSV is generated, never edited manually
3. **Backward Compatibility**: `load_canonical_meta()` maintains same interface
4. **Type Safety**: Python registry uses dataclasses for type safety
5. **Validation**: Built-in validation ensures data integrity

## Migration Notes

- `load_canonical_meta()` now reads from Python registry instead of CSV
- All code using `load_canonical_meta()` continues to work without changes
- CSV file remains for external tooling but is generated, not edited
- Historical team code resolution still uses `alias_mapping.yaml`

