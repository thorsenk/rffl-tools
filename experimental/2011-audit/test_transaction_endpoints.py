#!/usr/bin/env python3
"""Test transaction endpoints for different seasons to understand availability."""

import os
import sys
import json
from pathlib import Path

# Add src to path to use rffl modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rffl.core.api import ESPNCredentials
from rffl.core.transactions import export_transactions

ESPN_S2 = os.getenv("ESPN_S2")
SWID = os.getenv("SWID")

if not ESPN_S2 or not SWID:
    print("❌ Missing ESPN_S2 or SWID credentials")
    sys.exit(1)

credentials = ESPNCredentials(espn_s2=ESPN_S2, swid=SWID)
output_dir = Path(__file__).parent

seasons_to_test = [2011, 2018, 2019, 2020, 2024]

print("Testing transaction export for multiple seasons...\n")

results = {}
for year in seasons_to_test:
    print(f"Testing {year}...", end=" ")
    output_file = output_dir / f"transactions_{year}_test.csv"
    try:
        path = export_transactions(
            league_id=323196,
            year=year,
            output_path=output_file,
            credentials=credentials,
            public_only=False,
        )
        
        # Count lines in CSV
        with open(path) as f:
            lines = len(f.readlines())
        
        results[year] = {
            "success": True,
            "file": str(path),
            "rows": lines - 1,  # Subtract header
        }
        print(f"✅ {results[year]['rows']} transactions")
    except Exception as e:
        results[year] = {
            "success": False,
            "error": str(e),
        }
        print(f"❌ {str(e)[:60]}")

print("\n=== Summary ===")
for year, result in results.items():
    if result["success"]:
        print(f"{year}: ✅ {result['rows']} transactions")
    else:
        print(f"{year}: ❌ {result['error'][:80]}")

