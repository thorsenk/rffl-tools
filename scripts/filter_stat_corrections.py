#!/usr/bin/env python3
"""Filter stat corrections CSV to only include RFFL league players/D/ST and add team_code column."""

import sys
from pathlib import Path

import pandas as pd

# Script runs standalone - no imports from rffl package needed


def parse_player_name(name: str) -> tuple[str, str | None]:
    """
    Parse player name from stat corrections format.
    
    Format: "Player NameTeamPos" or "Team D/STTeamD/ST"
    Examples:
      - "Michael Penix Jr.AtlQBIR" -> ("Michael Penix Jr.", "Atl")
      - "Falcons D/STAtlD/ST" -> ("Falcons D/ST", "Atl")
      - "Keenan AllenLACWR" -> ("Keenan Allen", "LAC")
    
    Returns:
        Tuple of (clean_name, team_abbrev)
    """
    if not name:
        return ("", None)
    
    # Handle D/ST names
    if " D/ST" in name:
        # Pattern: "TeamName D/STTeamAbbrevD/ST"
        # Extract team name before " D/ST"
        parts = name.split(" D/ST")
        if len(parts) >= 2:
            team_name = parts[0].strip()
            # Try to extract team abbrev from second part
            remainder = parts[1].strip()
            # Remove "D/ST" suffix if present
            if remainder.endswith("D/ST"):
                team_abbrev = remainder.replace("D/ST", "").strip()
            else:
                team_abbrev = remainder[:3] if len(remainder) >= 3 else None
            return (f"{team_name} D/ST", team_abbrev)
        return (name, None)
    
    # Handle regular player names
    # Pattern: "NameTeamPos" - need to find where name ends and team starts
    # Team abbreviations are typically 2-3 uppercase letters
    import re
    
    # Try to find team abbreviation pattern (2-3 uppercase letters)
    # followed by position (QB, RB, WR, TE, K, D/ST, etc.)
    match = re.search(r'([A-Z]{2,3})(QB|RB|WR|TE|K|D/ST|IR|Q)', name)
    if match:
        team_abbrev = match.group(1)
        # Extract name part before team abbrev
        name_end = name.rfind(team_abbrev)
        if name_end > 0:
            clean_name = name[:name_end].strip()
            return (clean_name, team_abbrev)
    
    # Fallback: return as-is
    return (name.strip(), None)


def normalize_player_name(name: str) -> str:
    """Normalize player name for matching."""
    if not name:
        return ""
    clean_name, _ = parse_player_name(name)
    # Remove extra whitespace
    return " ".join(clean_name.split())


def normalize_dst_name(name: str) -> str:
    """Normalize D/ST name for matching."""
    if not name:
        return ""
    # Handle "Vikings D/ST" -> "Vikings D/ST" or "MIN D/ST"
    name = name.strip()
    # Remove " D/ST" suffix for matching
    if " D/ST" in name:
        return name.replace(" D/ST", "").strip()
    return name


def extract_dst_team(dst_name: str) -> str | None:
    """Extract NFL team abbreviation from D/ST name."""
    # Handle patterns like "Vikings D/ST" or "MIN D/ST"
    if not dst_name:
        return None
    
    # Map common team names to abbreviations
    team_map = {
        "Falcons": "Atl", "Atlanta": "Atl",
        "Ravens": "Bal", "Baltimore": "Bal",
        "Bills": "Buf", "Buffalo": "Buf",
        "Panthers": "Car", "Carolina": "Car",
        "Bears": "Chi", "Chicago": "Chi",
        "Bengals": "Cin", "Cincinnati": "Cin",
        "Browns": "Cle", "Cleveland": "Cle",
        "Cowboys": "Dal", "Dallas": "Dal",
        "Broncos": "Den", "Denver": "Den",
        "Lions": "Det", "Detroit": "Det",
        "Packers": "GB", "Green Bay": "GB",
        "Texans": "Hou", "Houston": "Hou",
        "Colts": "Ind", "Indianapolis": "Ind",
        "Jaguars": "Jax", "Jacksonville": "Jax",
        "Chiefs": "KC", "Kansas City": "KC",
        "Raiders": "LV", "Las Vegas": "LV",
        "Chargers": "LAC", "LA Chargers": "LAC",
        "Rams": "LAR", "LA Rams": "LAR",
        "Dolphins": "Mia", "Miami": "Mia",
        "Vikings": "Min", "Minnesota": "Min",
        "Patriots": "NE", "New England": "NE",
        "Saints": "NO", "New Orleans": "NO",
        "Giants": "NYG", "New York Giants": "NYG",
        "Jets": "NYJ", "New York Jets": "NYJ",
        "Eagles": "Phi", "Philadelphia": "Phi",
        "Steelers": "Pit", "Pittsburgh": "Pit",
        "49ers": "SF", "San Francisco": "SF",
        "Seahawks": "Sea", "Seattle": "Sea",
        "Buccaneers": "TB", "Tampa Bay": "TB",
        "Titans": "Ten", "Tennessee": "Ten",
        "Commanders": "Wsh", "Washington": "Wsh",
    }
    
    # Try to match team name
    for team_name, abbrev in team_map.items():
        if team_name.lower() in dst_name.lower():
            return abbrev
    
    # If it's already an abbreviation (3 chars), return as-is
    if len(dst_name) <= 3:
        return dst_name
    
    return None


