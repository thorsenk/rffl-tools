"""
RFFL Forensic Investigation Module

Provides tools for conducting data-driven investigations of league queries,
generating professional findings reports for Commissioner review.
"""

from .schemas import (
    InvestigationCategory,
    InvestigationStatus,
    InvestigationConfig,
    Petitioner,
    Inquiry,
    InvestigationTask,
    PriorAnalysis,
    OutputConfig,
)
from .agent import ForensicAgent
from .tools import ESPNAPITool, DataAnalysisTool, SEASON_DATA_QUALITY
from .reporter import ForensicReporter, ReportData
from .stat_ids import PlayerStatID, DSTStatID, validate_stat_ids

__all__ = [
    # Schemas
    "InvestigationCategory",
    "InvestigationStatus", 
    "InvestigationConfig",
    "Petitioner",
    "Inquiry",
    "InvestigationTask",
    "PriorAnalysis",
    "OutputConfig",
    # Agent
    "ForensicAgent",
    # Tools
    "ESPNAPITool",
    "DataAnalysisTool",
    "SEASON_DATA_QUALITY",
    # Reporter
    "ForensicReporter",
    "ReportData",
    # Stat IDs
    "PlayerStatID",
    "DSTStatID",
    "validate_stat_ids",
]

