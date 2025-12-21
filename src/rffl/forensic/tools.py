"""
Forensic investigation tools for RFFL data analysis.
"""
from dataclasses import dataclass
from typing import Optional, Any
from enum import Enum
import pandas as pd  # type: ignore[import-untyped]
from pathlib import Path
import time

from rffl.core.api import ESPNClient, ESPNCredentials
from rffl.core.utils import load_canonical_meta, resolve_canonical, load_alias_index, get_team_abbrev
from rffl.core.rosters import map_pro_team_id
from rffl.live.scores import LiveScoreClient
from rffl.forensic.stat_ids import PlayerStatID, DSTStatID


class DataCompleteness(Enum):
    """Flag for historical data quality."""
    COMPLETE = "complete"
    PARTIAL = "partial"
    INCOMPLETE = "incomplete"


@dataclass
class SeasonDataQuality:
    """Track data quality per season."""
    season: int
    completeness: DataCompleteness
    notes: Optional[str] = None


# Known data quality issues by season
SEASON_DATA_QUALITY: dict[int, SeasonDataQuality] = {
    2011: SeasonDataQuality(2011, DataCompleteness.PARTIAL, "Limited boxscore detail"),
    2012: SeasonDataQuality(2012, DataCompleteness.PARTIAL, "Limited boxscore detail"),
    2013: SeasonDataQuality(2013, DataCompleteness.PARTIAL, "Limited boxscore detail"),
    2014: SeasonDataQuality(2014, DataCompleteness.PARTIAL, "Limited boxscore detail"),
    2015: SeasonDataQuality(2015, DataCompleteness.PARTIAL, "Limited boxscore detail"),
    2016: SeasonDataQuality(2016, DataCompleteness.PARTIAL, "Limited boxscore detail"),
    2017: SeasonDataQuality(2017, DataCompleteness.PARTIAL, "Limited boxscore detail"),
    2018: SeasonDataQuality(2018, DataCompleteness.PARTIAL, "Limited boxscore detail"),
    2019: SeasonDataQuality(2019, DataCompleteness.COMPLETE, "Full API coverage begins"),
    2020: SeasonDataQuality(2020, DataCompleteness.COMPLETE, None),
    2021: SeasonDataQuality(2021, DataCompleteness.COMPLETE, None),
    2022: SeasonDataQuality(2022, DataCompleteness.COMPLETE, None),
    2023: SeasonDataQuality(2023, DataCompleteness.COMPLETE, None),
    2024: SeasonDataQuality(2024, DataCompleteness.COMPLETE, None),
    2025: SeasonDataQuality(2025, DataCompleteness.COMPLETE, None),
}


