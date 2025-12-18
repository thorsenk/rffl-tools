# RFFL Tools

Unified RFFL Fantasy Football data toolkit - export, validate, and automate ESPN Fantasy Football data operations.

## Overview

RFFL Tools combines the data processing engine (`rffl-boxscores`) with the orchestration layer (`rffl-recipes`) into a single, unified repository. This eliminates cross-repository dependencies, removes the DATA_ROOT configuration requirement, and provides a streamlined CLI experience.

## Features

- **Export**: Fetch ESPN fantasy football boxscores and export to CSV format
- **Validate**: Verify data consistency and completeness
- **Recipes**: Orchestrated workflows with YAML-based recipe definitions
- **Live Scoring**: Real-time score tracking and reporting
- **Clean Data**: Normalized slot positions, injury status, and bye week information

## Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd rffl-tools

# Install in development mode
pip install -e ".[dev]"
```

### Requirements

- Python 3.11+
- Virtual environment (recommended)

## Quick Start

```bash
# Export boxscores
rffl core export --league 323196 --year 2024 --fill-missing-slots

# Export transactions (requires authentication - set ESPN_S2 and SWID env vars)
rffl core transactions --league 323196 --year 2024

# Export draft data
rffl core draft --league 323196 --year 2024

# Run a recipe
rffl recipe run recipes/local/my-recipe.yaml

# Live scores
rffl live scores --season 2025
```

## CLI Commands

### Core Commands (`rffl core`)

- **`export`** - Export boxscores with detailed player-level data
  ```bash
  rffl core export --year 2024 --fill-missing-slots --require-clean
  ```

- **`draft`** - Export draft data
  ```bash
  rffl core draft --year 2024
  ```

- **`transactions`** - Export transaction history (2019+ only, requires auth)
  ```bash
  rffl core transactions --year 2024
  ```

- **`h2h`** - Export head-to-head matchup results
  ```bash
  rffl core h2h --year 2024
  ```

- **`historical-rosters`** - Export end-of-season rosters (2011-2018 only)
  ```bash
  rffl core historical-rosters --year 2018
  ```

- **`validate`** - Validate boxscore data consistency
  ```bash
  rffl core validate data/seasons/2024/boxscores.csv
  ```

- **`validate-lineup`** - Validate RFFL lineup compliance
  ```bash
  rffl core validate-lineup data/seasons/2024/boxscores.csv
  ```

### Recipe Commands (`rffl recipe`)

- **`run`** - Execute a recipe workflow
  ```bash
  rffl recipe run recipes/baselines/weekly-enhanced-boxscores.yaml
  ```

- **`wizard`** - Interactive recipe creation wizard
  ```bash
  rffl recipe wizard
  ```

- **`list`** - List available recipes
  ```bash
  rffl recipe list
  ```

- **`validate`** - Validate recipe file
  ```bash
  rffl recipe validate recipes/local/my-recipe.yaml
  ```

- **`migrate`** - Migrate recipe from old format
  ```bash
  rffl recipe migrate recipes/local/my-recipe.yaml
  ```

### Live Commands (`rffl live`)

- **`scores`** - Fetch live scores
  ```bash
  rffl live scores --season 2025 --scoring-period 1
  ```

- **`report`** - Generate live matchup report
  ```bash
  rffl live report --season 2025 --scoring-period 1
  ```

- **`korm`** - KORM-specific live report
  ```bash
  rffl live korm 1 --season 2025
  ```

For detailed command options, use `--help`:
```bash
rffl core export --help
rffl recipe run --help
rffl live scores --help
```

## Authentication

Some features (like transaction export) require ESPN authentication credentials:

1. Copy `.env.example` to `.env`
2. Extract `ESPN_S2` and `SWID` from your browser cookies when logged into ESPN Fantasy Football
3. Add them to your `.env` file

See `.env.example` for detailed instructions.

## Documentation

- [CLAUDE.md](CLAUDE.md) - Agent context and development guide
- [MIGRATION.md](MIGRATION.md) - Migration guide from separate repositories
- [scripts/README.md](scripts/README.md) - Utility scripts documentation
- [templates/seasons/README.md](templates/seasons/README.md) - Season data structure and templates

## License

MIT License - see [LICENSE](LICENSE) for details.

