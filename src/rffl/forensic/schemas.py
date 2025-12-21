"""
Investigation configuration schema for RFFL Forensic Agent.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class InvestigationCategory(Enum):
    """RFFL inquiry category taxonomy."""
    RULES_CLARIFY = "RULES-CLARIFY"
    RULES_SCORING = "RULES-SCORING"
    RULES_DISPUTE = "RULES-DISPUTE"
    TRADE_REVIEW = "TRADE-REVIEW"
    DATA_AUDIT = "DATA-AUDIT"
    POLICY_PROPOSE = "POLICY-PROPOSE"
    INTEGRITY = "INTEGRITY"


class InvestigationStatus(Enum):
    """Workflow state machine for investigations."""
    SUBMITTED = "submitted"
    TRIAGE = "triage"
    AWAITING_APPROVAL = "awaiting_approval"
    INVESTIGATION = "investigation"
    REVIEW = "review"
    RESOLVED = "resolved"
    NEEDS_CLARITY = "needs_clarity"


@dataclass
class Petitioner:
    team_code: str
    submitted_at: datetime


@dataclass
class Inquiry:
    summary: str
    full_text: str


@dataclass
class InvestigationTask:
    id: str
    description: str
    completed: bool = False
    output_file: Optional[str] = None


@dataclass
class PriorAnalysis:
    """Context from Claude Project preliminary analysis."""
    source: str
    findings_summary: str
    validation_required: list[str] = field(default_factory=list)


@dataclass
class OutputConfig:
    local_path: str
    github_path: Optional[str] = None
    sync_to_claude_project: bool = False


@dataclass
class InvestigationConfig:
    """Full investigation configuration."""
    case_id: str
    title: str
    category: InvestigationCategory
    petitioner: Petitioner
    inquiry: Inquiry
    investigation_type: str
    data_range: tuple[int, int]
    league_id: int
    tasks: list[InvestigationTask]
    status: InvestigationStatus = InvestigationStatus.SUBMITTED
    investigator: str = "Forensic Agent v1.0"
    commissioner_approved: bool = False
    prior_analysis: Optional[PriorAnalysis] = None
    outputs: Optional[OutputConfig] = None

