# Season Data Audit

## Purpose

Audit a season's data completeness, consistency, and quality.

## When to Use

- ✅ After exporting season data
- ✅ Before using data for analysis
- ✅ When verifying data integrity
- ✅ As part of data quality checks

## Quick Audit

```bash
# Validate boxscores
rffl core validate data/seasons/2024/boxscores.csv

# Validate lineup compliance
rffl core validate-lineup data/seasons/2024/boxscores.csv
```

## Detailed Audit Steps

### 1. Check File Existence

```bash
# Check for required files
YEAR=2024
ls -la data/seasons/$YEAR/

# Expected files for recent seasons (2019+):
# - boxscores.csv
# - draft.csv
# - transactions.csv
# - stat_corrections.csv (optional)
# - reports/ directory

# Expected files for historical seasons (2011-2018):
# - draft.csv
# - h2h.csv
# - reports/ directory
```

### 2. Validate Boxscores

```bash
# Basic validation
rffl core validate data/seasons/2024/boxscores.csv

# Validation with tolerance
rffl core validate data/seasons/2024/boxscores.csv --tolerance 0.02

# Check validation report if issues found
```

**What it checks:**
- Team-week consistency
- Projected vs actual totals match
- Starter counts (should be 9)
- Sum of starter points matches team totals

### 3. Validate Lineup Compliance

```bash
# Validate RFFL lineup rules
rffl core validate-lineup data/seasons/2024/boxscores.csv

# Generate detailed report
rffl core validate-lineup data/seasons/2024/boxscores.csv --out reports/lineup_validation_2024.md
```

**What it checks:**
- 1 QB, 2 RB, 2 WR, 1 TE, 1 FLEX, 1 D/ST, 1 K
- No invalid position assignments
- All required slots filled

### 4. Check Data Completeness

```bash
# Check file sizes (should not be empty)
ls -lh data/seasons/2024/*.csv

# Check row counts
wc -l data/seasons/2024/boxscores.csv
wc -l data/seasons/2024/draft.csv
wc -l data/seasons/2024/transactions.csv
```

### 5. Verify Week Coverage

```python
# Quick Python check
import pandas as pd

df = pd.read_csv("data/seasons/2024/boxscores.csv")
weeks = df["week"].unique()
print(f"Weeks covered: {sorted(weeks)}")
print(f"Total weeks: {len(weeks)}")
```

**Expected:**
- Regular season: Weeks 1-14 (or 1-17 depending on season)
- Playoffs: Weeks 15-18 (if applicable)

### 6. Check Team Coverage

```python
# Check all teams are represented
import pandas as pd

df = pd.read_csv("data/seasons/2024/boxscores.csv")
teams = df["team_code"].unique()
print(f"Teams: {sorted(teams)}")
print(f"Total teams: {len(teams)}")
```

**Expected:** 12 teams (or current league size)

### 7. Validate Draft Data

```bash
# Check draft file exists and has data
head -5 data/seasons/2024/draft.csv

# Verify draft picks count (should be ~192 for 12 teams, 16 rounds)
wc -l data/seasons/2024/draft.csv
```

### 8. Validate Transactions (2019+)

```bash
# Check transactions file
head -5 data/seasons/2024/transactions.csv

# Count transactions
wc -l data/seasons/2024/transactions.csv

# Check transaction types
cut -d',' -f9 data/seasons/2024/transactions.csv | sort | uniq -c
```

### 9. Check Stat Corrections (Optional)

```bash
# Verify stat corrections are filtered to RFFL teams
head -5 data/seasons/2024/stat_corrections.csv

# Check rffl_team_code column exists
head -1 data/seasons/2024/stat_corrections.csv | grep rffl_team_code
```

## Automated Audit Script

Create a simple audit script:

```python
#!/usr/bin/env python3
"""Audit season data completeness."""

import sys
from pathlib import Path
import pandas as pd

def audit_season(year: int):
    """Audit season data."""
    season_dir = Path(f"data/seasons/{year}")
    
    print(f"\n=== Auditing Season {year} ===\n")
    
    # Check files exist
    required_files = {
        "boxscores.csv": year >= 2019,
        "draft.csv": True,
        "transactions.csv": year >= 2019,
        "h2h.csv": year < 2019,
    }
    
    for file, required in required_files.items():
        path = season_dir / file
        if required:
            if path.exists():
                size = path.stat().st_size
                rows = sum(1 for _ in open(path)) - 1  # Subtract header
                print(f"✅ {file}: {rows:,} rows ({size:,} bytes)")
            else:
                print(f"❌ {file}: MISSING")
        else:
            if path.exists():
                print(f"⚠️  {file}: Present but not required for {year}")
    
    # Validate boxscores if exists
    boxscores_path = season_dir / "boxscores.csv"
    if boxscores_path.exists():
        df = pd.read_csv(boxscores_path)
        weeks = sorted(df["week"].unique())
        teams = sorted(df["team_code"].unique())
        print(f"\n📊 Boxscores:")
        print(f"   Weeks: {weeks[0]}-{weeks[-1]} ({len(weeks)} weeks)")
        print(f"   Teams: {len(teams)} teams")
        print(f"   Team-weeks: {len(df.groupby(['week', 'team_code']))}")

if __name__ == "__main__":
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    audit_season(year)
```

## Audit Checklist

### File Completeness
- [ ] All required files exist
- [ ] Files are not empty
- [ ] File sizes are reasonable

### Data Quality
- [ ] Boxscores validation passes
- [ ] Lineup validation passes
- [ ] No missing weeks
- [ ] All teams represented

### Data Consistency
- [ ] Team totals match sum of starters
- [ ] Projected totals match sum of projected starters
- [ ] Starter counts are correct (9 per team-week)

### Data Completeness
- [ ] All weeks covered (1-14 or 1-17)
- [ ] All teams have data for all weeks
- [ ] Draft data complete
- [ ] Transactions complete (if 2019+)

## Common Issues

### Missing Files

```bash
# Re-export missing files
rffl core export --year 2024
rffl core draft --year 2024
rffl core transactions --year 2024
```

### Validation Failures

```bash
# Check validation report
rffl core validate data/seasons/2024/boxscores.csv --tolerance 0.02

# Review specific issues
# Fix data or re-export
```

### Incomplete Data

```bash
# Re-export with proper week range
rffl core export --year 2024 --start-week 1 --end-week 17
```

## Related Commands

- `data-export-workflow.md` - Export data workflow
- `code-quality-check.md` - Code quality checks
- `docs-update.md` - Update documentation

## Success Criteria

✅ All required files exist  
✅ Files contain data (not empty)  
✅ Validation passes  
✅ Lineup validation passes  
✅ Data is complete and consistent  
✅ All teams and weeks represented