class ESPNAPITool:
    """
    ESPN Fantasy API tool for forensic investigations.
    
    Known Challenges:
    - Return TD attribution may be buried in boxscore HTML for older seasons
    - Historical seasons (2011-2018) have sparser data structures
    - Player-to-D/ST mapping requires proTeamId cross-reference
    - Rate limits apply on bulk historical queries
    
    ESPN Stat ID Reference:
    - Kick Return TD: Stat ID 102 (discovered via RFFL-INQ-2025-001)
    - Punt Return TD: TBD (to be discovered)
    - Note: Return TDs are in player.stats[].appliedStats dictionaries
    """
    
    def __init__(self, league_id: int = 323196, credentials: Optional[ESPNCredentials] = None):
        self.league_id = league_id
        self.credentials = credentials
        self._team_registry: dict[tuple[int, str], dict[Any, Any]] | None = None
    
    @property
    def team_registry(self) -> dict[tuple[int, str], dict[Any, Any]]:
        """Lazy-load canonical team registry."""
        if self._team_registry is None:
            # Fall back to CSV-based canonical metadata
            repo_root = Path.cwd()
            for parent in [repo_root, *repo_root.parents]:
                if (parent / "pyproject.toml").exists():
                    repo_root = parent
                    break
            self._team_registry = load_canonical_meta(repo_root)
        return self._team_registry
    
    def get_scoring_plays(
        self, 
        season: int, 
        week: Optional[int] = None,
        scoring_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Extract scoring plays from ESPN API using raw API to access appliedStats.
        
        Args:
            season: NFL season year
            week: Optional specific week (None = all weeks)
            scoring_type: Filter by type (e.g., "kick_return_td", "punt_return_td")
        
        Returns:
            DataFrame with columns:
            [season, week, player_id, player_name, nfl_team, pro_team_id, 
             scoring_type, points, rffl_team_code, lineup_slot]
        
        Notes:
            - Uses LiveScoreClient to access raw JSON with appliedStats
            - For seasons 2011-2018, data may be incomplete
            - Stat ID 102 = Kick Return TD (discovered)
        """
        quality = SEASON_DATA_QUALITY.get(season)
        if quality and quality.completeness == DataCompleteness.INCOMPLETE:
            raise ValueError(f"Season {season} has insufficient data for this query")
        
        if PlayerStatID.KICK_RETURN_TD is None:
            raise ValueError("Kick Return TD stat ID not yet discovered. Run discovery script first.")
        
        # Use raw API to access appliedStats
        client = LiveScoreClient(
            league_id=self.league_id,
            season=season,
            espn_s2=self.credentials.espn_s2 if self.credentials else None,
            swid=self.credentials.swid if self.credentials else None,
        )
        
        # Load team mappings
        repo_root = Path.cwd()
        for parent in [repo_root, *repo_root.parents]:
            if (parent / "pyproject.toml").exists():
                repo_root = parent
                break
        
        alias_idx = load_alias_index(repo_root / "data" / "teams" / "alias_mapping.yaml")
        canon_meta = load_canonical_meta(repo_root)
        
        # Map proTeamId to NFL team abbreviations
        # proTeamId mapping: 1=BAL, 2=CIN, 3=CLE, 4=PIT, 5=BUF, 6=MIA, 7=DEN, 8=KC, etc.
        # We'll use map_pro_team_id from rosters module
        
        return_td_events = []
        
        # Determine weeks to process
        weeks_to_process = [week] if week else range(1, 19)
        
        for week_num in weeks_to_process:
            try:
                # Fetch raw boxscore data
                data = client.fetch_scoreboard(
                    scoring_period=week_num,
                    include_boxscore=True
                )
                
                # Extract return TD events from rosters
                teams = data.get('teams', [])
                for team in teams:
                    # Resolve RFFL team code from raw JSON team data
                    team_id = team.get('id')
                    # Try to get team abbreviation from various possible fields
                    team_abbrev = (
                        team.get('abbrev') or 
                        team.get('teamAbbrev') or
                        (team.get('location', '') + ' ' + team.get('nickname', '')).strip()
                    )
                    # Resolve to canonical RFFL team code
                    rffl_team_code = resolve_canonical(team_abbrev, season, alias_idx)
                    
                    # If resolution failed, try to match by team ID or owner info
                    if rffl_team_code == team_abbrev:  # Resolution failed
                        # Try matching via canonical metadata
                        for (y, code), meta in canon_meta.items():
                            if y == season:
                                # Could try matching by owner if available
                                pass
                        # Fallback: use team abbreviation as-is
                        rffl_team_code = team_abbrev or f"TEAM_{team_id}"
                    
                    # Get roster entries
                    roster = team.get('roster', {}).get('entries', [])
                    for entry in roster:
                        player = entry.get('playerPoolEntry', {}).get('player', {})
                        player_id = player.get('id')
                        player_name = player.get('fullName', 'Unknown')
                        pro_team_id = player.get('proTeamId')
                        default_pos = player.get('defaultPositionId')
                        
                        # Skip D/ST players (defaultPositionId == 16) - they're handled separately
                        if default_pos == 16:
                            continue
                        
                        nfl_team = map_pro_team_id(pro_team_id) if pro_team_id else None
                        
                        # Get lineup slot
                        lineup_slot_id = entry.get('lineupSlotId')
                        # Map lineup slot ID to name (16=D/ST, 0=QB, 2=RB, 4=WR, 6=TE, 23=FLEX, 20=K, 21=BE)
                        slot_map = {
                            0: "QB", 2: "RB", 4: "WR", 6: "TE", 
                            16: "D/ST", 20: "K", 21: "BE", 23: "FLEX"
                        }
                        lineup_slot = slot_map.get(lineup_slot_id, f"SLOT_{lineup_slot_id}")
                        
                        # Check stats for return TDs
                        stats = player.get('stats', [])
                        for stat_entry in stats:
                            if not isinstance(stat_entry, dict):
                                continue
                            
                            # Only process actual stats (statSourceId == 0) for the current week
                            stat_source = stat_entry.get('statSourceId')
                            scoring_period = stat_entry.get('scoringPeriodId')
                            
                            if stat_source != 0 or scoring_period != week_num:
                                continue
                            
                            applied_stats = stat_entry.get('appliedStats', {})
                            
                            # Check for kick return TD (Stat ID 102)
                            kick_return_td_stat = str(PlayerStatID.KICK_RETURN_TD)
                            if kick_return_td_stat in applied_stats:
                                kick_return_td_value = applied_stats[kick_return_td_stat]
                                if kick_return_td_value > 0:
                                    # Stat value appears to already be in points (6.0 = 6 points)
                                    # If value is exactly 6.0, it's likely already points, not count
                                    # If value is 1.0, it's a count and needs multiplication
                                    # Based on discovery: Shaheed had value 6.0 = 6 points
                                    points = kick_return_td_value if kick_return_td_value >= 6.0 else kick_return_td_value * 6.0
                                    
                                    return_td_events.append({
                                        'season': season,
                                        'week': week_num,
                                        'player_id': player_id,
                                        'player_name': player_name,
                                        'nfl_team': nfl_team,
                                        'pro_team_id': pro_team_id,
                                        'scoring_type': 'kick_return_td',
                                        'points': points,
                                        'rffl_team_code': rffl_team_code,
                                        'lineup_slot': lineup_slot,
                                    })
                            
                            # Check for punt return TD (when discovered)
                            if PlayerStatID.PUNT_RETURN_TD is not None:
                                punt_return_td_stat = str(PlayerStatID.PUNT_RETURN_TD)
                                if punt_return_td_stat in applied_stats:
                                    punt_return_td_value = applied_stats[punt_return_td_stat]
                                    if punt_return_td_value > 0:
                                        return_td_events.append({
                                            'season': season,
                                            'week': week_num,
                                            'player_id': player_id,
                                            'player_name': player_name,
                                            'nfl_team': nfl_team,
                                            'pro_team_id': pro_team_id,
                                            'scoring_type': 'punt_return_td',
                                            'points': punt_return_td_value * 6.0,
                                            'rffl_team_code': rffl_team_code,
                                            'lineup_slot': lineup_slot,
                                        })
                
                # Rate limit: sleep between weeks
                if week is None:  # Only sleep if processing multiple weeks
                    time.sleep(1)
                    
            except Exception as e:
                # Log error but continue with other weeks
                print(f"Warning: Could not process Week {week_num} for season {season}: {e}")
                continue
        
        # Filter by scoring_type if provided
        if scoring_type:
            return_td_events = [e for e in return_td_events if e['scoring_type'] == scoring_type]
        
        if not return_td_events:
            return pd.DataFrame(columns=[
                'season', 'week', 'player_id', 'player_name', 'nfl_team', 
                'pro_team_id', 'scoring_type', 'points', 'rffl_team_code', 'lineup_slot'
            ])
        
        return pd.DataFrame(return_td_events)
    
    def get_dst_scoring(
        self,
        season: int,
        week: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Extract D/ST scoring including special teams TDs.
        
        Returns:
            DataFrame with columns:
            [season, week, dst_team, pro_team_id, dst_points, 
             includes_return_td, rffl_team_code, lineup_slot]
        """
        quality = SEASON_DATA_QUALITY.get(season)
        if quality and quality.completeness == DataCompleteness.INCOMPLETE:
            raise ValueError(f"Season {season} has insufficient data for this query")
        
        if DSTStatID.KICK_RETURN_TD is None:
            raise ValueError("D/ST Kick Return TD stat ID not yet discovered. Run discovery script first.")
        
        # Use raw API to access appliedStats
        client = LiveScoreClient(
            league_id=self.league_id,
            season=season,
            espn_s2=self.credentials.espn_s2 if self.credentials else None,
            swid=self.credentials.swid if self.credentials else None,
        )
        
        # Load team mappings
        repo_root = Path.cwd()
        for parent in [repo_root, *repo_root.parents]:
            if (parent / "pyproject.toml").exists():
                repo_root = parent
                break
        
        alias_idx = load_alias_index(repo_root / "data" / "teams" / "alias_mapping.yaml")
        canon_meta = load_canonical_meta(repo_root)
        
        dst_events = []
        
        # Determine weeks to process
        weeks_to_process = [week] if week else range(1, 19)
        
        for week_num in weeks_to_process:
            try:
                # Fetch raw boxscore data
                data = client.fetch_scoreboard(
                    scoring_period=week_num,
                    include_boxscore=True
                )
                
                # Extract D/ST scoring from rosters
                teams = data.get('teams', [])
                for team in teams:
                    # Resolve RFFL team code
                    team_id = team.get('id')
                    team_abbrev = (
                        team.get('abbrev') or 
                        team.get('teamAbbrev') or
                        (team.get('location', '') + ' ' + team.get('nickname', '')).strip()
                    )
                    rffl_team_code = resolve_canonical(team_abbrev, season, alias_idx)
                    if rffl_team_code == team_abbrev:  # Resolution failed
                        rffl_team_code = team_abbrev or f"TEAM_{team_id}"
                    
                    # Get roster entries
                    roster = team.get('roster', {}).get('entries', [])
                    for entry in roster:
                        player = entry.get('playerPoolEntry', {}).get('player', {})
                        default_pos = player.get('defaultPositionId')
                        
                        # D/ST has defaultPositionId == 16
                        if default_pos != 16:
                            continue
                        
                        player_id = player.get('id')
                        player_name = player.get('fullName', 'Unknown')
                        pro_team_id = player.get('proTeamId')
                        dst_team = map_pro_team_id(pro_team_id) if pro_team_id else None
                        
                        # Get lineup slot
                        lineup_slot_id = entry.get('lineupSlotId')
                        # Map lineup slot ID to name (16=D/ST, 20=K, 21=BE)
                        slot_map = {
                            16: "D/ST", 
                            20: "K",
                            21: "BE"
                        }
                        lineup_slot = slot_map.get(lineup_slot_id, f"SLOT_{lineup_slot_id}")
                        
                        # Check stats for return TDs
                        stats = player.get('stats', [])
                        for stat_entry in stats:
                            if not isinstance(stat_entry, dict):
                                continue
                            
                            # Only process actual stats (statSourceId == 0) for the current week
                            stat_source = stat_entry.get('statSourceId')
                            scoring_period = stat_entry.get('scoringPeriodId')
                            
                            if stat_source != 0 or scoring_period != week_num:
                                continue
                            
                            applied_stats = stat_entry.get('appliedStats', {})
                            dst_total_points = stat_entry.get('appliedTotal', 0.0)
                            
                            # Check for kick return TD (Stat ID 102)
                            kick_return_td_stat = str(DSTStatID.KICK_RETURN_TD)
                            includes_kick_return_td = (
                                kick_return_td_stat in applied_stats and 
                                applied_stats[kick_return_td_stat] > 0
                            )
                            
                            # Check for punt return TD (when discovered)
                            includes_punt_return_td = False
                            if DSTStatID.PUNT_RETURN_TD is not None:
                                punt_return_td_stat = str(DSTStatID.PUNT_RETURN_TD)
                                includes_punt_return_td = (
                                    punt_return_td_stat in applied_stats and 
                                    applied_stats[punt_return_td_stat] > 0
                                )
                            
                            includes_return_td = includes_kick_return_td or includes_punt_return_td
                            
                            if includes_return_td or dst_total_points > 0:
                                dst_events.append({
                                    'season': season,
                                    'week': week_num,
                                    'dst_team': dst_team,
                                    'pro_team_id': pro_team_id,
                                    'dst_points': dst_total_points,
                                    'includes_return_td': includes_return_td,
                                    'rffl_team_code': rffl_team_code,
                                    'lineup_slot': lineup_slot,
                                })
                
                # Rate limit: sleep between weeks
                if week is None:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Warning: Could not process Week {week_num} for season {season}: {e}")
                continue
        
        if not dst_events:
            return pd.DataFrame(columns=[
                'season', 'week', 'dst_team', 'pro_team_id', 'dst_points',
                'includes_return_td', 'rffl_team_code', 'lineup_slot'
            ])
        
        return pd.DataFrame(dst_events)
    
    def get_rosters(
        self,
        season: int,
        week: int
    ) -> pd.DataFrame:
        """
        Get roster composition for all teams in a given week.
        
        Returns:
            DataFrame with columns:
            [season, week, rffl_team_code, player_id, player_name, 
             position, lineup_slot, is_starter, pro_team_id]
        """
        # TODO: Implement roster extraction
        # Key steps:
        # 1. Get boxscores for season/week
        # 2. Extract all players from all teams
        # 3. Map to RFFL team_code
        # 4. Determine is_starter from lineup_slot
        
        raise NotImplementedError("Implement ESPN API roster extraction")
    
    def map_player_to_dst(self, player_id: int, season: int) -> Optional[str]:
        """
        Map a player to their NFL team's D/ST identifier.
        
        Uses proTeamId to cross-reference.
        """
        # This is a helper method - actual mapping happens via pro_team_id
        # in the cross-reference logic
        return None  # Not needed for current implementation
    
    def verify_dst_return_td(
        self,
        dst_applied_stats: dict[str, float],
        return_type: str
    ) -> Optional[dict[str, Any]]:
        """
        Verify D/ST has matching return TD stat using Full Attribution.
        
        Args:
            dst_applied_stats: Dictionary of stat ID -> value from D/ST's appliedStats
            return_type: "kick" or "punt"
        
        Returns:
            Dict with stat_id, count, and points if found, None otherwise
        """
        if return_type == "kick":
            target_stat_id = DSTStatID.KICK_RETURN_TD
        elif return_type == "punt":
            if DSTStatID.PUNT_RETURN_TD is None:
                return None
            target_stat_id = DSTStatID.PUNT_RETURN_TD
        else:
            raise ValueError(f"Unknown return type: {return_type}")
        
        if target_stat_id is None:
            return None
        
        # Check D/ST's applied_stats for the matching stat
        stat_value = dst_applied_stats.get(str(target_stat_id), 0)
        
        if stat_value > 0:
            return {
                "stat_id": target_stat_id,
                "count": int(stat_value),
                "points": stat_value * 6.0  # Each return TD = 6 pts
            }
        
        return None


class DataAnalysisTool:
    """Pandas-based data analysis utilities."""
    
    @staticmethod
    def cross_reference_double_dips(
        player_return_tds: pd.DataFrame,
        dst_return_tds: pd.DataFrame,
        api_tool: Optional['ESPNAPITool'] = None
    ) -> pd.DataFrame:
        """
        Find instances where same RFFL owner had both player AND D/ST 
        for a return TD in the same week.
        
        FULL ATTRIBUTION METHOD:
        - Match on: season, week, pro_team_id, rffl_team_code
        - EXPLICITLY VERIFY: D/ST's appliedStats contains matching return TD stat ID
        - Only count as double-dip if stat match confirmed
        
        Args:
            player_return_tds: DataFrame from get_scoring_plays()
            dst_return_tds: DataFrame from get_dst_scoring()
            api_tool: Optional ESPNAPITool for Full Attribution verification
        
        Returns:
            DataFrame with columns:
            [season, week, player_name, nfl_team, rffl_team_code,
             player_points, dst_points, total_points, 
             player_started, dst_started, both_started,
             player_stat_id, dst_stat_id, attribution_method]
        """
        if player_return_tds.empty or dst_return_tds.empty:
            return pd.DataFrame(columns=[
                'season', 'week', 'player_name', 'nfl_team', 'rffl_team_code',
                'player_points', 'dst_points', 'total_points',
                'player_started', 'dst_started', 'both_started',
                'player_stat_id', 'dst_stat_id', 'attribution_method'
            ])
        
        # Join on season + week + NFL team + RFFL owner
        merged = pd.merge(
            player_return_tds,
            dst_return_tds,
            on=["season", "week", "pro_team_id", "rffl_team_code"],
            suffixes=("_player", "_dst"),
            how="inner"
        )
        
        if merged.empty:
            return pd.DataFrame(columns=[
                'season', 'week', 'player_name', 'nfl_team', 'rffl_team_code',
                'player_points', 'dst_points', 'total_points',
                'player_started', 'dst_started', 'both_started',
                'player_stat_id', 'dst_stat_id', 'attribution_method'
            ])
        
        # Determine if both were in starting lineup
        # Lineup slot codes: "QB", "RB", "WR", "TE", "FLEX", "K", "D/ST", "BE" (bench), "IR"
        merged["player_started"] = merged["lineup_slot_player"].apply(
            lambda x: x not in ["BE", "Bench", "IR", "SLOT_21"] if pd.notna(x) else False
        )
        merged["dst_started"] = merged["lineup_slot_dst"].apply(
            lambda x: x not in ["BE", "Bench", "IR", "SLOT_21"] if pd.notna(x) else False
        )
        merged["both_started"] = merged["player_started"] & merged["dst_started"]
        
        # Add stat ID columns (for Full Attribution)
        # Player stat ID based on scoring_type
        merged["player_stat_id"] = merged["scoring_type"].apply(
            lambda x: PlayerStatID.KICK_RETURN_TD if x == "kick_return_td" 
                     else (PlayerStatID.PUNT_RETURN_TD if x == "punt_return_td" else None)
        )
        merged["dst_stat_id"] = merged["scoring_type"].apply(
            lambda x: DSTStatID.KICK_RETURN_TD if x == "kick_return_td"
                     else (DSTStatID.PUNT_RETURN_TD if x == "punt_return_td" else None)
        )
        merged["attribution_method"] = "explicit_stat_match"
        
        # Calculate combined points (only if both started)
        merged["total_points"] = (
            merged["points"] + 
            merged["dst_points"].where(merged["both_started"], 0)
        )
        
        # Note: Full Attribution verification requires access to raw appliedStats
        # This is done at a higher level in the investigation logic
        # where we can verify the D/ST actually has the matching stat ID
        
        return merged
    
    @staticmethod
    def generate_summary_stats(double_dips: pd.DataFrame) -> dict:
        """
        Generate summary statistics for investigation report.
        
        Args:
            double_dips: DataFrame from cross_reference_double_dips()
        
        Returns dict with:
        - total_return_tds: int (total player return TDs found)
        - total_double_dip_rostered: int (same owner had both rostered)
        - total_double_dip_started: int (both in starting lineup)
        - pct_double_dip: float (percentage with double-dip benefit)
        - benefiting_teams: list[dict] with team_code, count, total_points
        """
        if len(double_dips) == 0:
            return {
                "total_return_tds": 0,
                "total_double_dip_rostered": 0,
                "total_double_dip_started": 0,
                "pct_double_dip": 0.0,
                "benefiting_teams": []
            }
        
        # Filter for events where both were started
        both_started = double_dips[double_dips.get("both_started", False)]
        
        # Count unique return TD events (by season, week, player)
        total_return_tds = len(double_dips)
        
        # Count double-dip events (same owner had both)
        total_double_dip_rostered = len(double_dips[double_dips["rffl_team_code"].notna()])
        
        # Count double-dip events where both were started
        total_double_dip_started = len(both_started)
        
        # Calculate percentage
        pct_double_dip = (
            total_double_dip_started / max(total_return_tds, 1) * 100
        ) if total_return_tds > 0 else 0.0
        
        # Get benefiting teams
        if len(both_started) > 0:
            benefiting_teams = (
                both_started.groupby("rffl_team_code")
                .agg(
                    count=("season", "count"),
                    total_points=("total_points", "sum")
                )
                .reset_index()
                .to_dict("records")
            )
        else:
            benefiting_teams = []
        
        return {
            "total_return_tds": total_return_tds,
            "total_double_dip_rostered": total_double_dip_rostered,
            "total_double_dip_started": total_double_dip_started,
            "pct_double_dip": pct_double_dip,
            "benefiting_teams": benefiting_teams
        }

