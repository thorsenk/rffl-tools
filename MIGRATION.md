# Migration Guide: rffl-boxscores + rffl-recipes → rffl-tools

This guide documents the migration from the separate `rffl-boxscores` and `rffl-recipes` repositories to the unified `rffl-tools` repository.

## Overview

The unified `rffl-tools` repository combines:
- **rffl-boxscores**: Data processing engine (export, validation, etc.)
- **rffl-recipes**: Orchestration layer (recipes, wizard, live scoring)

## Key Changes

### 1. No More DATA_ROOT

**Before**:
```bash
export DATA_ROOT=/path/to/rffl-boxscores
rffl-recipes run recipes/local/my-recipe.yaml
```

**After**:
```bash
cd rffl-tools
rffl recipe run recipes/local/my-recipe.yaml
```

All paths are now relative to the `rffl-tools` repository root.

### 2. Unified CLI

**Before**:
- `rffl-bs export ...` (from rffl-boxscores)
- `rffl-recipes run ...` (from rffl-recipes)

**After**:
- `rffl export ...` (unified command)
- `rffl recipe run ...` (unified command)

### 3. Direct Imports

Recipes now use direct Python imports instead of subprocess calls, resulting in:
- Faster execution
- Better error messages
- Type safety
- Easier debugging

## Migration Steps

### Step 1: Update Recipe Paths

If you have existing recipes with `${DATA_ROOT}` paths, migrate them:

```bash
cd rffl-tools
rffl recipe migrate recipes/local/my-recipe.yaml
```

Or migrate all recipes:
```bash
rffl recipe migrate recipes/local/ --all
```

### Step 2: Update Scripts

Update any shell scripts that reference:
- `rffl-bs` → `rffl`
- `rffl-recipes` → `rffl recipe`
- `${DATA_ROOT}` → relative paths

### Step 3: Update Environment Variables

Remove `DATA_ROOT` from your `.env` file. The `LEAGUE` variable is still used:

```bash
# .env
LEAGUE=323196
# DATA_ROOT no longer needed
```

## Breaking Changes

1. **CLI Commands**: `rffl-bs` and `rffl-recipes` are replaced by `rffl`
2. **Path Resolution**: All paths must be relative to repository root
3. **Recipe Format**: `${DATA_ROOT}` paths are deprecated (but still work with warnings)

## Rollback Plan

If you need to revert to the old repositories:

1. Old repositories remain untouched (reference only)
2. Set `DATA_ROOT` back to point to `src/rffl-boxscores`
3. Use `rffl-bs` and `rffl-recipes` commands from old repos

## Questions?

See [CLAUDE.md](CLAUDE.md) for development context or check the [plan document](../.cursor/plans/rffl_unified_architecture_ff841bab.plan.md) for detailed architecture decisions.

