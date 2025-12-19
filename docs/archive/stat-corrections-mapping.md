# Stat Corrections API Mapping

## Web URL Reference
- https://fantasy.espn.com/football/statcorrections?leagueId=323196&scoringPeriodId=15

## API Endpoint Investigation

### Tested Patterns

1. **View Parameter Pattern**
   ```
   /seasons/{year}/segments/0/leagues/{leagueId}?scoringPeriodId={week}&view=mStatCorrections
   ```
   - Status: ✅ Endpoint accessible
   - Result: Returns league data but no explicit stat corrections key
   - Note: May be embedded in matchup/roster data

2. **Separate Endpoint Pattern (lm-api-reads)**
   ```
   /seasons/{year}/segments/0/leagues/{leagueId}/statcorrections?scoringPeriodId={week}
   ```
   - Status: ❌ 404 Not Found

3. **Separate Endpoint Pattern (fantasy.espn.com)**
   ```
   /seasons/{year}/segments/0/leagues/{leagueId}/statcorrections?scoringPeriodId={week}
   ```
   - Status: ⚠️ Redirects (may require different authentication)

## Findings

### Current Status
- `mStatCorrections` view parameter exists and is accessible
- No explicit `statCorrections` key found in response
- Stat corrections may be:
  1. Embedded in player stats (checking `appliedStats` vs `stats`)
  2. In a different endpoint structure
  3. Requiring different authentication method
  4. Available only through web scraping

### Next Steps

1. **Check Player Stats Structure**
   - Compare `appliedStats` vs `stats` in player entries
   - Look for `statSourceId` differences
   - Check for correction timestamps or flags

2. **Test Historical Seasons**
   - Verify if stat corrections are available for past seasons
   - Check if endpoint works for 2019-2025

3. **Investigate Web Scraping**
   - The web URL suggests HTML page exists
   - May need to scrape HTML table if API doesn't expose it

4. **Check espn_api Library**
   - See if library has stat corrections support
   - Check library source code for correction methods

## Data Structure Expectations

Stat corrections typically include:
- `playerId` - Player affected
- `week` / `scoringPeriodId` - Week of correction
- `statId` - Stat that was corrected
- `originalValue` - Original stat value
- `correctedValue` - New stat value
- `pointsImpact` - Fantasy points difference
- `teamId` - Team affected
- `correctionDate` - When correction was made
- `reason` - Reason for correction (optional)

## Implementation Plan

1. Create `stat_corrections.py` module in `src/rffl/core/`
2. Add CLI command `rffl core stat-corrections`
3. Support per-week extraction (similar to transactions)
4. Export to CSV format
5. Integrate into `fill_completed_season.py` script

