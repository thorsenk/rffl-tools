# Archived Orphaned Team Files

**Archive Date**: 2025-12-21

## Why These Files Were Archived

These files were archived because they:

1. **Use non-canonical team codes** - Codes like `COCK`, `AC`, `DKGG`, `GOW`, `PTB` instead of canonical codes (`PCX`, `CHLK`, `DKEG`, `JAGB`, `PITB`)
2. **Are not used by codebase** - No code references these files
3. **Have inconsistent formatting** - Some have "#" prefixes, team names with numbers, etc.
4. **Create confusion** - Multiple sources of truth conflict with canonical registry

## Current Source of Truth

**`src/rffl/core/registry.py` (RFFL_REG_TEAMS_001)** is the canonical Source of Truth.

All team data is now managed through:
- Python registry module with structured dataclasses
- `canonical_teams.csv` (generated from Python registry)
- `alias_mapping.yaml` (maps historical codes to canonical)

## Files Archived

- observed_abbrevs.csv

## Recovery

If you need to recover these files, they are preserved in this archive directory.
However, **do not restore them to the main teams directory** as they conflict with the canonical registry.

Instead, use the Python registry:
```python
from rffl.core.registry import get_teams_by_season
teams_2011 = get_teams_by_season(2011)
```
