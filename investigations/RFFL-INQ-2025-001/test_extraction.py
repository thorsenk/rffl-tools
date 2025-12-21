"""
Test extraction methods for return TD detection.
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rffl.forensic.tools import ESPNAPITool
from rffl.core.api import ESPNCredentials

def test_player_return_tds():
    """Test player return TD extraction."""
    print("=== Testing Player Return TD Extraction ===\n")
    
    tool = ESPNAPITool(league_id=323196)
    creds = ESPNCredentials(
        espn_s2=os.getenv('ESPN_S2'),
        swid=os.getenv('SWID')
    )
    tool.credentials = creds
    
    try:
        df = tool.get_scoring_plays(season=2025, week=16)
        print(f"Found {len(df)} return TD events\n")
        
        if len(df) > 0:
            print("All return TD events:")
            print(df.to_string())
            print()
            
            # Check for Shaheed specifically
            shaheed = df[df['player_name'].str.contains('Shaheed', case=False, na=False)]
            if len(shaheed) > 0:
                print("✅ Found Rashid Shaheed return TD:")
                print(shaheed.to_string())
                print()
                return True
            else:
                print("⚠️ Shaheed not found in results")
                return False
        else:
            print("⚠️ No return TD events found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dst_scoring():
    """Test D/ST scoring extraction."""
    print("\n=== Testing D/ST Scoring Extraction ===\n")
    
    tool = ESPNAPITool(league_id=323196)
    creds = ESPNCredentials(
        espn_s2=os.getenv('ESPN_S2'),
        swid=os.getenv('SWID')
    )
    tool.credentials = creds
    
    try:
        df = tool.get_dst_scoring(season=2025, week=16)
        print(f"Found {len(df)} D/ST scoring events\n")
        
        if len(df) > 0:
            print("All D/ST events:")
            print(df.to_string())
            print()
            
            # Check for Seattle D/ST specifically
            seattle = df[df['dst_team'] == 'SEA']
            if len(seattle) > 0:
                print("✅ Found Seattle D/ST:")
                print(seattle.to_string())
                print()
                
                # Check if it includes return TD
                if seattle['includes_return_td'].any():
                    print("✅ Seattle D/ST has return TD flag set")
                    return True
                else:
                    print("⚠️ Seattle D/ST does not have return TD flag")
                    return False
            else:
                print("⚠️ Seattle D/ST not found")
                return False
        else:
            print("⚠️ No D/ST events found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing Return TD Extraction Methods\n")
    print("=" * 50)
    
    player_test = test_player_return_tds()
    dst_test = test_dst_scoring()
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"  Player Return TD Extraction: {'✅ PASS' if player_test else '❌ FAIL'}")
    print(f"  D/ST Scoring Extraction: {'✅ PASS' if dst_test else '❌ FAIL'}")
    
    if player_test and dst_test:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)

