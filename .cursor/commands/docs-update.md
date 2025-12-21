# Documentation Update

## Purpose

Update project documentation after code changes or feature additions.

## When to Use

- ✅ After adding new CLI commands
- ✅ After modifying existing functionality
- ✅ After adding new features
- ✅ When documentation is outdated
- ✅ Before committing significant changes

## Quick Update

```bash
# Check what documentation might need updates
# Review recent code changes
git diff HEAD~1 src/rffl/cli.py

# Update relevant documentation files
```

## Documentation Files Structure

```
docs/
├── README.md                    # Docs overview
├── archive/                     # Archived docs
├── aars/                        # After-action reviews
│   ├── README.md
│   └── AAR_*.md
├── ORPHANED_FILES_CLEANUP.md
├── TEAM_DATA_COMPLETE_AUDIT.md
└── TEAM_REGISTRY_MIGRATION.md

Root level:
├── README.md                    # Main project README
├── CLAUDE.md                    # Agent context
├── MIGRATION.md                 # Migration guide
├── DETAILED_AUDIT_REPORT.md     # Repository audit
└── AUDIT_SUMMARY.md             # Audit summary
```

## Documentation Update Checklist

### 1. Main README.md

**Update when:**
- Adding new CLI commands
- Changing command syntax
- Adding new features
- Updating installation instructions

**Sections to check:**
- Features list
- CLI Commands section
- Quick Start examples
- Installation instructions
- Authentication setup

**Example:**
```markdown
## CLI Commands

### Core Commands (`rffl core`)
- **`new-command`** - Description
  ```bash
  rffl core new-command --year 2024
  ```
```

### 2. CLAUDE.md (Agent Context)

**Update when:**
- Adding new modules
- Changing architecture
- Adding new workflows
- Updating development guidelines

**Sections to check:**
- Module Structure
- Key Design Principles
- Development Guidelines
- Common Tasks
- Inbox Folder rules

**Example:**
```markdown
### Module Structure
- `rffl.core` - Data processing engine
- `rffl.forensic` - Forensic investigation tools  # NEW
```

### 3. Command-Specific Documentation

**Update when:**
- Adding new commands to a command group
- Changing command behavior
- Adding new options

**Files:**
- `scripts/README.md` - Script documentation
- `templates/seasons/README.md` - Season structure docs
- `inbox/README.md` - Inbox workflow docs

### 4. AAR Documentation

**Create when:**
- Completing significant features
- Major refactoring
- Important decisions made

**Location:** `docs/aars/`

**Use:** `session-aar.md` command template

### 5. Migration Documentation

**Update when:**
- Breaking changes
- API changes
- Configuration changes

**File:** `MIGRATION.md`

## Update Workflow

### 1. Identify Changes

```bash
# Review recent commits
git log --oneline -10

# Review changed files
git diff HEAD~1 --name-only

# Check for new commands
git diff HEAD~1 src/rffl/cli.py | grep "@.*command"
```

### 2. Update Relevant Docs

**For new CLI commands:**
1. Update `README.md` CLI Commands section
2. Add examples to Quick Start (if applicable)
3. Update `CLAUDE.md` if architecture changed

**For new scripts:**
1. Update `scripts/README.md`
2. Add usage examples
3. Document options and requirements

**For new features:**
1. Update Features section in `README.md`
2. Add to `CLAUDE.md` architecture section
3. Create AAR if significant

### 3. Verify Documentation

```bash
# Check for broken links (if using link checker)
# Verify code examples work
# Ensure formatting is correct
```

### 4. Update Version/Date

**If applicable:**
- Update version in `pyproject.toml`
- Update dates in audit reports
- Update "Last Updated" dates

## Documentation Standards

### Code Examples

```markdown
# Always use proper syntax highlighting
```bash
rffl core export --year 2024
```

# Include expected output when helpful
```bash
$ rffl core export --year 2024
✅ Wrote data/seasons/2024/boxscores.csv
```
```

### Command Documentation

```markdown
- **`command-name`** - Brief description
  ```bash
  rffl group command-name --option value
  ```
  
  **Options:**
  - `--option` - Option description
  - `--flag` - Flag description
```

### File References

```markdown
# Use relative paths
See [CLAUDE.md](CLAUDE.md) for development context

# Use full paths for clarity
See `src/rffl/core/export.py` for implementation
```

## Common Documentation Tasks

### Adding New Command Documentation

1. Add to `README.md` CLI Commands section
2. Add example to Quick Start (if commonly used)
3. Update `CLAUDE.md` Common Tasks section
4. Add to relevant command group docs

### Updating Examples

1. Verify examples still work
2. Update command syntax if changed
3. Update output examples if changed
4. Test examples before committing

### Archiving Old Docs

1. Move to `docs/archive/`
2. Update references if needed
3. Add note about archived status
4. Update `docs/README.md` if needed

## Documentation Review Checklist

- [ ] All new commands documented
- [ ] Examples are accurate and tested
- [ ] Links are correct
- [ ] Code examples use correct syntax
- [ ] Dates/versions updated if needed
- [ ] Architecture docs reflect current state
- [ ] Migration docs updated for breaking changes

## Related Commands

- `session-aar.md` - Create after-action review
- `code-quality-check.md` - Verify code quality
- `git-workflow.md` - Git commit workflow

## Success Criteria

✅ Documentation reflects current code  
✅ All new features documented  
✅ Examples are accurate  
✅ Links are working  
✅ Documentation is consistent  
✅ No outdated information

