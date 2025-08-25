# Jira CLI

A comprehensive command-line interface for Jira REST API operations, built with Python and Typer. This tool provides complete issue management, project operations, epic handling, and timeline tracking capabilities.

## Features

- **🔍 Issue Management**: Search, create, read, update, delete, assign, and transition issues
- **📋 Epic Management**: Create epics, link stories to epics, list epic contents
- **📅 Timeline Management**: Set due dates, track project timelines, timeline-based filtering
- **🏗️ Project Operations**: List projects, get project details, manage versions, components, and issue types
- **🔐 Authentication**: Secure API token authentication with connection testing
- **📊 Rich Output**: Enhanced tables, detailed views, JSON output, and beautiful formatting
- **⚡ Quick Commands**: Shortcuts for common operations (my-issues, epics, search)
- **🎨 Multiple Output Formats**: JSON, table, and detailed panel views

## Installation

### Prerequisites

- **Python 3.8 or higher** - Download from [python.org](https://www.python.org/downloads/)
- **Jira Cloud or Server** with REST API access
- **Jira API token** (for Jira Cloud) or Personal Access Token (for Jira Server/DC)

### Quick Install

Choose the installation method that works best for your operating system:

#### 🪟 Windows

```cmd
git clone https://github.com/AccelTechnology/jira-cli.git
cd jira-cli
install.bat
```

#### 🐧 Linux / 🍎 macOS

```bash
git clone https://github.com/AccelTechnology/jira-cli.git
cd jira-cli
chmod +x install.sh
./install.sh
```

### Manual Installation Options

#### Option 1: Using pip directly

```bash
git clone https://github.com/AccelTechnology/jira-cli.git
cd jira-cli
pip install -e .
```

#### Option 2: With virtual environment (recommended)

```bash
git clone https://github.com/AccelTechnology/jira-cli.git
cd jira-cli
python -m venv jira-cli-venv

# Activate virtual environment
# On Windows:
jira-cli-venv\Scripts\activate
# On Linux/macOS:
source jira-cli-venv/bin/activate

pip install -e .
```

#### Option 3: Using requirements.txt

```bash
git clone https://github.com/AccelTechnology/jira-cli.git
cd jira-cli
pip install -r requirements.txt
pip install -e .
```

### Platform-Specific Installation

#### Ubuntu/Debian
```bash
# Install Python and required packages
sudo apt update
sudo apt install python3 python3-pip python3-venv git

# Clone and install
git clone https://github.com/AccelTechnology/jira-cli.git
cd jira-cli
./install.sh
```

#### CentOS/RHEL/Fedora
```bash
# Install Python and required packages
sudo yum install python3 python3-pip git  # CentOS/RHEL
# OR
sudo dnf install python3 python3-pip git  # Fedora

# Clone and install
git clone https://github.com/AccelTechnology/jira-cli.git
cd jira-cli
./install.sh
```

#### macOS with Homebrew
```bash
# Install Python via Homebrew
brew install python3

# Clone and install
git clone https://github.com/AccelTechnology/jira-cli.git
cd jira-cli
./install.sh
```

#### Windows with Package Manager
```powershell
# Using Chocolatey
choco install python3 git

# Using Scoop
scoop install python git

# Then run the installation
git clone https://github.com/AccelTechnology/jira-cli.git
cd jira-cli
.\install.bat
```

### Development Installation

For contributors and developers:

```bash
git clone https://github.com/AccelTechnology/jira-cli.git
cd jira-cli
chmod +x install-dev.sh
./install-dev.sh
```

This installs additional development tools: `black`, `isort`, `flake8`, `pytest`, `mypy`

### Verify Installation

After installation, verify it works:

```bash
jira-cli --help
jira-cli version
```

### Installation Troubleshooting

#### Common Issues

**Python not found:**
- Windows: Make sure to check "Add Python to PATH" during Python installation
- Linux: Install Python 3 using your package manager
- macOS: Use Homebrew or download from python.org

**Permission denied on install.sh:**
```bash
chmod +x install.sh
./install.sh
```

**pip not found:**
- Install pip: `python -m ensurepip --upgrade`
- Or reinstall Python with pip included

**Virtual environment issues:**
- Make sure `python -m venv` works
- Try using `virtualenv` instead: `pip install virtualenv && virtualenv jira-cli-venv`

**Installation fails with dependencies:**
- Update pip: `pip install --upgrade pip`
- Install dependencies manually: `pip install -r requirements.txt`

#### System-specific Notes

- **Windows**: Use Command Prompt or PowerShell, not Git Bash for .bat files
- **WSL (Windows Subsystem for Linux)**: Use the Linux installation method
- **macOS**: If you have multiple Python versions, specify the version: `python3.11 -m pip install -e .`
- **Docker**: You can run jira-cli in a container - see Development section

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

# Show version
jira-cli version

# Show current configuration
jira-cli config

# Test connection
jira-cli auth test

# Show current user
jira-cli auth whoami
```

### Issue Management

#### Search & Retrieve Issues

```bash
# Quick search (shortcut command)
jira-cli search "project = <project_id> AND assignee = currentUser()" --table

# Advanced search with options
jira-cli issues search "project = <project_id>" --table --max-results 100

# Get specific issue
jira-cli issues get <project_id>-123 --detail

# Get issue with specific fields
jira-cli issues get <project_id>-123 --field summary --field status
```

#### Create Issues

```bash
# Basic issue creation
jira-cli issues create --project <project_id> --summary "New task" --type Task

# Create issue with full details
jira-cli issues create \
  --project <project_id> \
  --summary "Feature implementation" \
  --type Story \
  --description "Detailed description here" \
  --assignee "user_account_id" \
  --priority "High" \
  --due-date "2025-12-31" \
  --label "frontend" --label "urgent"

# Create story under epic
jira-cli issues create \
  --project <project_id> \
  --summary "User authentication" \
  --type Story \
  --epic <project_id>-1
```

#### Update Issues

```bash
# Update summary
jira-cli issues update <project_id>-123 --summary "Updated summary"

# Update multiple fields
jira-cli issues update <project_id>-123 \
  --summary "New summary" \
  --description "Updated description" \
  --due-date "2025-12-31" \
  --priority "High"

# Link story to epic
jira-cli issues update <project_id>-123 --epic <project_id>-1
```

#### Issue Operations

```bash
# Assign issue
jira-cli issues assign <project_id>-123 user_account_id

# Unassign issue
jira-cli issues assign <project_id>-123 none

# Get available transitions
jira-cli issues transitions <project_id>-123 --table

# Transition issue
jira-cli issues transition <project_id>-123 transition_id

# Add comment
jira-cli issues comment <project_id>-123 "This is a comment"

# Delete issue (with confirmation)
jira-cli issues delete <project_id>-123

# Force delete (skip confirmation)
jira-cli issues delete <project_id>-123 --force
```

### Epic Management

```bash
# Create epic
jira-cli issues create --project <project_id> --summary "New Epic" --type Epic

# List all epics in project
jira-cli epics --project <project_id> --table

# List stories under an epic
jira-cli issues epic-stories <project_id>-1 --table

# Create story under epic
jira-cli issues create \
  --project <project_id> \
  --summary "Story under epic" \
  --type Story \
  --epic <project_id>-1
```

### Timeline Management

```bash
# Create issue with due date
jira-cli issues create \
  --project <project_id> \
  --summary "Task with deadline" \
  --type Task \
  --due-date "2025-09-15"

# View project timeline (sorted by due date)
jira-cli search "project = <project_id> ORDER BY duedate ASC" --table

# Find overdue issues
jira-cli search "project = <project_id> AND duedate < now()" --table

# Find issues due this week
jira-cli search "project = <project_id> AND duedate >= startOfWeek() AND duedate <= endOfWeek()" --table

# Update issue due date
jira-cli issues update <project_id>-123 --due-date "2025-10-01"
```

### Quick Commands

```bash
# List your assigned issues
jira-cli my-issues --project <project_id> --table

# List your issues with status filter
jira-cli my-issues --project <project_id> --status "In Progress" --table

# List your open issues
jira-cli my-issues --project <project_id> --status "open" --table

# List all epics
jira-cli epics --project <project_id> --table

# Quick search
jira-cli search "assignee = currentUser()" --table
```

### Project Operations

```bash
# List all projects
jira-cli projects list --table

# Get project details
jira-cli projects get <project_id> --json

# List all issue types
jira-cli projects issue-types --table

# List project versions
jira-cli projects versions <project_id>

# List project components
jira-cli projects components <project_id>
```

### Authentication & User Info

```bash
# Test API connection
jira-cli auth test

# Show current user info
jira-cli auth whoami

# Get detailed user info
jira-cli auth whoami --json
```

## Output Formats

The CLI supports three output formats:

- **JSON** (default): Raw JSON response from Jira API (`--json`)
- **Table**: Formatted table view (`--table`)
- **Detail**: Rich formatted panel view for single items (`--detail`)

## Advanced JQL Queries

```bash
# Issues assigned to you
jira-cli search "assignee = currentUser()" --table

# Open issues in a project
jira-cli search "project = <project_id> AND status != Done" --table

# High priority bugs
jira-cli search "project = <project_id> AND priority = High AND issuetype = Bug" --table

# Recent updates (last week)
jira-cli search "project = <project_id> AND updated >= -1w" --table

# All epics in project
jira-cli search "project = <project_id> AND issuetype = Epic" --table

# Stories under specific epic
jira-cli search "project = <project_id> AND parent = <project_id>-1" --table

# Stories without epic assignment
jira-cli search "project = <project_id> AND issuetype = Story AND parent is EMPTY" --table

# Issues by type with enhanced table view
jira-cli search "project = <project_id> AND issuetype in (Epic, Story, Task)" --table

# Complex timeline queries
jira-cli search "project = <project_id> AND duedate <= '2025-12-31' ORDER BY priority DESC, duedate ASC" --table
```

## Field Support

### Issue Creation Fields
- `project` - Project key (required)
- `summary` - Issue title (required)
- `type` - Issue type (Task, Story, Bug, Epic, etc.)
- `description` - Issue description (converted to ADF format)
- `assignee` - Assignee account ID
- `priority` - Priority name (High, Medium, Low, etc.)
- `labels` - Multiple labels can be added
- `epic` - Epic key for linking stories
- `due-date` - Due date in YYYY-MM-DD format

### Issue Update Fields
All creation fields except `project` can be updated, plus:
- Epic linking/unlinking
- Due date modification
- Label management

## Table Display Columns

Issues tables show:
- **Key**: Issue key (e.g., PROJ-123)
- **Summary**: Issue title (truncated if long)
- **Type**: Issue type (Epic, Story, Task, Bug, etc.)
- **Status**: Current status
- **Due Date**: Due date if set
- **Assignee**: Assigned user or "Unassigned"
- **Priority**: Issue priority

## Error Handling

The CLI provides clear error messages for:
- Authentication failures
- Missing environment variables
- Invalid JQL queries
- Network connectivity issues
- Permission errors
- Invalid issue keys or project keys
- API rate limiting

## Examples by Use Case

### Daily Workflow
```bash
# Check your assigned work
jira-cli my-issues --table

# Create a new task
jira-cli issues create --project <project_id> --summary "Daily standup notes" --type Task

# Update issue status
jira-cli issues transitions <project_id>-123
jira-cli issues transition <project_id>-123 21

# Add progress comment
jira-cli issues comment <project_id>-123 "Work in progress, 50% complete"
```

### Epic Management
```bash
# Create new epic
jira-cli issues create --project <project_id> --summary "User Management" --type Epic

# Create stories under epic
jira-cli issues create --project <project_id> --summary "User Login" --type Story --epic <project_id>-1
jira-cli issues create --project <project_id> --summary "User Registration" --type Story --epic <project_id>-1

# Review epic progress
jira-cli issues epic-stories <project_id>-1 --table
```

### Project Planning
```bash
# List all epics for planning
jira-cli epics --project <project_id> --table

# Review project timeline
jira-cli search "project = <project_id> ORDER BY duedate ASC" --table

# Find work without deadlines
jira-cli search "project = <project_id> AND duedate is EMPTY" --table
```

## Getting Help

```bash
# Main help
jira-cli --help

# Command-specific help
jira-cli issues --help
jira-cli issues create --help
jira-cli projects --help
jira-cli auth --help
jira-cli search --help
```

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