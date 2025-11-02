# Output Format Improvement Plan

## Executive Summary

This document outlines the plan to unify and improve the output formatting across all fetch/get operations in the Jira CLI. The goal is to provide a consistent, user-friendly, well-formatted default output while maintaining JSON output for scripting and automation needs.

## Current State Analysis

### Output Format Patterns

Currently, the CLI has **three different output modes** that are inconsistently applied:

1. **JSON output** - Raw API responses (used as default in most commands)
2. **Table output** - Rich-formatted tables (available via `--table` flag)
3. **Detail/Panel output** - Rich-formatted panels (available via `--detail` flag or default in some commands)

### Commands by Category

#### Issues Commands (`commands/issues.py`)

| Command | Current Default | Available Flags | Quality |
|---------|----------------|-----------------|---------|
| `search` | JSON | `--json`, `--table` | ⚠️ Default not user-friendly |
| `get` | JSON | `--json`, `--detail` | ⚠️ Default not user-friendly |
| `transitions` | JSON | `--json` (+ auto table) | ✓ Good fallback to table |
| `epic-stories` | JSON | `--json`, `--table` | ⚠️ Default not user-friendly |
| `subtasks` | JSON | `--json`, `--table` | ⚠️ Default not user-friendly |
| `watchers` | Custom format | `--json` | ✅ Excellent (bullet list + count) |

#### Projects Commands (`commands/projects.py`)

| Command | Current Default | Available Flags | Quality |
|---------|----------------|-----------------|---------|
| `list` | JSON | `--json`, `--table` | ⚠️ Default not user-friendly |
| `get` | JSON | `--json` | ❌ No rich format option |
| `issue-types` | JSON | `--json`, `--table` | ⚠️ Default not user-friendly |
| `versions` | JSON | `--json` | ❌ No rich format option |
| `components` | JSON | `--json` | ❌ No rich format option |

#### Auth Commands (`commands/auth.py`)

| Command | Current Default | Available Flags | Quality |
|---------|----------------|-----------------|---------|
| `whoami` | Rich Panel | `--json` | ✅ Excellent default |
| `test` | Success message | `--json` | ✅ Good for testing |

#### Worklog Commands (`commands/worklog.py`)

| Command | Current Default | Available Flags | Quality |
|---------|----------------|-----------------|---------|
| `list` | Custom format | `--json`, `--table` | ✅ Excellent (with totals) |
| `add` | Success message | `--json` | ✅ Appropriate for mutation |
| `update` | Success message | `--json` | ✅ Appropriate for mutation |
| `delete` | Success message | N/A | ✅ Appropriate for mutation |

### Key Problems Identified

1. **Inconsistent defaults**: 70% of fetch commands default to JSON instead of user-friendly output
2. **Confusing flags**: Users must know to use `--table` or `--detail` for readable output
3. **Poor discoverability**: New users see raw JSON and may not realize better formats exist
4. **Scripting concerns**: JSON output is useful but shouldn't be the default for human users
5. **Missing formatters**: Some commands (e.g., `projects get`, `versions`, `components`) have no rich output option

### Existing High-Quality Examples

The codebase already has excellent formatting examples we can learn from:

#### 1. **Worklog List** (Default Custom Format)
```
Worklogs for PROJ-123:

  ID: 12345
  Author: John Doe
  Time Spent: 2h 30m
  Started: 2025-01-15 09:00
  Comment: Implemented user authentication

  ID: 12346
  Author: Jane Smith
  Time Spent: 1h
  Started: 2025-01-15 14:00
  Comment: Code review

Total time logged: 3h 30m
```

#### 2. **Auth Whoami** (Rich Panel)
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Current User                               ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Display Name: John Doe                     │
│ Email: john.doe@example.com                │
│ Account ID: 5f8a9b1c2d3e4f5g6h7i8j9k       │
│ Active: Yes                                │
└────────────────────────────────────────────┘
```

#### 3. **Issue Watchers** (Custom List Format)
```
Watchers for PROJ-123:
  • John Doe (john.doe@example.com) - 5f8a9b1c2d3e4f5g6h7i8j9k
  • Jane Smith (jane.smith@example.com) - 6g9b0c3d4e5f6g7h8i9j0k1

