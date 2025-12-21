"""
Analyze raw JSON to discover return TD stat IDs.
"""
import json
from pathlib import Path


def find_player_stat_ids(json_file: str, player_name: str = "Shaheed"):
    """Find stat IDs for a specific player."""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Search through rosters
    teams = data.get('teams', [])
    found_players = []
    
    for team in teams:
        roster = team.get('roster', {}).get('entries', [])
        for entry in roster:
            player = entry.get('playerPoolEntry', {}).get('player', {})
            full_name = player.get('fullName', '')
            
            if player_name.lower() in full_name.lower():
                stats = player.get('stats', [])
                for stat_entry in stats:
                    if isinstance(stat_entry, dict):
                        applied_stats = stat_entry.get('appliedStats', {})
                        scoring_period = stat_entry.get('scoringPeriodId')
                        stat_source = stat_entry.get('statSourceId')  # 0 = actual, 1 = projected
                        
                        if applied_stats and stat_source == 0:  # Actual stats only
                            found_players.append({
                                'name': full_name,
                                'proTeamId': player.get('proTeamId'),
                                'scoringPeriodId': scoring_period,
                                'appliedStats': applied_stats,
                                'appliedTotal': stat_entry.get('appliedTotal', 0),
                                'lineupSlotId': entry.get('lineupSlotId'),
                            })
    
    return found_players


def find_dst_stat_ids(json_file: str, nfl_team_id: int = None):
    """Find stat IDs for D/ST units."""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    teams = data.get('teams', [])
    found_dsts = []
    
    for team in teams:
        roster = team.get('roster', {}).get('entries', [])
        for entry in roster:
            player = entry.get('playerPoolEntry', {}).get('player', {})
            default_pos = player.get('defaultPositionId')
            
            # D/ST has defaultPositionId == 16
            if default_pos == 16:
                pro_team_id = player.get('proTeamId')
                if nfl_team_id and pro_team_id != nfl_team_id:
                    continue
                
                stats = player.get('stats', [])
                for stat_entry in stats:
                    if isinstance(stat_entry, dict):
                        applied_stats = stat_entry.get('appliedStats', {})
                        scoring_period = stat_entry.get('scoringPeriodId')
                        stat_source = stat_entry.get('statSourceId')
                        
                        if applied_stats and stat_source == 0:
                            found_dsts.append({
                                'name': player.get('fullName', ''),
                                'proTeamId': pro_team_id,
                                'scoringPeriodId': scoring_period,
                                'appliedStats': applied_stats,
                                'appliedTotal': stat_entry.get('appliedTotal', 0),
                            })
    
    return found_dsts


def identify_return_td_stat_ids(player_stats: dict, dst_stats: dict):
    """
    Identify which stat IDs likely represent return TDs.
    
    Logic:
    - Return TDs are worth 6 points
    - Player stat should have value >= 1 (or 6 if points-based)
    - D/ST stat should match (same or different ID)
    """
    # Look for stat IDs with value >= 1 (or exactly 6 if points-based)
    player_candidates = {
        stat_id: value 
        for stat_id, value in player_stats.items() 
        if value >= 1.0 or value == 6.0
    }
    
    dst_candidates = {
        stat_id: value 
        for stat_id, value in dst_stats.items() 
        if value >= 1.0 or value == 6.0
    }
    
    return {
        'player_candidates': player_candidates,
        'dst_candidates': dst_candidates,
    }


if __name__ == "__main__":
    # Check if we have 2025 Week 16 data
    json_2025 = Path("raw_boxscore_s2025_w16.json")
    json_2024 = Path("raw_boxscore_s2024_w16.json")
    
    # Try 2025 first (where Shaheed actually scored)
    json_file = json_2025 if json_2025.exists() else json_2024
    
    if not json_file.exists():
        print(f"Error: {json_file} not found. Run discover_stat_ids.py first.")
        exit(1)
    
    print(f"Analyzing {json_file}\n")
    
    # Find Shaheed (known return TD player)
    print("=== Searching for Rashid Shaheed ===")
    shaheed_entries = find_player_stat_ids(str(json_file), "Shaheed")
    
    if shaheed_entries:
        for entry in shaheed_entries:
            print(f"\nFound: {entry['name']}")
            print(f"  Pro Team ID: {entry['proTeamId']}")
            print(f"  Scoring Period: {entry['scoringPeriodId']}")
            print(f"  Total Points: {entry['appliedTotal']}")
            print(f"  Lineup Slot: {entry['lineupSlotId']}")
            print(f"  Applied Stats:")
            for stat_id, value in sorted(entry['appliedStats'].items(), key=lambda x: float(x[0])):
                if value > 0:
                    print(f"    Stat ID {stat_id}: {value}")
    else:
        print("Shaheed not found. Trying Week 16, 2025...")
        # Try fetching 2025 data
        from rffl.live.scores import LiveScoreClient
        client = LiveScoreClient(league_id=323196, season=2025)
        data_2025 = client.fetch_scoreboard(scoring_period=16, include_boxscore=True)
        json_2025.write_text(json.dumps(data_2025, indent=2))
        print(f"Fetched 2025 Week 16 data to {json_2025}")
        
        shaheed_entries = find_player_stat_ids(str(json_2025), "Shaheed")
        if shaheed_entries:
            for entry in shaheed_entries:
                print(f"\nFound: {entry['name']}")
                print(f"  Pro Team ID: {entry['proTeamId']}")
                print(f"  Applied Stats:")
                for stat_id, value in sorted(entry['appliedStats'].items(), key=lambda x: float(x[0])):
                    if value > 0:
                        print(f"    Stat ID {stat_id}: {value}")
    
    # Find Seattle D/ST (proTeamId = 26 for SEA)
    print("\n=== Searching for Seattle D/ST ===")
    seattle_dst = find_dst_stat_ids(str(json_file), nfl_team_id=26)
    
    if not seattle_dst and json_2025.exists():
        seattle_dst = find_dst_stat_ids(str(json_2025), nfl_team_id=26)
    
    if seattle_dst:
        for entry in seattle_dst:
            print(f"\nFound: {entry['name']}")
            print(f"  Pro Team ID: {entry['proTeamId']}")
            print(f"  Scoring Period: {entry['scoringPeriodId']}")
            print(f"  Total Points: {entry['appliedTotal']}")
            print(f"  Applied Stats:")
            for stat_id, value in sorted(entry['appliedStats'].items(), key=lambda x: float(x[0])):
                if value > 0:
                    print(f"    Stat ID {stat_id}: {value}")
    else:
        print("Seattle D/ST not found")

