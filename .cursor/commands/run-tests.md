# Run Tests

## Purpose

Execute the test suite to verify code functionality and catch regressions.

## When to Use

- ✅ Before committing code changes
- ✅ After modifying core functionality
- ✅ When debugging issues
- ✅ As part of continuous integration
- ✅ After refactoring code

## Quick Test Run

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src/rffl tests/

# Run specific test file
pytest tests/test_export.py
```

## Detailed Steps

### 1. Run All Tests

```bash
# Basic test run
pytest tests/

# Verbose output
pytest tests/ -v

# Show print statements
pytest tests/ -s
```

### 2. Run with Coverage

```bash
# Generate coverage report
pytest --cov=src/rffl tests/

# Coverage with HTML report
pytest --cov=src/rffl --cov-report=html tests/
# Then open htmlcov/index.html
```

### 3. Run Specific Tests

```bash
# Run specific test file
pytest tests/test_api.py

# Run specific test function
pytest tests/test_api.py::test_credentials_is_authenticated

# Run tests matching pattern
pytest -k "test_export" tests/
```

### 4. Run Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run tests with markers
pytest -m "not slow" tests/
```

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_api.py          # API client tests
├── test_export.py       # Export functionality tests
├── test_korm_processor.py # KORM processor tests
├── test_loader.py      # Recipe loader tests
├── test_validation.py  # Validation tests
├── fixtures/           # Test data fixtures
├── integration/        # Integration tests
└── unit/               # Unit tests
```

## Common Test Commands

### Watch Mode (if pytest-watch installed)

```bash
# Auto-run tests on file changes
ptw tests/
```

### Parallel Execution

```bash
# Run tests in parallel (if pytest-xdist installed)
pytest tests/ -n auto
```

### Stop on First Failure

```bash
# Stop after first test failure
pytest tests/ -x

# Stop after N failures
pytest tests/ --maxfail=3
```

## Coverage Goals

**Current Coverage**: ~10.5% (4 test files for 38 Python files)

**Target Coverage**: 60%+ of modules

### Coverage by Module

- ✅ `test_api.py` - API client tests
- ✅ `test_loader.py` - Recipe loader tests
- ✅ `test_validation.py` - Validation tests
- ⚠️ Missing: `core/export.py`, `core/transactions.py`, `core/draft.py`
- ⚠️ Missing: `recipes/runner.py`, `live/` modules

## Debugging Failed Tests

### Run with Debugger

```bash
# Drop into debugger on failure
pytest tests/ --pdb

# Drop into debugger on first failure
pytest tests/ -x --pdb
```

### Show Local Variables

```bash
# Show local variables in traceback
pytest tests/ -l
```

### Verbose Output

```bash
# Very verbose output
pytest tests/ -vv

# Show test names only
pytest tests/ --collect-only
```

## Test Fixtures

Fixtures are defined in `tests/conftest.py`:

- `mock_espn_client` - Mock ESPN client
- `sample_boxscores_path` - Sample boxscores CSV
- `repo_root` - Temporary repository root
- `sample_recipe_path` - Sample recipe YAML
- `credentials` - Sample ESPN credentials

## Writing New Tests

### Test File Structure

```python
"""Tests for module_name."""

import pytest
from rffl.module import function_to_test

def test_function_name():
    """Test description."""
    result = function_to_test()
    assert result == expected_value
```

### Test Naming Convention

- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

## Continuous Integration

Tests should pass in CI/CD pipeline:

```bash
# CI-friendly command
pytest tests/ --cov=src/rffl --cov-report=xml --junitxml=test-results.xml
```

## Related Commands

- `code-quality-check.md` - Run code quality checks
- `git-workflow.md` - Git commit workflow
- `docs-update.md` - Update documentation

## Success Criteria

✅ All tests pass  
✅ Coverage meets target (60%+)  
✅ No test warnings  
✅ Tests run in reasonable time (< 30 seconds)

## Troubleshooting

### Import Errors

```bash
# Ensure package is installed in development mode
pip install -e ".[dev]"
```

### Missing Dependencies

```bash
# Install test dependencies
pip install -e ".[dev]"
```

### Test Data Issues

- Check `tests/fixtures/` for required test data
- Verify `conftest.py` fixtures are properly configured

