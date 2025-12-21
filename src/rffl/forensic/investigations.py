"""
Investigation-specific logic implementations.
"""
from typing import Optional
import pandas as pd  # type: ignore[import-untyped]
from pathlib import Path

from .tools import ESPNAPITool, DataAnalysisTool


class ReturnTDDoubleDipInvestigation:
    """
    Investigation: Return TD "Double Dip" Forensic Validation
    
    Determines if the return TD double scoring mechanic (player gets 6 pts + 
    D/ST gets 6 pts for same play) creates an exploitable advantage.
    """
    
    def __init__(self, api_tool: ESPNAPITool, analysis_tool: DataAnalysisTool):
        self.api_tool = api_tool
        self.analysis_tool = analysis_tool
    
    def identify_player_return_tds(
        self,
        start_year: int,
        end_year: int,
        output_path: Optional[Path] = None
    ) -> pd.DataFrame:
        """
        Task 1: Identify all return TDs in RFFL history.
        
        Returns DataFrame with columns:
        [season, week, player_id, player_name, nfl_team, pro_team_id, 
         scoring_type, points, rffl_team_code, lineup_slot]
        """
        all_return_tds = []
        
        for season in range(start_year, end_year + 1):
            try:
                # Get all return TDs for this season (no filter - gets both kick and punt)
                season_tds = self.api_tool.get_scoring_plays(season=season)
                if not season_tds.empty:
                    all_return_tds.append(season_tds)
            except Exception as e:
                # Log error but continue with other seasons
                print(f"Warning: Could not extract return TDs for {season}: {e}")
                continue
        
        if not all_return_tds:
            return pd.DataFrame(columns=[
                "season", "week", "player_id", "player_name", "nfl_team", 
                "pro_team_id", "scoring_type", "points", "rffl_team_code", "lineup_slot"
            ])
        
        result = pd.concat(all_return_tds, ignore_index=True)
        
        if output_path:
            result.to_csv(output_path, index=False)
        
        return result
    
    def identify_dst_return_tds(
        self,
        start_year: int,
        end_year: int,
        output_path: Optional[Path] = None
    ) -> pd.DataFrame:
        """
        Task 2: Identify all D/ST return TDs in RFFL history.
        
        Returns DataFrame with columns:
        [season, week, dst_team, pro_team_id, dst_points, 
         includes_return_td, rffl_team_code, lineup_slot]
        """
        all_dst_tds = []
        
        for season in range(start_year, end_year + 1):
            try:
                # Get D/ST scoring for this season
                season_dst = self.api_tool.get_dst_scoring(season=season)
                if not season_dst.empty:
                    all_dst_tds.append(season_dst)
            except Exception as e:
                print(f"Warning: Could not extract D/ST scoring for {season}: {e}")
                continue
        
        if not all_dst_tds:
            return pd.DataFrame(columns=[
                "season", "week", "dst_team", "pro_team_id", "dst_points",
                "includes_return_td", "rffl_team_code", "lineup_slot"
            ])
        
        result = pd.concat(all_dst_tds, ignore_index=True)
        
        if output_path:
            result.to_csv(output_path, index=False)
        
        return result
    
    def cross_reference_double_dips(
        self,
        player_return_tds: pd.DataFrame,
        dst_return_tds: pd.DataFrame,
        output_path: Optional[Path] = None
    ) -> pd.DataFrame:
        """
        Task 3: Cross-reference for "double dip" events.
        
        Finds instances where same RFFL owner rostered BOTH the individual 
        player AND that player's NFL team D/ST in the same week.
        
        Uses Full Attribution - requires explicit stat ID matching.
        """
        double_dips = self.analysis_tool.cross_reference_double_dips(
            player_return_tds,
            dst_return_tds,
            api_tool=self.api_tool
        )
        
        if output_path:
            double_dips.to_csv(output_path, index=False)
        
        return double_dips
    
    def analyze_starter_status(
        self,
        double_dips: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Task 4: Starter vs Bench Analysis.
        
        For each "double dip" event, determine if both player and D/ST 
        were in the starting lineup (points only count if BOTH were started).
        """
        # This is already handled in cross_reference_double_dips
        # which adds player_started, dst_started, both_started columns
        return double_dips
    
    def counterfactual_analysis(
        self,
        player_return_tds: pd.DataFrame,
        dst_return_tds: pd.DataFrame,
        output_path: Optional[Path] = None
    ) -> pd.DataFrame:
        """
        Task 5: Counterfactual Analysis.
        
        For return TDs where the player WAS rostered but D/ST was NOT 
        (or vice versa), identify missed double-dip opportunities.
        """
        # Find player return TDs where D/ST was not rostered by same owner
        # This requires checking if D/ST was rostered by any team that week
        
        # TODO: Implement counterfactual analysis
        # This would require checking roster composition to see if D/ST
        # was available but not rostered by the player's owner
        
        result = pd.DataFrame(columns=[
            "season", "week", "player_name", "nfl_team", "rffl_team_code",
            "player_rostered", "dst_rostered", "missed_opportunity"
        ])
        
        if output_path:
            result.to_csv(output_path, index=False)
        
        return result
    
    def generate_summary_stats(
        self,
        double_dips: pd.DataFrame
    ) -> dict:
        """
        Task 6: Summary Statistics.
        
        Generate summary report with:
        - Total return TDs scored by RFFL-rostered players
        - Total "double dip" events (same owner had both player + D/ST rostered)
        - Total "double dip" events where BOTH were started
        - Percentage of return TDs that resulted in actual double-dip benefit
        - List of RFFL owners who have benefited, with frequency
        """
        return self.analysis_tool.generate_summary_stats(double_dips)

