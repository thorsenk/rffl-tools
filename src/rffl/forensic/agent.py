"""
Main forensic investigation agent orchestrator.
"""
import yaml
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd  # type: ignore[import-untyped]

from .schemas import (
    InvestigationConfig,
    InvestigationCategory,
    InvestigationStatus,
    Petitioner,
    Inquiry,
    InvestigationTask,
    PriorAnalysis,
    OutputConfig,
)
from .tools import ESPNAPITool, DataAnalysisTool
from .investigations import ReturnTDDoubleDipInvestigation
from .reporter import ForensicReporter, ReportData
from rffl.core.api import ESPNCredentials


class ForensicAgent:
    """Main agent for conducting forensic investigations."""
    
    def __init__(self, investigations_root: Optional[Path] = None):
        """
        Initialize forensic agent.
        
        Args:
            investigations_root: Root directory for investigations (default: investigations/)
        """
        if investigations_root is None:
            investigations_root = Path("investigations")
        self.investigations_root = investigations_root
    
    def load_investigation(self, case_id: str) -> InvestigationConfig:
        """
        Load investigation configuration from YAML file.
        
        Args:
            case_id: Case ID (e.g., "RFFL-INQ-2025-001")
        
        Returns:
            InvestigationConfig object
        """
        config_path = self.investigations_root / case_id / "investigation.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Investigation config not found: {config_path}")
        
        with open(config_path, "r") as f:
            config_dict = yaml.safe_load(f)
        
        # Parse nested structures
        # Handle datetime parsing (YAML may parse it automatically or leave as string)
        submitted_at = config_dict["petitioner"]["submitted_at"]
        if isinstance(submitted_at, str):
            # Handle ISO format with or without Z
            if submitted_at.endswith("Z"):
                submitted_at = submitted_at[:-1] + "+00:00"
            submitted_at = datetime.fromisoformat(submitted_at)
        elif isinstance(submitted_at, datetime):
            # Already a datetime object
            pass
        else:
            raise ValueError(f"Invalid submitted_at format: {type(submitted_at)}")
        
        petitioner = Petitioner(
            team_code=config_dict["petitioner"]["team_code"],
            submitted_at=submitted_at
        )
        
        inquiry = Inquiry(
            summary=config_dict["inquiry"]["summary"],
            full_text=config_dict["inquiry"]["full_text"]
        )
        
        tasks = [
            InvestigationTask(**task_dict)
            for task_dict in config_dict["investigation"]["tasks"]
        ]
        
        prior_analysis = None
        if "prior_analysis" in config_dict:
            prior_analysis = PriorAnalysis(**config_dict["prior_analysis"])
        
        outputs = None
        if "outputs" in config_dict:
            outputs = OutputConfig(**config_dict["outputs"])
        
        return InvestigationConfig(
            case_id=config_dict["case_id"],
            title=config_dict["title"],
            category=InvestigationCategory(config_dict["category"]),
            petitioner=petitioner,
            inquiry=inquiry,
            investigation_type=config_dict["investigation"]["type"],
            data_range=tuple(config_dict["investigation"]["data_range"]),
            league_id=config_dict["investigation"]["league_id"],
            tasks=tasks,
            status=InvestigationStatus(config_dict.get("status", "submitted")),
            investigator=config_dict.get("investigator", "Forensic Agent v1.0"),
            commissioner_approved=config_dict.get("commissioner_approved", False),
            prior_analysis=prior_analysis,
            outputs=outputs
        )
    
    def execute_investigation(
        self,
        config: InvestigationConfig,
        season_filter: Optional[int] = None
    ) -> dict:
        """
        Execute investigation and generate outputs.
        
        Args:
            config: Investigation configuration
            season_filter: Optional season to filter to (for rate limit management)
        
        Returns:
            Dictionary with investigation results and data files
        """
        output_dir = self.investigations_root / config.case_id
        data_dir = output_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize tools
        # Get credentials from environment if available
        credentials = ESPNCredentials(
            espn_s2=os.getenv('ESPN_S2'),
            swid=os.getenv('SWID')
        )
        api_tool = ESPNAPITool(league_id=config.league_id, credentials=credentials)
        analysis_tool = DataAnalysisTool()
        
        # Determine investigation type and execute
        if config.investigation_type == "return_td_double_dip":
            investigation = ReturnTDDoubleDipInvestigation(api_tool, analysis_tool)
            
            # Determine data range
            start_year, end_year = config.data_range
            if season_filter:
                start_year = end_year = season_filter
            
            # Execute tasks
            player_return_tds = investigation.identify_player_return_tds(
                start_year, end_year,
                output_path=data_dir / "rffl_return_td_players_2011_2025.csv"
            )
            
            dst_return_tds = investigation.identify_dst_return_tds(
                start_year, end_year,
                output_path=data_dir / "rffl_dst_return_tds_2011_2025.csv"
            )
            
            double_dips = investigation.cross_reference_double_dips(
                player_return_tds,
                dst_return_tds,
                output_path=data_dir / "rffl_double_dip_events.csv"
            )
            
            double_dips_with_status = investigation.analyze_starter_status(double_dips)
            
            counterfactual = investigation.counterfactual_analysis(
                player_return_tds,
                dst_return_tds,
                output_path=data_dir / "rffl_missed_opportunities.csv"
            )
            
            summary_stats = investigation.generate_summary_stats(double_dips_with_status)
            
            return {
                "player_return_tds": player_return_tds,
                "dst_return_tds": dst_return_tds,
                "double_dips": double_dips_with_status,
                "counterfactual": counterfactual,
                "summary_stats": summary_stats,
                "data_files": [
                    "rffl_return_td_players_2011_2025.csv",
                    "rffl_dst_return_tds_2011_2025.csv",
                    "rffl_double_dip_events.csv",
                    "rffl_missed_opportunities.csv"
                ]
            }
        else:
            raise ValueError(f"Unknown investigation type: {config.investigation_type}")
    
    def generate_report(self, config: InvestigationConfig, results: dict) -> Path:
        """
        Generate findings report.
        
        Args:
            config: Investigation configuration
            results: Investigation results from execute_investigation()
        
        Returns:
            Path to generated report file
        """
        output_dir = self.investigations_root / config.case_id
        
        # Format findings from results
        summary_stats = results.get("summary_stats", {})
        
        # Get actual player return TD count from source data
        player_return_tds = results.get("player_return_tds", pd.DataFrame())
        total_player_return_tds = len(player_return_tds) if not player_return_tds.empty else 0
        
        # Calculate percentage based on actual return TD count
        pct_double_dip = (
            (summary_stats.get('total_double_dip_started', 0) / max(total_player_return_tds, 1)) * 100
        ) if total_player_return_tds > 0 else 0.0
        
        findings = f"""
### Summary Statistics

- **Total Return TDs (RFFL-rostered players):** {total_player_return_tds}
- **Double-Dip Events (rostered):** {summary_stats.get('total_double_dip_rostered', 0)}
- **Double-Dip Events (both started):** {summary_stats.get('total_double_dip_started', 0)}
- **Percentage with Double-Dip Benefit:** {pct_double_dip:.2f}%

### Benefiting Teams

{self._format_benefiting_teams(summary_stats.get('benefiting_teams', []))}
"""
        
        analysis = (
            f"The investigation found {total_player_return_tds} return TD events "
            f"scored by RFFL-rostered players in the analyzed period. "
            f"Of these, {summary_stats.get('total_double_dip_rostered', 0)} occurred "
            f"where the same owner rostered both the player and their team's D/ST. "
            f"However, only {summary_stats.get('total_double_dip_started', 0)} of these "
            f"resulted in actual double-dip benefit (both in starting lineup)."
        )
        
        conclusion = (
            f"Based on the forensic analysis, the return TD 'double dip' mechanic "
            f"has occurred {summary_stats.get('total_double_dip_started', 0)} times "
            f"in RFFL history where both the player and D/ST were started by the same owner. "
            f"This represents {pct_double_dip:.2f}% of all return TDs, "
            f"suggesting the mechanic is rare and does not appear to be exploitable."
        )
        
        report_data = ReportData(
            executive_summary=(
                f"This investigation analyzed return TD scoring events from {config.data_range[0]}-{config.data_range[1]} "
                f"to determine if the 'double dip' mechanic (player + D/ST both scoring 6 points for the same return TD) "
                f"creates an exploitable advantage. "
                f"Found {summary_stats.get('total_double_dip_started', 0)} instances where both player and D/ST were "
                f"started by the same owner, representing {pct_double_dip:.2f}% of all return TDs."
            ),
            findings=findings.strip(),
            analysis=analysis.strip(),
            conclusion=conclusion.strip(),
            data_files=results.get("data_files", []),
            data_quality_notes="See per-season quality flags in data outputs"
        )
        
        reporter = ForensicReporter(config)
        report_path = reporter.save(report_data, output_dir)
        
        return report_path
    
    def _format_benefiting_teams(self, teams: list[dict]) -> str:
        """Format benefiting teams list for report."""
        if not teams:
            return "None identified."
        
        lines = []
        for team in teams:
            team_code = team.get('rffl_team_code', team.get('team_code', 'Unknown'))
            count = team.get('count', 0)
            total_points = team.get('total_points', 0.0)
            lines.append(
                f"- **{team_code}:** {count} occurrence(s), "
                f"{total_points:.1f} total points"
            )
        return "\n".join(lines)

