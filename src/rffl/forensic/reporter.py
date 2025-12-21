"""
Report generator for forensic investigation findings.
Outputs legal memo format addressed to Commissioner.
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .schemas import InvestigationConfig, InvestigationStatus


MEMO_TEMPLATE = """# MEMORANDUM

**TO:** Commissioner (PCX)  
**FROM:** RFFL Forensic Investigation Agent  
**RE:** {case_id} — {title}  
**DATE:** {date}  

---

## EXECUTIVE SUMMARY

{executive_summary}

---

## BACKGROUND

### Inquiry Origin

**Petitioner:** {petitioner_team_code}  
**Date Filed:** {petitioner_date}  
**Category:** {category}

### Original Question

{inquiry_full_text}

### Prior Analysis

{prior_analysis_summary}

**Validation Required:**

{validation_required_list}

---

## METHODOLOGY

### Data Sources

- ESPN Fantasy Football API (League ID: {league_id})
- RFFL Team Owner Registry (canonical)
- Historical boxscores and roster data

### Investigation Period

- **Seasons Analyzed:** {start_year}–{end_year}
- **Data Quality Notes:** {data_quality_notes}

### Tasks Executed

{tasks_list}

---

## FINDINGS

{findings}

---

## ANALYSIS

{analysis}

---

## CONCLUSION

{conclusion}

---

## APPENDICES

### Data Files Generated

{data_files_list}

### Investigation Metadata

- **Case ID:** {case_id}
- **Status:** {status}
- **Investigator:** {investigator}
- **Commissioner Approved:** {commissioner_approved}
- **Report Generated:** {report_generated_at}

---

**Document ID:** {case_id}  
**Version:** 1.0.0  
**Status:** {status}  
**Authority:** League Commissioner (PCX)
"""


@dataclass
class ReportData:
    """Structured data for report generation."""
    executive_summary: str
    findings: str
    analysis: str
    conclusion: str
    data_files: list[str]
    data_quality_notes: str = "See per-season quality flags in data outputs"


class ForensicReporter:
    """Generate legal memo format reports."""
    
    def __init__(self, config: InvestigationConfig):
        self.config = config
    
    def generate(self, report_data: ReportData) -> str:
        """Generate the full report markdown."""
        
        # Format validation required as bullet list
        validation_list = "\n".join(
            f"- {item}" 
            for item in (self.config.prior_analysis.validation_required 
                        if self.config.prior_analysis else [])
        ) or "- None specified"
        
        # Format tasks as numbered list
        tasks_list = "\n".join(
            f"{i+1}. **{task.id}:** {task.description} "
            f"({'✅ Complete' if task.completed else '⏳ Pending'})"
            for i, task in enumerate(self.config.tasks)
        )
        
        # Format data files
        data_files_list = "\n".join(f"- `{f}`" for f in report_data.data_files) or "- None"
        
        return MEMO_TEMPLATE.format(
            case_id=self.config.case_id,
            title=self.config.title,
            date=datetime.now().strftime("%Y-%m-%d"),
            executive_summary=report_data.executive_summary,
            petitioner_team_code=self.config.petitioner.team_code,
            petitioner_date=self.config.petitioner.submitted_at.strftime("%Y-%m-%d"),
            category=self.config.category.value,
            inquiry_full_text=self.config.inquiry.full_text,
            prior_analysis_summary=(
                self.config.prior_analysis.findings_summary 
                if self.config.prior_analysis else "None provided"
            ),
            validation_required_list=validation_list,
            league_id=self.config.league_id,
            start_year=self.config.data_range[0],
            end_year=self.config.data_range[1],
            data_quality_notes=report_data.data_quality_notes,
            tasks_list=tasks_list,
            findings=report_data.findings,
            analysis=report_data.analysis,
            conclusion=report_data.conclusion,
            data_files_list=data_files_list,
            status=self.config.status.value,
            investigator=self.config.investigator,
            commissioner_approved="Yes" if self.config.commissioner_approved else "No",
            report_generated_at=datetime.now().isoformat()
        )
    
    def save(self, report_data: ReportData, output_dir: Path) -> Path:
        """Generate and save report to file."""
        report_content = self.generate(report_data)
        output_path = output_dir / "report.md"
        output_path.write_text(report_content)
        return output_path