def filter_stat_corrections(
    stat_corrections_path: Path,
    boxscores_path: Path,
    output_path: Path | None = None,
) -> pd.DataFrame:
    """
    Filter stat corrections to only include RFFL league players/D/ST.
    
    Args:
        stat_corrections_path: Path to stat_corrections.csv
        boxscores_path: Path to boxscores.csv for the same season
        output_path: Optional output path (defaults to overwriting input)
        
    Returns:
        Filtered DataFrame with rffl_team_code column added
    """
    # Read CSV files
    print(f"Reading stat corrections from: {stat_corrections_path}")
    corrections_df = pd.read_csv(stat_corrections_path)
    
    print(f"Reading boxscores from: {boxscores_path}")
    boxscores_df = pd.read_csv(boxscores_path)
    
    # Get unique players/D/ST from boxscores (starters and bench)
    # Filter to only starters and bench (exclude any other slot_types)
    roster_df = boxscores_df[
        boxscores_df["slot_type"].isin(["starters", "bench"])
    ].copy()
    
    # Create lookup: (week, player_name) -> team_code
    # For players
    player_lookup = {}
    for _, row in roster_df.iterrows():
        week = int(row["week"])
        player_name = normalize_player_name(str(row["player_name"]))
        team_code = str(row["team_code"])
        if player_name:
            player_lookup[(week, player_name)] = team_code
    
    # Create lookup for D/ST: (week, nfl_team) -> team_code
    dst_lookup = {}
    for _, row in roster_df.iterrows():
        if row["position"] == "D/ST":
            week = int(row["week"])
            nfl_team = str(row["nfl_team"]) if pd.notna(row["nfl_team"]) else ""
            team_code = str(row["team_code"])
            player_name = normalize_player_name(str(row["player_name"]))
            if nfl_team:
                dst_lookup[(week, nfl_team)] = team_code
            # Also add by player_name (e.g., "Vikings D/ST")
            if player_name:
                dst_lookup[(week, player_name)] = team_code
    
    # Add rffl_team_code column
    rffl_team_codes = []
    matched_count = 0
    
    for _, row in corrections_df.iterrows():
        week = int(row["week"])
        player_name = str(row["player_name"]) if pd.notna(row["player_name"]) else ""
        team_code_espn = str(row["team_code"]) if pd.notna(row["team_code"]) else ""
        
        # Try to match as player first
        normalized_name = normalize_player_name(player_name)
        team_code = player_lookup.get((week, normalized_name))
        
        # If not found and it looks like D/ST, try D/ST matching
        if not team_code and ("D/ST" in player_name or team_code_espn.endswith("D/ST")):
            # Try matching by D/ST name
            dst_name = normalize_dst_name(player_name)
            team_code = dst_lookup.get((week, player_name))
            
            # Try extracting NFL team from D/ST name and matching
            if not team_code:
                nfl_team = extract_dst_team(dst_name)
                if nfl_team:
                    team_code = dst_lookup.get((week, nfl_team))
            
            # Try matching by ESPN team_code (e.g., "AtlD/ST" -> "Atl")
            if not team_code and team_code_espn:
                if team_code_espn.endswith("D/ST"):
                    nfl_abbrev = team_code_espn.replace("D/ST", "")
                    team_code = dst_lookup.get((week, nfl_abbrev))
        
        if team_code:
            matched_count += 1
            rffl_team_codes.append(team_code)
        else:
            rffl_team_codes.append("")
    
    corrections_df["rffl_team_code"] = rffl_team_codes
    
    # Filter to only rows with rffl_team_code (i.e., matched to RFFL roster)
    filtered_df = corrections_df[corrections_df["rffl_team_code"] != ""].copy()
    
    print(f"\nFiltering results:")
    print(f"  Total corrections: {len(corrections_df)}")
    print(f"  Matched to RFFL teams: {matched_count}")
    print(f"  Filtered (RFFL only): {len(filtered_df)}")
    print(f"  Removed (not in RFFL): {len(corrections_df) - len(filtered_df)}")
    
    # Write output
    output_path = output_path or stat_corrections_path
    filtered_df.to_csv(output_path, index=False)
    print(f"\n✅ Wrote filtered stat corrections to: {output_path}")
    
    return filtered_df


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Filter stat corrections CSV to RFFL league players only"
    )
    parser.add_argument(
        "year",
        type=int,
        help="Season year (e.g., 2024)",
    )
    parser.add_argument(
        "--stat-corrections",
        type=Path,
        help="Path to stat_corrections.csv (default: data/seasons/{YEAR}/stat_corrections.csv)",
    )
    parser.add_argument(
        "--boxscores",
        type=Path,
        help="Path to boxscores.csv (default: data/seasons/{YEAR}/boxscores.csv)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path (default: overwrites input file)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Repository root (default: parent of scripts/)",
    )
    
    args = parser.parse_args()
    
    # Determine paths
    repo_root = args.repo_root or Path(__file__).parent.parent
    year = args.year
    
    stat_corrections_path = (
        args.stat_corrections
        or repo_root / "data" / "seasons" / str(year) / "stat_corrections.csv"
    )
    boxscores_path = (
        args.boxscores
        or repo_root / "data" / "seasons" / str(year) / "boxscores.csv"
    )
    
    if not stat_corrections_path.exists():
        print(f"❌ Error: Stat corrections file not found: {stat_corrections_path}")
        sys.exit(1)
    
    if not boxscores_path.exists():
        print(f"❌ Error: Boxscores file not found: {boxscores_path}")
        sys.exit(1)
    
    filter_stat_corrections(
        stat_corrections_path=stat_corrections_path,
        boxscores_path=boxscores_path,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()