Total watchers: 2
```

#### 4. **Issues Table** (Rich Table)
```
                                Issues
┏━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ Key     ┃ Summary       ┃ Type  ┃ Status ┃ Due Date ┃ Assignee ┃ Priority ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ PROJ-1  │ Fix login bug │ Bug   │ Open   │ None     │ John Doe │ High     │
│ PROJ-2  │ Add feature X │ Story │ Done   │ 2025-02  │ Jane S.  │ Medium   │
└─────────┴───────────────┴───────┴────────┴──────────┴──────────┴──────────┘
```

## Proposed Solution

### Design Principles

1. **Human-first defaults**: Default output should be optimized for human readability
2. **Scripting support**: JSON output always available via `--json` flag
3. **Consistency**: Similar commands should have similar output patterns
4. **Information density**: Show relevant information without overwhelming users
5. **Visual hierarchy**: Use Rich library features (colors, panels, tables) effectively

### Unified Output Strategy

#### For Single-Item Fetches (get, whoami, etc.)
**Default**: Rich Panel with structured key-value information

**Example**: `jira-cli projects get PROJ`
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Project: PROJ                              ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Name: My Project                           │
│ Key: PROJ                                  │
│ Type: software                             │
│ Lead: John Doe                             │
│ Description: Project description here      │
│ URL: https://jira.example.com/browse/PROJ  │
└────────────────────────────────────────────┘
```

#### For Multi-Item Fetches (list, search)
**Default**: Rich Table with key columns

**Example**: `jira-cli projects list`
```
                        Projects
┏━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ Key    ┃ Name           ┃ Type     ┃ Lead     ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ PROJ   │ My Project     │ software │ John Doe │
│ TEST   │ Test Project   │ business │ Jane S.  │
└────────┴────────────────┴──────────┴──────────┘
```

#### For Nested/Hierarchical Data
**Default**: Custom formatted list with proper indentation and metadata

**Example**: Already good in `worklog list`

### Flag Simplification

**Current flags** (confusing):
- `--json` - Output raw JSON
- `--table` - Output as table
- `--detail` - Output detailed view

**Proposed flags** (simplified):
- `--json` - Output raw JSON (for scripting)
- *(default)* - Well-formatted output (table/panel/custom based on data type)

### Implementation Plan

#### Phase 1: Add Missing Formatters

Create new formatting functions in `utils/formatting.py`:

```python
def format_project_detail(project: Dict[str, Any]) -> Panel:
    """Format single project as a panel."""

def format_versions_table(versions: List[Dict[str, Any]]) -> Table:
    """Format versions as a table."""

def format_components_table(components: List[Dict[str, Any]]) -> Table:
    """Format components as a table."""
```

#### Phase 2: Update Commands to Use Well-Formatted Defaults

**Issues Commands**:
- ✅ `search` - Change default from JSON to table
- ✅ `get` - Change default from JSON to panel (detail view)
- ✅ `transitions` - Keep current behavior (already good)
- ✅ `epic-stories` - Change default from JSON to table
- ✅ `subtasks` - Change default from JSON to table
- ✅ `watchers` - Keep current behavior (already excellent)

**Projects Commands**:
- ✅ `list` - Change default from JSON to table
- ✅ `get` - Change default from JSON to panel (new formatter)
- ✅ `issue-types` - Change default from JSON to table
- ✅ `versions` - Change default from JSON to table (new formatter)
- ✅ `components` - Change default from JSON to table (new formatter)

**Auth Commands**:
- ✅ `whoami` - Keep current behavior (already excellent)
- ✅ `test` - Keep current behavior (appropriate)

**Worklog Commands**:
- ✅ `list` - Keep current behavior (already excellent)
- ✅ Other commands - Keep current behavior (appropriate for mutations)

