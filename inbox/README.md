# Inbox / Capture Folder

**Staging area for files awaiting processing.**

## Workflow

1. **Drop files here** - Place any files that need processing in this folder
2. **Read inbox** - Use `rffl utils read-inbox` to see what files need processing
3. **Process files** - Complete the required tasks
4. **Clean inbox** - Use `rffl utils clean-inbox` to move or delete processed files

## CLI Commands

### Read Inbox
```bash
# List files in inbox
rffl utils read-inbox

# List files with preview (first 20 lines)
rffl utils read-inbox --preview
```

### Clean Inbox
```bash
# Interactive mode - prompts for each file's destination
rffl utils clean-inbox

# Delete all files
rffl utils clean-inbox --delete --force

# Move all files to a directory
rffl utils clean-inbox --move-to investigations/RFFL-INQ-2025-001 --force
```

### Check Status
```bash
# Quick status check (alias for read-inbox)
rffl utils inbox-status
```

## Rules for Agents/Scripts

**CRITICAL: Always clean up after processing!**

1. ✅ Use `rffl utils read-inbox` to see what needs processing
2. ✅ Process the files (complete your task)
3. ✅ Use `rffl utils clean-inbox` to remove processed files
4. ❌ **DON'T** leave processed files in the inbox
5. ❌ **DON'T** commit inbox contents to git (they're ignored)

**If you processed files but didn't run `clean-inbox`, you've failed to complete the task.**

## File Types

This folder accepts any file type:
- CSV files for data import
- JSON/YAML configuration files
- Text files for analysis
- Any other files that need processing

## Git Ignore

Files in this folder are ignored by git (except this README). The folder structure is preserved via `.gitkeep`.

