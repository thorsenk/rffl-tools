#!/usr/bin/env python3
"""Investigate ESPN stat corrections API endpoints."""

import os
import sys
import json
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ Missing 'requests' module")
    sys.exit(1)

ESPN_S2 = os.getenv("ESPN_S2")
SWID = os.getenv("SWID")

if not ESPN_S2 or not SWID:
    print("❌ Missing ESPN_S2 or SWID credentials")
    sys.exit(1)

cookies = {"espn_s2": ESPN_S2, "SWID": SWID}
base_url = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
league_id = 323196

# Test multiple endpoint patterns
endpoints = [
    # Pattern 1: View parameter
    f"{base_url}/seasons/2024/segments/0/leagues/{league_id}?scoringPeriodId=15&view=mStatCorrections",
    f"{base_url}/seasons/2024/segments/0/leagues/{league_id}?scoringPeriodId=15&view=mStatCorrections&view=mMatchup",
    f"{base_url}/seasons/2024/segments/0/leagues/{league_id}?scoringPeriodId=15&view=mStatCorrections&view=mRoster",
    
    # Pattern 2: Different base URL
    f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/2024/segments/0/leagues/{league_id}?scoringPeriodId=15&view=mStatCorrections",
    
    # Pattern 3: Separate endpoint (various patterns)
    f"{base_url}/seasons/2024/segments/0/leagues/{league_id}/statcorrections?scoringPeriodId=15",
    f"{base_url}/seasons/2024/segments/0/leagues/{league_id}/statCorrections?scoringPeriodId=15",
    f"{base_url}/seasons/2024/segments/0/leagues/{league_id}/corrections?scoringPeriodId=15",
]

print("=" * 80)
print("STAT CORRECTIONS API INVESTIGATION")
print("=" * 80)

results = {}

for url in endpoints:
    print(f"\n{'='*80}")
    print(f"Testing: {url.split('?')[0]}...")
    print(f"{'='*80}")
    
    try:
        r = requests.get(url, cookies=cookies, timeout=10, allow_redirects=True)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            try:
                data = r.json()
                
                # Search for stat correction data
                def find_corrections(obj, path="", depth=0, max_depth=4):
                    """Recursively find correction-related data"""
                    if depth > max_depth:
                        return []
                    
                    results = []
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            current_path = f"{path}.{key}" if path else key
                            key_lower = key.lower()
                            if any(term in key_lower for term in ['correction', 'adjustment', 'stat']):
                                results.append({
                                    'path': current_path,
                                    'type': type(value).__name__,
                                    'value_preview': str(value)[:100] if not isinstance(value, (dict, list)) else f"{type(value).__name__}"
                                })
                            if isinstance(value, (dict, list)) and depth < max_depth:
                                results.extend(find_corrections(value, current_path, depth+1, max_depth))
                    elif isinstance(obj, list) and depth < max_depth:
                        for i, item in enumerate(obj[:5]):  # Check first 5 items
                            results.extend(find_corrections(item, f"{path}[{i}]", depth+1, max_depth))
                    
                    return results
                
                corrections = find_corrections(data)
                
                if corrections:
                    print(f"✅ Found {len(corrections)} correction-related fields:")
                    for corr in corrections[:10]:
                        print(f"  {corr['path']}: {corr['type']}")
                else:
                    print("⚠️  No correction-related fields found")
                    print(f"Top-level keys: {list(data.keys())[:15]}")
                
                # Save response for analysis
                output_file = Path(__file__).parent / f"response_{url.split('/')[-1].split('?')[0]}.json"
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                print(f"💾 Saved response to {output_file.name}")
                
                results[url] = {
                    'status': 'success',
                    'corrections_found': len(corrections),
                    'top_keys': list(data.keys())[:10] if isinstance(data, dict) else []
                }
                
            except json.JSONDecodeError:
                print(f"⚠️  Response is not JSON")
                print(f"Content preview: {r.text[:200]}")
                results[url] = {'status': 'not_json', 'preview': r.text[:200]}
        else:
            print(f"❌ Status {r.status_code}")
            results[url] = {'status': 'error', 'code': r.status_code}
            
    except Exception as e:
        print(f"❌ Error: {e}")
        results[url] = {'status': 'exception', 'error': str(e)}

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

for url, result in results.items():
    status = result.get('status', 'unknown')
    if status == 'success':
        corrections = result.get('corrections_found', 0)
        print(f"✅ {url.split('?')[0]}: {corrections} correction fields found")
    else:
        print(f"❌ {url.split('?')[0]}: {status}")