#### Phase 3: Remove Deprecated Flags

- Remove `--table` flag (default will be table for lists)
- Remove `--detail` flag (default will be panel for single items)
- Keep `--json` flag for all commands

#### Phase 4: Update Documentation

- Update help text for all commands
- Update README.md with new output examples
- Update CLAUDE.md with new patterns

## Implementation Checklist

### New Formatters to Create

- [ ] `format_project_detail()` - Rich panel for single project
- [ ] `format_versions_table()` - Rich table for project versions
- [ ] `format_components_table()` - Rich table for project components

### Commands to Update

**Issues** (`commands/issues.py`):
- [ ] `search` - Change default to table
- [ ] `get` - Change default to panel
- [ ] `epic-stories` - Change default to table
- [ ] `subtasks` - Change default to table
- [ ] Remove `--table` and `--detail` flags from these commands

**Projects** (`commands/projects.py`):
- [ ] `list` - Change default to table
- [ ] `get` - Change default to panel (use new formatter)
- [ ] `issue-types` - Change default to table
- [ ] `versions` - Change default to table (use new formatter)
- [ ] `components` - Change default to table (use new formatter)
- [ ] Remove `--table` flag from these commands

### Testing Strategy

For each updated command, verify:
1. Default output is well-formatted and readable
2. `--json` flag still works correctly
3. No breaking changes to JSON structure
4. Visual formatting looks good in terminal
5. Information is complete and accurate

### Example Before/After

#### Before: `jira-cli projects get PROJ`
```json
{
  "id": "10000",
  "key": "PROJ",
  "name": "My Project",
  "projectTypeKey": "software",
  "lead": {
    "displayName": "John Doe",
    "accountId": "5f8a9b1c2d3e4f5g6h7i8j9k"
  },
  "description": "This is my project"
}
```

#### After: `jira-cli projects get PROJ`
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Project: PROJ                              ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Name: My Project                           │
│ Type: software                             │
│ Lead: John Doe                             │
│ Description: This is my project            │
└────────────────────────────────────────────┘
```

#### After with JSON: `jira-cli projects get PROJ --json`
```json
{
  "id": "10000",
  "key": "PROJ",
  "name": "My Project",
  "projectTypeKey": "software",
  "lead": {
    "displayName": "John Doe",
    "accountId": "5f8a9b1c2d3e4f5g6h7i8j9k"
  },
  "description": "This is my project"
}
```

## Benefits

1. **Improved UX**: Users get readable output by default without needing to know special flags
2. **Reduced confusion**: Single `--json` flag is easier to understand than multiple format flags
3. **Better discoverability**: New users immediately see well-formatted output
4. **Maintained flexibility**: Scripting use cases still supported via `--json`
5. **Consistent patterns**: Similar commands behave similarly across the CLI
6. **Professional appearance**: Rich formatting makes the CLI look polished and modern

## Migration Path

This change is **mostly backward compatible**:

- **Breaking**: `--table` and `--detail` flags will be removed
- **Non-breaking**: `--json` flag behavior unchanged
- **Non-breaking**: JSON structure unchanged
- **Improved default**: Users who didn't use flags get better output

### Communication Plan

1. Add deprecation warnings for `--table` and `--detail` in version N
2. Remove deprecated flags in version N+1
3. Update documentation and examples
4. Add migration notes to CHANGELOG.md

## Success Metrics

After implementation, the CLI should have:

- ✅ 100% of fetch/get commands have well-formatted default output
- ✅ 0 commands default to raw JSON output (except when `--json` used)
- ✅ Consistent flag usage across all commands
- ✅ Improved user satisfaction (subjective, based on feedback)
- ✅ No degradation in scripting capabilities

## Future Enhancements

Potential improvements beyond this plan:

1. **Color themes**: Allow users to customize color schemes
2. **Output templates**: Let users define custom output formats
3. **Pagination**: Add pagination for large result sets
4. **Export formats**: Support CSV, Markdown table output
5. **Interactive mode**: TUI for browsing issues and projects
