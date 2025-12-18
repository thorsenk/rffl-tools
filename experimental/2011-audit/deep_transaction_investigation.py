#!/usr/bin/env python3
"""Deep investigation into transaction data extraction for 2019-2025 seasons."""

import os
import json
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ Missing 'requests' module. Install with: pip install requests")
    sys.exit(1)

ESPN_S2 = os.getenv("ESPN_S2")
SWID = os.getenv("SWID")

if not ESPN_S2 or not SWID:
    print("❌ Missing ESPN_S2 or SWID credentials")
    print("Set them with: export ESPN_S2='...' && export SWID='...'")
    exit(1)

cookies = {"espn_s2": ESPN_S2, "SWID": SWID}
base_url = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"

# Test multiple seasons and view combinations
seasons_to_test = [2019, 2020, 2024]

view_combinations = [
    "view=mTransactions2&view=mTeam",
    "view=mTransactions&view=mTeam",
    "view=kona_league_communication",
    "view=mRoster&view=mTeam&view=mTransactions2",
    "view=mTeam&view=mSettings&view=mStatus&view=mTransactions2",
    "view=mPendingTransactions&view=mTeam",
    "view=mTransactions2",
    "view=mTransactions",
    "view=mTeam&view=mTransactions2&view=mTransactions",
    "view=mTransactions2&view=mTransactions&view=mTeam",
]

print("=" * 80)
print("DEEP TRANSACTION INVESTIGATION")
print("=" * 80)

for year in seasons_to_test:
    print(f"\n{'='*80}")
    print(f"SEASON: {year}")
    print(f"{'='*80}\n")
    
    best_result = None
    best_trans_count = 0
    
    for views in view_combinations:
        url = f"{base_url}/seasons/{year}/segments/0/leagues/323196?{views}"
        
        try:
            r = requests.get(url, cookies=cookies, timeout=10)
            if r.status_code == 200:
                data = r.json()
                
                # Check for transactions in various locations
                trans_keys = ['transactions', 'recentTransactions', 'activity', 'recentActivity']
                found_keys = []
                trans_count = 0
                trans_data = None
                
                # Check top level
                for key in trans_keys:
                    if key in data:
                        val = data[key]
                        if isinstance(val, list):
                            trans_count += len(val)
                            found_keys.append(f"{key}({len(val)})")
                            if len(val) > 0:
                                trans_data = val
                        elif isinstance(val, dict):
                            found_keys.append(f"{key}(dict)")
                            # Check if dict contains arrays
                            for subkey in val:
                                if isinstance(val[subkey], list):
                                    trans_count += len(val[subkey])
                                    found_keys.append(f"{key}.{subkey}({len(val[subkey])})")
                
                # Check nested in teams
                if 'teams' in data:
                    for i, team in enumerate(data['teams']):
                        for key in trans_keys:
                            if key in team:
                                val = team[key]
                                if isinstance(val, list):
                                    trans_count += len(val)
                                    found_keys.append(f"teams[{i}].{key}({len(val)})")
                
                # Check all keys for transaction-related patterns
                all_keys = list(data.keys())
                trans_related = [k for k in all_keys if 'trans' in k.lower() or 'activity' in k.lower() or 'waiver' in k.lower()]
                
                if trans_count > 0 or found_keys or trans_related:
                    status = "✅" if trans_count > 0 else "⚠️"
                    print(f"{status} {views[:60]:<60} | Transactions: {trans_count} | Keys: {', '.join(found_keys[:3])}")
                    
                    if trans_count > best_trans_count:
                        best_trans_count = trans_count
                        best_result = {
                            'views': views,
                            'url': url,
                            'data': data,
                            'transactions': trans_data,
                            'found_keys': found_keys,
                            'trans_related_keys': trans_related,
                        }
                    
                    # Show sample transaction structure if found
                    if trans_data and len(trans_data) > 0:
                        sample = trans_data[0]
                        print(f"   Sample transaction keys: {list(sample.keys())[:20]}")
                        print(f"   Sample transaction: {json.dumps(sample, indent=2, default=str)[:500]}")
                        print()
            else:
                print(f"❌ {views[:60]:<60} | Status {r.status_code}")
        except Exception as e:
            print(f"❌ {views[:60]:<60} | Error: {str(e)[:50]}")
    
    # Save best result for detailed analysis
    if best_result and best_result['transactions']:
        output_file = Path(__file__).parent / f"transactions_{year}_detailed.json"
        with open(output_file, 'w') as f:
            json.dump({
                'year': year,
                'views': best_result['views'],
                'transaction_count': best_trans_count,
                'sample_transaction': best_result['transactions'][0] if best_result['transactions'] else None,
                'all_transactions': best_result['transactions'][:10],  # First 10 for analysis
            }, f, indent=2, default=str)
        print(f"\n💾 Saved detailed transaction data to {output_file}")
        print(f"   Found {best_trans_count} transactions using: {best_result['views']}")
    elif best_result:
        # Save response structure even if no transactions found
        output_file = Path(__file__).parent / f"response_{year}_structure.json"
        with open(output_file, 'w') as f:
            json.dump({
                'year': year,
                'views': best_result['views'],
                'top_level_keys': list(best_result['data'].keys()),
                'trans_related_keys': best_result['trans_related_keys'],
                'sample_data_structure': {k: type(v).__name__ for k, v in list(best_result['data'].items())[:20]},
            }, f, indent=2, default=str)
        print(f"\n💾 Saved response structure to {output_file}")
        print(f"   No transactions found, but response structure saved for analysis")

print("\n" + "=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
