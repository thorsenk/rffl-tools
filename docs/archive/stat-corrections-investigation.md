# Stat Corrections API Investigation

## Goal
Find the ESPN API endpoint that provides stat corrections data for each season/week.

## Web URL Reference
The user provided this web URL:
- https://fantasy.espn.com/football/statcorrections?leagueId=323196&scoringPeriodId=15

This suggests stat corrections are:
- Per-week (scoringPeriodId parameter)
- Per-league (leagueId parameter)
- Available via a `/statcorrections` endpoint pattern

## API Endpoint Patterns to Test

### Pattern 1: View Parameter
```
/seasons/{year}/segments/0/leagues/{leagueId}?scoringPeriodId={week}&view=mStatCorrections
```

### Pattern 2: Separate Endpoint
```
/seasons/{year}/segments/0/leagues/{leagueId}/statcorrections?scoringPeriodId={week}
```

### Pattern 3: Embedded in Matchup Data
Stat corrections might be embedded in matchup/roster data when fetched with specific views.

## Testing Strategy

1. Test `mStatCorrections` view parameter
2. Test separate `/statcorrections` endpoint
3. Check matchup/roster data for correction fields
4. Test historical seasons (2019-2025)
5. Document response structure

## Expected Data Structure

Stat corrections typically include:
- Player ID
- Week/Scoring Period
- Stat ID that was corrected
- Original value
- Corrected value
- Points impact
- Team affected
- Date of correction

## Next Steps

1. Test all endpoint patterns
2. Document successful endpoint
3. Create extraction function
4. Add CLI command
5. Integrate into season export workflow

