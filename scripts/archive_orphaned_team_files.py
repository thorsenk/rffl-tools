#!/usr/bin/env python3
"""Archive orphaned team data files that are no longer used.

These files contain historical team codes and inconsistent formatting that
conflicts with the canonical registry (RFFL_REG_TEAMS_001).

Files to archive:
- teams_YYYY.csv (2011-2024) - Legacy files with non-canonical codes
- teams_all.csv - Aggregated version of above
- canonicals.yaml - Unused scaffold file
- all_abbrevs.csv - Audit file only

Usage:
    python scripts/archive_orphaned_team_files.py [--dry-run]
"""

import argparse
import shutil
from pathlib import Path
from datetime import datetime


ORPHANED_FILES = [
    "teams_2011.csv",
    "teams_2012.csv",
    "teams_2013.csv",
    "teams_2014.csv",
    "teams_2015.csv",
    "teams_2016.csv",
    "teams_2017.csv",
    "teams_2018.csv",
    "teams_2019.csv",
    "teams_2020.csv",
    "teams_2021.csv",
    "teams_2022.csv",
    "teams_2023.csv",
    "teams_2024.csv",
    "teams_all.csv",
    "canonicals.yaml",
    "all_abbrevs.csv",
    "observed_abbrevs.csv",  # Audit file with non-canonical codes, not used by codebase
]


def archive_files(repo_root: Path, dry_run: bool = False) -> None:
    """Archive orphaned team files to archive directory."""
    teams_dir = repo_root / "data" / "teams"
    archive_dir = repo_root / "data" / "teams" / "archive" / f"orphaned_{datetime.now().strftime('%Y%m%d')}"
    
    if not dry_run:
        archive_dir.mkdir(parents=True, exist_ok=True)
    
    archived = []
    missing = []
    
    for filename in ORPHANED_FILES:
        source = teams_dir / filename
        if source.exists():
            dest = archive_dir / filename
            if dry_run:
                print(f"Would archive: {source} → {dest}")
            else:
                shutil.move(str(source), str(dest))
                print(f"✅ Archived: {filename}")
            archived.append(filename)
        else:
            missing.append(filename)
    
    if missing:
        print(f"\n⚠️  Files not found (may already be archived): {', '.join(missing)}")
    
    if not dry_run:
        # Create README in archive explaining why files were archived
        readme_path = archive_dir / "README.md"
        readme_path.write_text(f"""# Archived Orphaned Team Files

**Archive Date**: {datetime.now().strftime('%Y-%m-%d')}

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

{chr(10).join(f"- {f}" for f in archived)}

## Recovery

If you need to recover these files, they are preserved in this archive directory.
However, **do not restore them to the main teams directory** as they conflict with the canonical registry.

Instead, use the Python registry:
```python
from rffl.core.registry import get_teams_by_season
teams_2011 = get_teams_by_season(2011)
```
""")
        print(f"\n✅ Archive created: {archive_dir}")
        print(f"📄 Archive README: {archive_dir / 'README.md'}")
    
    return len(archived)


def main():
    parser = argparse.ArgumentParser(
        description="Archive orphaned team data files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be archived without actually archiving",
    )
    args = parser.parse_args()
    
    # Find repo root
    repo_root = Path(__file__).parent.parent
    
    print("=" * 80)
    print("ARCHIVING ORPHANED TEAM FILES")
    print("=" * 80)
    print(f"\nRepository: {repo_root}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'ARCHIVE'}")
    print(f"\nFiles to archive: {len(ORPHANED_FILES)}")
    print("-" * 80)
    
    archived_count = archive_files(repo_root, dry_run=args.dry_run)
    
    print("-" * 80)
    if args.dry_run:
        print(f"\nDRY RUN: Would archive {archived_count} files")
        print("Run without --dry-run to actually archive files")
    else:
        print(f"\n✅ Archived {archived_count} files")
        print("\nNext steps:")
        print("1. Review archived files in data/teams/archive/")
        print("2. Commit the removal of orphaned files")
        print("3. Update .gitignore if needed")


if __name__ == "__main__":
    main()

