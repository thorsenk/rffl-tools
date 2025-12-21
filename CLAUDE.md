# CLAUDE.md - Agent Context for RFFL Tools

## Project Overview

RFFL Tools is a unified repository combining `rffl-boxscores` (data processing engine) and `rffl-recipes` (orchestration layer) into a single, streamlined toolkit for ESPN Fantasy Football data operations.

## Architecture

### Module Structure

- `rffl.core` - Data processing engine (export, validation, etc.)
- `rffl.recipes` - Recipe orchestration (runner, wizard, loader)
- `rffl.live` - Live scoring features

### Key Design Principles

1. **Direct Python Imports**: No subprocess calls between modules
2. **Path Resolution**: All paths relative to repository root (no DATA_ROOT)
3. **Centralized ESPN Client**: Single `api.py` module for all ESPN API interactions
4. **Exception Hierarchy**: Clean error handling with custom exceptions

## Development Guidelines

- Python 3.11+ required
- Use type hints throughout
- Follow PEP 8 style guide (enforced by ruff/black)
- Write tests for all new functionality
- Update documentation when adding features

## Inbox Folder - CRITICAL CLEANUP REQUIREMENT

**⚠️ MANDATORY: When processing files from `inbox/` folder, you MUST clean up after completion.**

The `inbox/` folder is a staging area for files awaiting processing. After processing files:

1. **Move processed files** to their proper destination (e.g., `data/`, `investigations/`, `docs/`)
2. **Delete temporary files** that are no longer needed
3. **ALWAYS verify** the inbox is clean before completing your task

### Using Inbox Utilities

Use the provided utilities in `rffl.core.inbox`:

```python
from rffl.core.inbox import process_inbox_files, ensure_inbox_clean, move_inbox_file

# Process files with automatic cleanup checking
def process_file(file_path: Path):
    # Your processing logic
    move_inbox_file(file_path, destination_path)

process_inbox_files(process_file)

# Verify cleanup
ensure_inbox_clean()  # Raises if inbox not clean
```

### CLI Commands

- `rffl utils inbox-status` - Check what files are in inbox
- `rffl utils inbox-clean` - Verify inbox is clean

**Failure to clean up the inbox is considered an incomplete task.**

## Common Tasks

### Adding a New Command

1. Create function in appropriate module (`rffl.core.*` or `rffl.live.*`)
2. Add CLI command in `rffl/cli.py`
3. Add tests in `tests/`
4. Update documentation

### Migrating from Old Repos

See [MIGRATION.md](MIGRATION.md) for detailed migration instructions.

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src/rffl tests/

# Run specific test file
pytest tests/test_export.py
```

## Code Style

- Format: `black src/ tests/`
- Lint: `ruff check src/ tests/`
- Type check: `mypy src/`

