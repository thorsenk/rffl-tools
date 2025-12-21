# Investigation Setup

## Purpose

Create a new forensic investigation case with proper structure and documentation.

## When to Use

- ✅ Starting a new forensic investigation
- ✅ Creating a case file for data analysis
- ✅ Setting up investigation workflow
- ✅ Documenting investigation requirements

## Quick Setup

```bash
# Create investigation directory structure
mkdir -p investigations/RFFL-INQ-2025-XXX
cd investigations/RFFL-INQ-2025-XXX

# Create investigation.yaml template
# Create README.md
# Create data/ directory
```

## Detailed Steps

### 1. Create Investigation Directory

```bash
# Determine next case ID
# Format: RFFL-INQ-YYYY-XXX (e.g., RFFL-INQ-2025-001)

# Create directory
mkdir -p investigations/RFFL-INQ-2025-XXX
cd investigations/RFFL-INQ-2025-XXX
```

### 2. Create Investigation Configuration

Create `investigation.yaml`:

```yaml
case_id: RFFL-INQ-2025-XXX
title: "Investigation Title"
category: "scoring"  # scoring, transactions, lineup, other
description: "Brief description of investigation"
commissioner_approved: false
data_range: [2011, 2025]  # [start_year, end_year]

tasks:
  - id: task_1
    description: "Task description"
    completed: false
    data_sources: ["boxscores", "transactions"]
    analysis_type: "extraction"  # extraction, validation, comparison
```

**Categories:**
- `scoring` - Scoring-related issues
- `transactions` - Transaction-related issues
- `lineup` - Lineup compliance issues
- `other` - Other investigation types

**Analysis Types:**
- `extraction` - Extract specific data
- `validation` - Validate data consistency
- `comparison` - Compare datasets
- `statistical` - Statistical analysis

### 3. Create README.md

```markdown
# RFFL-INQ-2025-XXX: Investigation Title

## Overview
Brief description of the investigation.

## Objectives
- Objective 1
- Objective 2

## Data Sources
- boxscores.csv (2019-2025)
- transactions.csv (2019-2025)
- draft.csv (all seasons)

## Methodology
How the investigation will be conducted.

## Findings
(To be filled in during investigation)

## Conclusion
(To be filled in after investigation)
```

### 4. Create Data Directory

```bash
# Create data directory for investigation outputs
mkdir -p data

# Create scripts directory for investigation scripts
mkdir -p scripts
```

### 5. Initialize Investigation

```bash
# List investigations
rffl forensic list

# Validate investigation structure
# (Check that investigation.yaml is valid)

# Dry run investigation
rffl forensic investigate RFFL-INQ-2025-XXX --dry-run
```

## Investigation Structure

```
investigations/
└── RFFL-INQ-2025-XXX/
    ├── investigation.yaml      # Investigation configuration
    ├── README.md              # Investigation documentation
    ├── data/                  # Investigation data outputs
    │   └── *.csv
    ├── scripts/               # Investigation scripts
    │   └── *.py
    ├── report.md              # Investigation report (generated)
    └── AAR_*.md               # After-action review (optional)
```

## Example Investigation

See `investigations/RFFL-INQ-2025-001/` for reference:

- **Case**: Return TD double scoring investigation
- **Category**: Scoring
- **Data Range**: 2011-2025
- **Tasks**: Extract return TDs, identify double-scoring events

## Running Investigation

```bash
# Execute investigation
rffl forensic investigate RFFL-INQ-2025-XXX

# Execute for specific season (rate limit management)
rffl forensic investigate RFFL-INQ-2025-XXX --season 2024

# Dry run (show plan without executing)
rffl forensic investigate RFFL-INQ-2025-XXX --dry-run

# Force execution (skip commissioner approval)
rffl forensic investigate RFFL-INQ-2025-XXX --force
```

## Investigation Workflow

1. **Setup** - Create investigation structure (this command)
2. **Planning** - Define tasks and methodology
3. **Approval** - Get commissioner approval (set `commissioner_approved: true`)
4. **Execution** - Run investigation
5. **Analysis** - Analyze results
6. **Reporting** - Generate report
7. **AAR** - Create after-action review

## Commissioner Approval

Before executing, investigations require commissioner approval:

```yaml
# In investigation.yaml
commissioner_approved: true  # Set to true after approval
```

Or use `--force` flag to bypass (not recommended for production).

## Investigation Scripts

Create Python scripts in `scripts/` directory:

```python
#!/usr/bin/env python3
"""Investigation script for RFFL-INQ-2025-XXX."""

import pandas as pd
from pathlib import Path

# Load data
boxscores = pd.read_csv("../../data/seasons/2024/boxscores.csv")

# Perform analysis
# ...

# Save results
results.to_csv("data/investigation_results.csv", index=False)
```

## Data Sources

Available data sources for investigations:

- `data/seasons/{YEAR}/boxscores.csv` - Detailed boxscores (2019+)
- `data/seasons/{YEAR}/transactions.csv` - Transactions (2019+)
- `data/seasons/{YEAR}/draft.csv` - Draft results (all seasons)
- `data/seasons/{YEAR}/stat_corrections.csv` - Stat corrections (2019+)
- `data/seasons/{YEAR}/h2h.csv` - Head-to-head (2011-2018)

## Related Commands

- `forensic-execute.md` - Execute investigation
- `session-aar.md` - Create after-action review
- `docs-update.md` - Update documentation

## Success Criteria

✅ Investigation directory created  
✅ investigation.yaml configured  
✅ README.md created  
✅ Data directory structure ready  
✅ Investigation validates successfully  
✅ Dry run shows correct plan

