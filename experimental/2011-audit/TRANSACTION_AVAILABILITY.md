# Transaction Data Availability Analysis

## Question
Are detailed transactions available for 2019-2025 but restricted for 2011-2018?

## Testing Results

### 2011 Season
- **Endpoint**: `leagueHistory/{id}?seasonId=2011&view=mTransactions`
- **Status**: ✅ Endpoint accessible (200 OK)
- **Transaction Data**: ❌ No transaction arrays found in response
- **Response Structure**: Contains teams, schedule, settings, draft, but NO transactions key
- **Conclusion**: Transaction endpoint exists but returns no transaction data for 2011

### 2019-2024 Seasons  
- **Endpoint**: `/seasons/{year}/segments/0/leagues/{id}?view=mTransactions2&view=mTeam`
- **Status**: ✅ Endpoint accessible (200 OK) with authentication
- **Transaction Data**: ⚠️ Export succeeds but returns 0 transactions
- **Possible Reasons**:
  1. Transactions may be stored differently (different view parameters needed)
  2. Transactions may require different authentication scope
  3. Transactions may be in a different location in the response
  4. League may have had no transactions (unlikely for full seasons)

## Key Findings

### Historical Seasons (2011-2018)
- Transaction endpoint (`leagueHistory` with `mTransactions` view) is **accessible**
- However, **no transaction data** is returned in the response
- The endpoint returns successfully but the `transactions` key is missing from the JSON

### Recent Seasons (2019-2025)
- Transaction endpoint (modern API) is **accessible** with authentication
- Export function succeeds (no errors)
- However, **0 transactions** are extracted from the response
- This suggests either:
  - Transactions are in a different location/structure than expected
  - Different view parameters are needed
  - Transactions require additional authentication or permissions

## Comparison with Boxscores

**Boxscores**:
- 2011-2018: ❌ Not available (purged by ESPN)
- 2019-2025: ✅ Available (detailed player-level data)

**Transactions**:
- 2011-2018: ⚠️ Endpoint accessible but returns no data
- 2019-2025: ⚠️ Endpoint accessible but extraction returns 0 transactions

## Conclusion

**Answer**: The restriction appears to apply differently than boxscores:

1. **2011-2018**: Transaction endpoint exists but returns empty/no transaction data
2. **2019-2025**: Transaction endpoint exists and is accessible, but current extraction logic returns 0 transactions

**This suggests**:
- Transactions may require different view parameters or endpoints
- Transactions may be stored/accessed differently than the current code expects
- Further investigation needed to find the correct way to extract transaction data

## Next Steps

1. Investigate alternative view parameters for transaction extraction
2. Check if transactions are nested in team data or other structures
3. Compare with known working transaction exports (if any exist)
4. Test with different authentication scopes or endpoints

