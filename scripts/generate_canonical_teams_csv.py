#!/usr/bin/env python3
"""Generate canonical_teams.csv from Python registry (RFFL_REG_TEAMS_001).

This script generates the CSV file from the Python registry Source of Truth
for backward compatibility and external tooling that may depend on the CSV format.

Usage:
    python scripts/generate_canonical_teams_csv.py [--output PATH]
"""

import argparse
import csv
import sys
from pathlib import Path

# Add src to path to import registry
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rffl.core.registry import REGISTRY


def generate_csv(output_path: Path) -> None:
    """Generate canonical_teams.csv from Python registry."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "season_year",
                "team_code",
                "team_full_name",
                "is_co_owned",
                "owner_code_1",
                "owner_code_2",
            ],
        )
        writer.writeheader()
        
        for team in sorted(REGISTRY, key=lambda t: (t.season_year, t.team_code)):
            writer.writerow({
                "season_year": team.season_year,
                "team_code": team.team_code,
                "team_full_name": team.team_full_name,
                "is_co_owned": "Yes" if team.is_co_owned else "No",
                "owner_code_1": team.owner_code_1,
                "owner_code_2": team.owner_code_2 or "",
            })
    
    print(f"✅ Generated {output_path} with {len(REGISTRY)} records")


def main():
    parser = argparse.ArgumentParser(
        description="Generate canonical_teams.csv from Python registry"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV path (default: data/teams/canonical_teams.csv)",
    )
    args = parser.parse_args()
    
    if args.output:
        output_path = args.output
    else:
        # Find repo root
        repo_root = Path(__file__).parent.parent
        output_path = repo_root / "data" / "teams" / "canonical_teams.csv"
    
    generate_csv(output_path)


if __name__ == "__main__":
    main()

