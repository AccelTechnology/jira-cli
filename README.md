# Jira CLI

A command-line interface for Jira REST API operations, built with Python and Typer.

## Features

- **Issue Management**: Search, create, update, assign, and transition issues
- **Epic Management**: Create stories under epics, link existing stories to epics, list epic stories
- **Timeline Management**: Set due dates, track project timelines, timeline-based filtering
- **Project Operations**: List projects, versions, components, and issue types
- **Authentication**: Secure API token authentication
- **Enhanced Tables**: Display issue types, due dates, and improved formatting
- **Flexible Output**: JSON, table, and detailed views
- **Quick Commands**: Shortcuts for common operations like listing epics and your issues

## Installation

### Prerequisites

- Python 3.8 or higher
- Jira Cloud or Server with REST API access
- Jira API token (for Jira Cloud) or Personal Access Token (for Jira Server/DC)

### Install from Source

```bash
git clone <repository>
cd jira-cli
./install.sh
```

Or install manually:

```bash
pip install -e .
```

## Configuration

Set the required environment variables:

```bash
# Required
export JIRA_EMAIL="your.email@example.com"
export JIRA_API_TOKEN="your_api_token"

# Optional (defaults to acceldevs.atlassian.net)
export JIRA_URL="https://your-domain.atlassian.net"
```

### Getting an API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Copy the generated token and set it as `JIRA_API_TOKEN`

## Usage

### Basic Commands

```bash
# Show help
jira-cli --help

# Test connection
jira-cli auth test

# Show current user
jira-cli auth whoami

# Show configuration
jira-cli config
```

### Issue Operations

```bash
# Search issues
jira-cli search "project = <project_id> AND assignee = currentUser()" --table

# Get issue details
jira-cli issues get <project_id>-123 --detail

# Create issue
jira-cli issues create --project <project_id> --summary "New task" --type Task

# Update issue
jira-cli issues update <project_id>-123 --summary "Updated summary"

# Assign issue
jira-cli issues assign <project_id>-123 user_account_id

# Add comment
jira-cli issues comment <project_id>-123 "This is a comment"

# For more options and examples:
jira-cli issues --help
```

### Epic Management

```bash
# Create epic
jira-cli issues create --project <project_id> --summary "New Epic" --type Epic

# List stories under an epic
jira-cli issues epic-stories <project_id>-1 --table

# List all epics in project
jira-cli epics --project <project_id> --table

# For more epic operations:
jira-cli epics --help
jira-cli issues --help
```

### Timeline Management

```bash
# Create issue with due date
jira-cli issues create --project <project_id> --summary "Task with deadline" --type Task --due-date "2025-09-15"

# View project timeline
jira-cli search "project = <project_id> ORDER BY duedate ASC" --table

# Find overdue issues
jira-cli search "project = <project_id> AND duedate < now()" --table

# For more timeline operations:
jira-cli issues --help
jira-cli search --help
```

### Quick Commands

```bash
# List your issues
jira-cli my-issues --project <project_id>

# List epics
jira-cli epics --project <project_id>

# For more options:
jira-cli my-issues --help
jira-cli epics --help
```

### Project Operations

```bash
# List projects
jira-cli projects list --table

# Get project details
jira-cli projects get <project_id>

# List issue types
jira-cli projects issue-types --table

# For more project operations:
jira-cli projects --help
```

## Output Formats

The CLI supports multiple output formats:

- **JSON** (default): Raw JSON response from Jira API
- **Table**: Formatted table view (use `--table` flag)
- **Detail**: Rich formatted view for single items (use `--detail` flag)

## Common JQL Examples

```bash
# Issues assigned to you
jira-cli search "assignee = currentUser()" --table

# Open issues in a project
jira-cli search "project = <project_id> AND status != Done" --table

# All epics in project
jira-cli search "project = <project_id> AND issuetype = Epic" --table

# For more JQL examples and syntax:
jira-cli search --help
```

## Error Handling

The CLI provides clear error messages for common issues:

- Authentication failures
- Missing environment variables
- Invalid JQL queries
- Network connectivity issues
- Permission errors

## Development

### Project Structure

```
jira-cli/
├── src/jira_cli/
│   ├── commands/          # Command modules
│   │   ├── issues.py      # Issue operations
│   │   ├── projects.py    # Project operations
│   │   └── auth.py        # Authentication
│   ├── utils/             # Utilities
│   │   ├── api.py         # API client
│   │   ├── auth.py        # Authentication helpers
│   │   └── formatting.py  # Output formatting
│   ├── models.py          # Data models
│   ├── exceptions.py      # Custom exceptions
│   └── main.py           # Main CLI entry point
├── tests/                 # Test files
├── pyproject.toml        # Project configuration
└── README.md
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
isort src/
```

## License

MIT License