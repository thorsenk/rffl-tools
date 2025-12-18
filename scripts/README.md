# Scripts

Utility scripts for RFFL Tools.

## Available Scripts

### `scaffold_season.py`

Creates a new season directory structure with empty CSV files and proper headers.

**Usage:**
```bash
python scripts/scaffold_season.py 2025
```

**What it does:**
- Automatically detects if season is historical (2011-2018) or recent (2019+)
- Creates `data/seasons/{YEAR}/` directory
- Creates `reports/` subdirectory
- Creates appropriate CSV files based on season type:

  **Recent seasons (2019+):**
  - `boxscores.csv`
  - `draft.csv`
  - `reports/{YEAR}-Draft-Snake-Canonicals.csv`
  - `reports/boxscores_normalized.csv`
  - `reports/teamweek_unified.csv`

  **Historical seasons (2011-2018):**
  - `draft.csv`
  - `h2h.csv`
  - `reports/{YEAR}-Draft-Snake-Canonicals.csv`
  - `reports/h2h_teamweek.csv`

---

### `extract_all_transactions.py`

Extracts transactions for all seasons 2019-2025 in batch.

**Usage:**
```bash
# Set credentials first
export ESPN_S2="your_espn_s2_value"
export SWID="your_swid_value"
export LEAGUE=323196

# Run the script
python scripts/extract_all_transactions.py
```

**What it does:**
- Extracts transactions for seasons 2019-2025
- Saves to `data/seasons/{YEAR}/transactions.csv` for each season
- Shows progress and summary of results
- Handles errors gracefully (continues if one season fails)

**Output:**
- Creates/updates `transactions.csv` in each season folder
- Displays transaction count for each successful extraction
- Shows summary of successes and errors

---

### `fill_completed_season.py`

Fills out a completed season by exporting data from ESPN API. Automatically handles historical vs recent seasons.

**Usage:**
```bash
# Fill out recent season 2024 (uses $LEAGUE env var)
python scripts/fill_completed_season.py 2024

# Fill out recent season 2023 with specific league ID
python scripts/fill_completed_season.py 2023 --league 323196

# Fill out recent season 2022, weeks 1-17 only
python scripts/fill_completed_season.py 2022 --start-week 1 --end-week 17

# Fill out historical season 2011 (draft + h2h only)
python scripts/fill_completed_season.py 2011 --league 323196

# Export only boxscores (skip draft) - 2019+ only
python scripts/fill_completed_season.py 2024 --skip-draft

# Export only draft (skip boxscores)
python scripts/fill_completed_season.py 2024 --skip-boxscores
```

**Options:**
- `--league LEAGUE` - ESPN league ID (defaults to $LEAGUE env var)
- `--start-week N` - Start week (default: 1)
- `--end-week N` - End week (default: 18)
- `--no-fill-missing-slots` - Don't fill missing starter slots
- `--no-require-clean` - Don't require clean data validation
- `--skip-draft` - Skip draft export
- `--skip-boxscores` - Skip boxscores export
- `--skip-transactions` - Skip transactions export (2019+ only)

**Authentication:**
- Set `ESPN_S2` and `SWID` environment variables to enable transaction export
- These can be extracted from browser cookies when logged into ESPN Fantasy Football
- See `.env.example` for details

**What it does:**

**For recent seasons (2019+):**
1. Exports boxscores using `rffl core export` (detailed player-level data)
2. Exports draft using `rffl core draft`
3. Exports transactions using `rffl core transactions` (optional, may require authentication)
4. Creates necessary directories if they don't exist
5. Provides progress feedback and error handling

**For historical seasons (2011-2018):**
1. Automatically skips boxscores export (ESPN has purged this data)
2. Automatically skips transactions export (not available for old seasons)
3. Exports draft using `rffl core draft`
4. Exports h2h matchups using `rffl core h2h` (matchup results only)
5. Creates necessary directories if they don't exist
6. Provides progress feedback and error handling

**Note:** 
- Report files (`boxscores_normalized.csv`, `teamweek_unified.csv`) need to be generated separately using post-processing scripts (2019+ only)
- Historical seasons (2011-2018) do NOT have detailed boxscore data available (ESPN has purged this data)
- Transactions are available for 2018+ seasons but may require authentication even for public leagues
- Transaction export failures are non-fatal (warnings only) since they may require authentication

---

## Workflow Example

### Filling out a new completed season:

```bash
# 1. Scaffold the season directory structure
python scripts/scaffold_season.py 2024

# 2. Fill it with data from ESPN API
python scripts/fill_completed_season.py 2024

# 3. Generate report files (if post-processing scripts exist)
# TODO: Add report generation scripts
```

### Batch processing multiple seasons:

```bash
# Fill out seasons 2011-2025
# Note: Historical seasons (2011-2018) will only export draft + h2h
# Recent seasons (2019-2025) will export full boxscore data
for year in {2011..2025}; do
    echo "Processing season $year..."
    python scripts/fill_completed_season.py $year --league 323196
done
```

### Important Notes:

**ESPN Data Retention Policy:**

**Boxscores:**
- ESPN maintains detailed boxscore data for only **6 years** (5 past + current season)
- Currently (2025 season): Detailed boxscores available for 2019-2025
- Next season (2026): Detailed boxscores available for 2020-2026 (2019 will be purged)
- Historical seasons (2011-2018): Only draft and h2h data available

**Transactions:**
- Available for 2019+ seasons (may require authentication even for public leagues)
- Historical seasons (< 2019): Endpoints exist but return no transaction data (ESPN has purged historical records)
- Do NOT follow the same strict 6-year retention window as boxscores
- Availability decreases significantly for older seasons

**Preservation Strategy:**
Always extract and save the oldest available year before the new season begins:
- **2025 season**: Ensure 2019 data is locked and saved (will be purged in 2026)
- **2026 season**: Ensure 2020 data is locked and saved (will be purged in 2027)
- And so on...

