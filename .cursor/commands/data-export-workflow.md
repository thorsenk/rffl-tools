# Data Export Workflow

## Purpose

Complete workflow for exporting season data from ESPN API (boxscores, draft, transactions).

## When to Use

- ✅ Setting up a new season
- ✅ Refreshing season data
- ✅ Filling out a completed season
- ✅ Extracting data for analysis

## Quick Workflow

```bash
# Fill out a complete season (automated)
python scripts/fill_completed_season.py 2024
```

## Detailed Workflow

### 1. Scaffold Season Structure

```bash
# Create season directory structure
python scripts/scaffold_season.py 2024
```

**What it creates:**
- `data/seasons/2024/` directory
- `boxscores.csv` (for 2019+)
- `draft.csv`
- `transactions.csv` (for 2019+)
- `reports/` subdirectory

### 2. Export Boxscores

```bash
# Export boxscores for a season
rffl core export --year 2024 --fill-missing-slots --require-clean

# Export specific weeks
rffl core export --year 2024 --start-week 1 --end-week 17 --fill-missing-slots

# Export to custom location
rffl core export --year 2024 --out data/seasons/2024/boxscores.csv
```

**Options:**
- `--fill-missing-slots` - Insert 0-pt placeholders for missing starters
- `--require-clean` - Validate data and fail if inconsistencies found
- `--tolerance` - Allowed tolerance for validation (default: 0.0)

### 3. Export Draft Data

```bash
# Export draft results
rffl core draft --year 2024

# Export to custom location
rffl core draft --year 2024 --out data/seasons/2024/draft.csv
```

**Note:** Works for both snake and auction drafts.

### 4. Export Transactions

```bash
# Export transactions (requires authentication)
rffl core transactions --year 2024

# Requires ESPN_S2 and SWID in .env file
```

**Authentication Required:**
- Set `ESPN_S2` and `SWID` in `.env` file
- Extract from browser cookies when logged into ESPN Fantasy Football

**Availability:**
- 2019-2025 seasons only
- Historical seasons (2011-2018) have no transaction data

### 5. Export Stat Corrections (Optional)

```bash
# Export stat corrections (requires authentication)
rffl core stat-corrections --year 2024

# Export specific week
rffl core stat-corrections --year 2024 --week 15
```

**Note:** Stat corrections are filtered to RFFL league players only.

### 6. Validate Exported Data

```bash
# Validate boxscores
rffl core validate data/seasons/2024/boxscores.csv

# Validate with tolerance
rffl core validate data/seasons/2024/boxscores.csv --tolerance 0.02

# Validate lineup compliance
rffl core validate-lineup data/seasons/2024/boxscores.csv
```

## Automated Workflow

### Using fill_completed_season.py

```bash
# Fill out recent season (2019+)
python scripts/fill_completed_season.py 2024

# Fill out historical season (2011-2018)
python scripts/fill_completed_season.py 2018

# Options
python scripts/fill_completed_season.py 2024 \
  --start-week 1 \
  --end-week 17 \
  --no-fill-missing-slots \
  --skip-transactions
```

**What it does:**
- Automatically detects season type (historical vs recent)
- Exports appropriate data files
- Handles authentication requirements
- Provides progress feedback

### Batch Processing

```bash
# Fill out multiple seasons
for year in 2019 2020 2021 2022 2023 2024; do
    echo "Processing $year..."
    python scripts/fill_completed_season.py $year
done
```

## Historical Seasons (2011-2018)

**Available Data:**
- ✅ Draft data (`draft.csv`)
- ✅ Head-to-head matchups (`h2h.csv`)
- ❌ Boxscores (ESPN has purged this data)
- ❌ Transactions (not available)

**Export Commands:**
```bash
# Export draft
rffl core draft --year 2018

# Export h2h matchups
rffl core h2h --year 2018

# Export historical rosters (end-of-season)
rffl core historical-rosters --year 2018
```

## Recent Seasons (2019+)

**Available Data:**
- ✅ Boxscores (`boxscores.csv`)
- ✅ Draft (`draft.csv`)
- ✅ Transactions (`transactions.csv`)
- ✅ Stat corrections (`stat_corrections.csv`)

## Data Retention Policy

**Boxscores:**
- ESPN maintains detailed boxscore data for only **6 years** (5 past + current season)
- Currently (2025): Available for 2019-2025
- Next season (2026): Will purge 2019 data

**Transactions:**
- Available for 2019+ seasons
- May require authentication even for public leagues

**Preservation Strategy:**
- Always extract and save the oldest available year before new season begins
- Archive data before ESPN purges it

## Verification Checklist

After exporting, verify:

- [ ] Boxscores file exists and has data
- [ ] Draft file exists and has data
- [ ] Transactions file exists (if 2019+)
- [ ] Data validation passes
- [ ] Lineup validation passes
- [ ] File sizes are reasonable (not empty, not corrupted)

## Troubleshooting

### Authentication Errors

```bash
# Check credentials are set
echo $ESPN_S2
echo $SWID

# Or check .env file
cat .env | grep ESPN
```

### Missing Data

- **Boxscores**: Check if season is within 6-year window
- **Transactions**: Verify season is 2019+
- **Historical**: Only draft and h2h available for 2011-2018

### Validation Failures

```bash
# Check validation report
rffl core validate data/seasons/2024/boxscores.csv --tolerance 0.02

# Review validation output for specific issues
```

## Related Commands

- `season-data-audit.md` - Audit season data completeness
- `code-quality-check.md` - Verify code quality
- `docs-update.md` - Update documentation

## Success Criteria

✅ All data files exported successfully  
✅ Data validation passes  
✅ Files are properly formatted  
✅ Data is complete and consistent

