# Stat Corrections - Summary

## Implementation Status ✅

**Stat corrections extraction feature has been implemented** (December 2024)

### Feature Overview

The `rffl core stat-corrections` command extracts stat correction history from ESPN Fantasy Football for audit and historical tracking purposes.

**CLI Command**:
```bash
rffl core stat-corrections --year 2024 --week 15
```

**Output**: `data/seasons/{YEAR}/stat_corrections.csv`

### Key Understanding ✅

**Stat corrections are already baked into all scores and stats we extract.**

### What This Means

1. **Boxscores**: The `rs_actual_pf` (actual fantasy points) values already include all stat corrections
2. **Player Stats**: The `appliedStats` and `appliedTotal` values already reflect corrected stats
3. **Team Totals**: Team scores already include all corrections

### Data Sources That Include Corrections

- ✅ `boxscores.csv` - Actual PF already corrected
- ✅ `boxscores_normalized.csv` - Normalized data includes corrections
- ✅ `teamweek_unified.csv` - Aggregated data includes corrections
- ✅ All player-level stats from ESPN API

### What We DON'T Need

- ❌ Separate stat corrections extraction for score calculation
- ❌ Comparing stats before/after corrections
- ❌ Calculating corrections from differences

### What We Extract (Audit Trail)

The stat corrections CSV provides:

- 📋 Correction history to see what was changed
- 📋 Track when corrections were made
- 📋 Record original vs corrected values for audit trail
- 📋 Filtered to RFFL league players/D/ST only (starters and bench)

**Note**: This is purely informational - scores already reflect corrections.

## Stat Corrections Web Page

- **URL**: `https://fantasy.espn.com/football/statcorrections?leagueId={id}&scoringPeriodId={week}`
- **Purpose**: Shows correction history (informational only)
- **Use Case**: Audit trail, understanding what corrections were made
- **Not Needed For**: Score calculation (scores already include corrections)

## Implementation Details

- **Module**: `src/rffl/core/stat_corrections.py`
- **Method**: Web scraping (requires authentication)
- **Output Format**: CSV with columns: season_year, week, player_name, team_code (RFFL), stat_name, original_value, corrected_value, points_impact, correction_date
- **Filtering**: Only includes players/D/ST rostered in RFFL league (starters or bench)

## Conclusion

**Feature implemented** ✅ - Stat corrections extraction is available via CLI for audit/historical tracking. The extracted data is filtered to RFFL league players only and provides a complete audit trail of all stat corrections made during the season.

