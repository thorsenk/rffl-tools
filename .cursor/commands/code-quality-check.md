# Code Quality Check

## Purpose

Run all code quality checks to ensure code meets project standards before committing.

## When to Use

- ✅ Before committing code changes
- ✅ After making significant code modifications
- ✅ When preparing a pull request
- ✅ As part of pre-commit workflow

## Quick Check

```bash
# Run all checks
ruff check src/ tests/
black --check src/ tests/
mypy src/
```

## Detailed Steps

### 1. Linting (Ruff)

```bash
# Check for linting errors
ruff check src/ tests/

# Auto-fix fixable issues
ruff check --fix src/ tests/
```

**What it checks:**
- PEP 8 style violations
- Import organization
- Unused variables/imports
- Code complexity issues

### 2. Formatting (Black)

```bash
# Check formatting without changing files
black --check src/ tests/

# Format files (if needed)
black src/ tests/
```

**What it checks:**
- Code formatting consistency
- Line length (100 chars)
- String quote style

### 3. Type Checking (MyPy)

```bash
# Run type checker
mypy src/

# With more verbose output
mypy src/ --verbose
```

**What it checks:**
- Type annotation correctness
- Type compatibility
- Missing type hints
- Incorrect type usage

## Fixing Issues

### Auto-fixable Issues

```bash
# Fix linting issues automatically
ruff check --fix src/ tests/

# Format code automatically
black src/ tests/
```

### Manual Fixes Required

1. **Type errors**: Fix type annotations in source code
2. **Complex logic**: Refactor complex functions flagged by ruff
3. **Import issues**: Organize imports according to project standards

## Verification

After running checks, verify:

```bash
# All checks should pass with exit code 0
ruff check src/ tests/ && echo "✅ Linting passed"
black --check src/ tests/ && echo "✅ Formatting passed"
mypy src/ && echo "✅ Type checking passed"
```

## Common Issues

### MyPy Errors

- **Missing type hints**: Add type annotations to function parameters and return types
- **Import errors**: Add `# type: ignore[import-untyped]` for third-party libraries (pandas, requests, espn_api)
- **None handling**: Use `int | None` union types instead of assigning None to int fields

### Ruff Errors

- **Unused imports**: Remove or use the imports
- **Line too long**: Break into multiple lines or use Black to auto-format
- **Complex functions**: Consider refactoring into smaller functions

### Black Issues

- **Formatting differences**: Run `black src/ tests/` to auto-format
- **Line length**: Black will wrap lines at 100 characters

## Integration with Git

### Pre-commit Hook (Optional)

```bash
# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
ruff check src/ tests/ && black --check src/ tests/ && mypy src/
EOF
chmod +x .git/hooks/pre-commit
```

## Related Commands

- `run-tests.md` - Run test suite
- `git-workflow.md` - Git commit workflow
- `docs-update.md` - Update documentation

## Configuration

Quality checks are configured in:
- `pyproject.toml` - Ruff, Black, MyPy, Pytest settings
- `.ruff.toml` (if exists) - Additional Ruff configuration

## Success Criteria

✅ All linting checks pass  
✅ Code is properly formatted  
✅ Type checking passes  
✅ No errors or warnings (or acceptable warnings documented)

