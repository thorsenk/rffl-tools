"""
ESPN Stat ID Discovery Script
Discover stat IDs for return TDs (player and D/ST)
"""
import json
from pathlib import Path

from rffl.core.api import ESPNClient, ESPNCredentials


def discover_stat_ids(season: int = 2024, week: int = 16):
    """
    Fetch boxscores and inspect player/D/ST stat structures.
    
    Goals:
    1. Find a player with a kick/punt return TD
    2. Extract their appliedStats dictionary
    3. Identify which stat ID represents the return TD
    4. Find the corresponding D/ST and verify matching stat
    """
    client = ESPNClient(league_id=323196, year=season)
    
    try:
        boxscores = client.get_boxscores(week=week)
    except Exception as e:
        print(f"Error fetching boxscores: {e}")
        return
    
    print(f"=== Season {season}, Week {week} ===\n")
    print(f"Found {len(boxscores)} matchups\n")
    
    for matchup in boxscores:
        for side in ['home', 'away']:
            lineup = getattr(matchup, f'{side}_lineup', [])
            team = getattr(matchup, f'{side}_team', None)
            
            team_name = team.team_name if team and hasattr(team, 'team_name') else 'Unknown'
            print(f"\n--- {team_name} ({side.upper()}) ---")
            
            for player in lineup:
                # Check if this is a D/ST
                slot_pos = getattr(player, 'slot_position', '')
                player_name = getattr(player, 'name', 'Unknown')
                is_dst = slot_pos == 'D/ST' or 'D/ST' in player_name
                
                # Get points
                points = getattr(player, 'points', 0)
                
                # Get stats - espn_api library structure
                stats = getattr(player, 'stats', [])
                
                # Print players with significant points (potential return TD) or D/ST
                if points >= 6 or is_dst:
                    print(f"\nPlayer: {player_name}")
                    print(f"Position: {slot_pos}")
                    print(f"Points: {points}")
                    print(f"Pro Team: {getattr(player, 'proTeam', 'N/A')}")
                    
                    # Inspect stats structure
                    if stats:
                        print(f"Stats array length: {len(stats)}")
                        for i, stat_entry in enumerate(stats):
                            print(f"\n  Stat Entry {i}:")
                            if hasattr(stat_entry, '__dict__'):
                                print(f"    Attributes: {dir(stat_entry)}")
                                # Try to access common attributes
                                for attr in ['statSourceId', 'scoringPeriodId', 'appliedTotal', 'appliedStats']:
                                    if hasattr(stat_entry, attr):
                                        value = getattr(stat_entry, attr)
                                        print(f"    {attr}: {value}")
                            elif isinstance(stat_entry, dict):
                                print(f"    Dict keys: {list(stat_entry.keys())}")
                                # Check for appliedStats
                                if 'appliedStats' in stat_entry:
                                    applied_stats = stat_entry['appliedStats']
                                    print(f"    appliedStats: {applied_stats}")
                                    if isinstance(applied_stats, dict):
                                        for stat_id, value in applied_stats.items():
                                            if value > 0:
                                                print(f"      Stat ID {stat_id}: {value}")
                            else:
                                print(f"    Type: {type(stat_entry)}")
                                print(f"    Value: {stat_entry}")
                    else:
                        print("  No stats found")
                    
                    # Special attention to Rashid Shaheed (known return TD)
                    if "Shaheed" in player_name:
                        print("\n  *** RASHID SHAHEED FOUND - KNOWN RETURN TD PLAYER ***")
                        print(f"  Points: {points}")
                        print(f"  Full player object attributes: {dir(player)}")
                        
                        # Try to get raw data if possible
                        if hasattr(player, '__dict__'):
                            print(f"  Player __dict__: {player.__dict__}")


def explore_raw_api(season: int = 2024, week: int = 16):
    """
    If espn_api library abstracts too much, fetch raw JSON.
    """
    from rffl.live.scores import LiveScoreClient
    
    client = LiveScoreClient(league_id=323196, season=season)
    data = client.fetch_scoreboard(scoring_period=week, include_boxscore=True)
    
    # Save for manual inspection
    output_file = Path(f"raw_boxscore_s{season}_w{week}.json")
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"\n=== Raw API Data Saved ===")
    print(f"Saved raw data to {output_file}")
    print("Search for 'appliedStats' in the JSON to find stat structure")
    print("\nSearching for Rashid Shaheed in raw data...")
    
    # Search for Shaheed in the raw data
    def search_for_player(data, name="Shaheed"):
        """Recursively search for player name in nested dict/list structure."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    result = search_for_player(value, name)
                    if result:
                        return {key: result}
                elif isinstance(value, str) and name.lower() in value.lower():
                    return {key: value}
        elif isinstance(data, list):
            for item in data:
                result = search_for_player(item, name)
                if result:
                    return result
        return None
    
    shaheed_data = search_for_player(data, "Shaheed")
    if shaheed_data:
        print("\nFound Shaheed in raw data:")
        print(json.dumps(shaheed_data, indent=2)[:1000])  # Print first 1000 chars
    else:
        print("Shaheed not found in raw data structure")


if __name__ == "__main__":
    print("=== Using espn_api library ===\n")
    discover_stat_ids(season=2024, week=16)
    
    print("\n\n=== Fetching raw API data ===")
    explore_raw_api(season=2024, week=16)


