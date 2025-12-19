# Stat Corrections API Mapping

## ⚠️ Important Understanding

**Stat corrections are already baked into the scores/stats we extract.**

When we extract boxscores and player stats from the ESPN API:
- ✅ `rs_actual_pf` (actual fantasy points) already includes all stat corrections
- ✅ Player stats (`appliedStats`, `appliedTotal`) already reflect corrected values
- ✅ Team totals already include corrected scores

**Therefore**: We do NOT need to extract stat corrections separately for score calculation purposes. The corrections are already reflected in our extracted data.

## Web URL Reference
- **Web Page**: https://fantasy.espn.com/football/statcorrections?leagueId=323196&scoringPeriodId=15
- **Parameters**: `leagueId` and `scoringPeriodId` (week)
- **Purpose**: Informational/audit only - shows what corrections were made, but scores already reflect these corrections

## API Endpoint Investigation Results

### ✅ Pattern 1: View Parameter (Accessible but No Direct Data)
```
GET /seasons/{year}/segments/0/leagues/{leagueId}?scoringPeriodId={week}&view=mStatCorrections
```
- **Base URL**: `https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl`
- **Status**: ✅ 200 OK (endpoint accessible)
- **Response**: Returns league data but **no explicit `statCorrections` key found**
- **Tested combinations**:
  - `view=mStatCorrections` alone
  - `view=mStatCorrections&view=mMatchup`
  - `view=mStatCorrections&view=mRoster`
  - `view=mStatCorrections&view=mMatchup&view=mRoster&view=mTeam`
- **Result**: All return league data but no stat corrections array

### ❌ Pattern 2: Separate Endpoint (Not Found)
```
GET /seasons/{year}/segments/0/leagues/{leagueId}/statcorrections?scoringPeriodId={week}
```
- **Status**: ❌ 404 Not Found
- **Variations tested**:
  - `/statcorrections`
  - `/statCorrections`
  - `/stat-corrections`
  - `/corrections`
- **Result**: None of these patterns work

### ⚠️ Pattern 3: Web Domain (Redirects)
```
GET https://fantasy.espn.com/apis/v3/games/ffl/.../statcorrections
```
- **Status**: ⚠️ Redirects (likely requires web session/cookies)

## Findings Summary

### What We Know
1. ✅ `mStatCorrections` view parameter exists and is accessible
2. ❌ No explicit `statCorrections` key in API response
3. ❌ No separate `/statcorrections` endpoint found
4. ✅ Web page exists at `/football/statcorrections` (HTML page)

### Hypothesis
Stat corrections may be:
1. **Only available via web scraping** - The web URL suggests HTML table exists
2. **Embedded in player stats** - Need to compare stats at different times
3. **Calculated from differences** - Compare boxscores before/after corrections
4. **In a different API version** - May require different endpoint structure

## Implementation Decision

**No separate stat corrections extraction needed** - corrections are already in our data.

However, if you want to track corrections for **audit/historical purposes** (to see what corrections were made, when, and by how much), we can implement extraction:

### Optional: Audit/Historical Tracking Only

If you want to track corrections for audit purposes (not for score calculation):

**Approach**: Web Scraping
- Scrape: `https://fantasy.espn.com/football/statcorrections?leagueId={id}&scoringPeriodId={week}`
- Parse HTML table to extract correction history
- Export to CSV for audit trail

**Use Case**: 
- Historical record of what corrections were made
- Understanding when corrections happened
- Audit trail for league disputes

**Note**: This is purely informational - scores already reflect corrections.

## API Endpoint Structure

### For Recent Seasons (2019-2025)
```
Base: https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl
Endpoint: /seasons/{year}/segments/0/leagues/{leagueId}
Required Parameters:
  - scoringPeriodId={week} (1-18)
Optional View Parameters:
  - view=mStatCorrections (exists but unclear if it helps)
  - view=mMatchup (get matchup data)
  - view=mRoster (get roster/player data)
  - view=mTeam (get team data)
```

### For Historical Seasons (2011-2018)
```
Base: https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl
Endpoint: /leagueHistory/{leagueId}
Parameters:
  - seasonId={year}
  - scoringPeriodId={week} (if supported)
  - view=mStatCorrections (if supported)
```

## Per-Season Extraction Pattern

### Recent Seasons (2019-2025)
```python
# Iterate through all weeks (1-18)
for week in range(1, 19):
    url = f"{base_url}/seasons/{year}/segments/0/leagues/{league_id}?scoringPeriodId={week}&view=mStatCorrections"
    # Fetch and extract corrections
```

### Historical Seasons (2011-2018)
```python
# Use leagueHistory endpoint
url = f"{base_url}/leagueHistory/{league_id}?seasonId={year}&scoringPeriodId={week}&view=mStatCorrections"
# May not be available for old seasons
```

## Next Steps

1. **Test web scraping approach** - Parse HTML from `/statcorrections` page
2. **Investigate player stats comparison** - Compare stats before/after corrections
3. **Test multiple weeks** - See if corrections appear in certain weeks only
4. **Check for correction timestamps** - Look for date fields indicating when corrections were made
5. **Test historical seasons** - Verify if corrections available for 2019-2025

## Implementation Plan (Optional - Audit Only)

If you want to track corrections for audit purposes:

1. **Create module**: `src/rffl/core/stat_corrections.py` (optional)
2. **Add CLI command**: `rffl core stat-corrections --year {year} [--week {week}]` (optional)
3. **Support per-week extraction** (similar to transactions)
4. **Export format**: CSV file `stat_corrections.csv` (optional)
5. **Integration**: Add to `fill_completed_season.py` script (optional)
6. **Documentation**: Update season template docs (optional)

**Note**: This is optional since corrections are already in scores. Only implement if you want audit/historical tracking.

## File Structure (Optional)

```
data/seasons/{YEAR}/
├── stat_corrections.csv  # Optional: Audit trail of corrections (2019+)
```

## CSV Schema (Proposed - Optional)

```csv
season_year,week,player_id,player_name,team_id,team_code,stat_id,stat_name,original_value,corrected_value,points_impact,correction_date
```

**Purpose**: Audit/historical record only. Scores already reflect corrections.

## Testing Checklist

- [ ] Test web scraping approach for week 15, 2024
- [ ] Verify corrections data structure from HTML
- [ ] Test multiple weeks to ensure consistency
- [ ] Test historical seasons (2019-2025)
- [ ] Verify authentication requirements
- [ ] Create extraction function
- [ ] Add CLI command
- [ ] Integrate into season export workflow
