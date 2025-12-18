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

