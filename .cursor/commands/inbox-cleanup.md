# Inbox Cleanup

## Purpose

Process and clean up files from the inbox folder after completing tasks.

## When to Use

- ✅ After processing files from inbox
- ✅ Before committing changes
- ✅ As part of task completion workflow
- ✅ When inbox folder has accumulated files

## CRITICAL: Always Clean Up

**⚠️ MANDATORY: When processing files from `inbox/` folder, you MUST clean up after completion.**

Failure to clean up the inbox is considered an incomplete task.

## Quick Cleanup

```bash
# Check inbox status
rffl utils read-inbox

# Clean inbox interactively
rffl utils clean-inbox
```

## Detailed Workflow

### 1. Check Inbox Status

```bash
# List files in inbox
rffl utils read-inbox

# List with preview (first 20 lines)
rffl utils read-inbox --preview

# Quick status check
rffl utils inbox-status
```

**What to check:**
- What files are in the inbox
- File types and sizes
- Whether files need processing

### 2. Process Files

Process files according to their purpose:

- **CSV files** → Move to `data/` or `investigations/`
- **JSON files** → Process and move to appropriate location
- **Documentation** → Move to `docs/` or appropriate folder
- **Temporary files** → Delete after processing

### 3. Clean Inbox

#### Interactive Mode (Recommended)

```bash
# Interactive cleanup - prompts for each file
rffl utils clean-inbox
```

**Options for each file:**
- Move to specific directory
- Delete file
- Skip (leave in inbox)

#### Automated Cleanup

```bash
# Delete all files (use with caution)
rffl utils clean-inbox --delete --force

# Move all files to specific directory
rffl utils clean-inbox --move-to investigations/RFFL-INQ-2025-XXX/data --force

# Move to archive
rffl utils clean-inbox --move-to data/archive/$(date +%Y-%m-%d) --force
```

### 4. Verify Cleanup

```bash
# Verify inbox is clean
rffl utils inbox-clean

# Or check manually
ls -la inbox/
# Should only show README.md and .gitkeep
```

## Inbox Rules

### For Agents/Scripts

**CRITICAL: Always clean up after processing!**

1. ✅ Use `rffl utils read-inbox` to see what needs processing
2. ✅ Process the files (complete your task)
3. ✅ Use `rffl utils clean-inbox` to remove processed files
4. ❌ **DON'T** leave processed files in the inbox
5. ❌ **DON'T** commit inbox contents to git (they're ignored)

**If you processed files but didn't run `clean-inbox`, you've failed to complete the task.**

## File Processing Guidelines

### CSV Files

```bash
# Move to data directory
rffl utils clean-inbox --move-to data/seasons/2024/ --force

# Move to investigation data
rffl utils clean-inbox --move-to investigations/RFFL-INQ-2025-XXX/data/ --force
```

### JSON Files

```bash
# Process JSON and move to appropriate location
# Usually move to investigations/ or data/archive/
rffl utils clean-inbox --move-to investigations/RFFL-INQ-2025-XXX/data/ --force
```

### Documentation Files

```bash
# Move to docs directory
rffl utils clean-inbox --move-to docs/ --force

# Move to specific doc folder
rffl utils clean-inbox --move-to docs/aars/ --force
```

### Temporary Files

```bash
# Delete temporary files
rffl utils clean-inbox --delete --force
```

## Python API Usage

If writing scripts that process inbox files:

```python
from pathlib import Path
from rffl.core.inbox import (
    list_inbox_files,
    ensure_inbox_clean,
    move_inbox_file,
    delete_inbox_file
)

# List files
files = list_inbox_files()

# Process each file
for file_path in files:
    # Your processing logic
    process_file(file_path)
    
    # Move to destination
    move_inbox_file(file_path, destination_path)
    # Or delete
    # delete_inbox_file(file_path)

# Verify cleanup
ensure_inbox_clean()  # Raises if inbox not clean
```

## Git Ignore

Files in `inbox/` are ignored by git (except `README.md` and `.gitkeep`).

**Don't commit inbox contents** - they're temporary staging files.

## Common Scenarios

### Scenario 1: Processed CSV Files

```bash
# Files processed and moved to data/
rffl utils clean-inbox --move-to data/seasons/2024/ --force
```

### Scenario 2: Investigation Data

```bash
# Files processed for investigation
rffl utils clean-inbox --move-to investigations/RFFL-INQ-2025-XXX/data/ --force
```

### Scenario 3: Temporary Files

```bash
# Delete temporary files
rffl utils clean-inbox --delete --force
```

### Scenario 4: Mixed Files

```bash
# Use interactive mode to handle each file individually
rffl utils clean-inbox
```

## Verification Checklist

After cleanup, verify:

- [ ] Inbox folder is empty (except README.md and .gitkeep)
- [ ] Files moved to correct destinations
- [ ] No orphaned files left behind
- [ ] Git status shows no inbox changes (they're ignored)

## Troubleshooting

### Files Still in Inbox

```bash
# Check what's left
rffl utils read-inbox

# Force cleanup
rffl utils clean-inbox --delete --force
```

### Wrong Destination

```bash
# Files moved to wrong location - manually move them
# Then verify inbox is clean
rffl utils inbox-clean
```

## Related Commands

- `data-export-workflow.md` - Export data workflow
- `investigation-setup.md` - Setup investigation
- `git-workflow.md` - Git commit workflow

## Success Criteria

✅ Inbox folder is clean  
✅ All files processed and moved/deleted  
✅ No orphaned files  
✅ Verification passes (`rffl utils inbox-clean`)

