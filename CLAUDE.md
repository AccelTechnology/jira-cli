# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation and Setup
```bash
# Development setup with dependencies
./install-dev.sh

# Regular installation
./install.sh

# Install in development mode manually
pip install -e .

# Install development dependencies
pip install black isort flake8 pytest pytest-cov mypy
```

### Code Quality and Testing
```bash
# Format code
black src/

# Sort imports
isort src/

# Lint code
flake8 src/

# Run tests
pytest

# Run tests with coverage
pytest --cov=jira_cli --cov-report=term-missing

# Type checking
mypy src/
```

### Running the CLI
```bash
# Both commands are available after installation
jira-cli --help
jira --help

# Test configuration
jira-cli auth test
jira-cli config --setup-help
```

## Architecture Overview

### Project Structure
```
src/jira_cli/
├── commands/              # Command modules organized by domain
│   ├── issues.py         # Issue operations (create, update, search, etc.)
│   ├── projects.py       # Project management commands
│   ├── auth.py          # Authentication and user commands
│   ├── worklog.py       # Time tracking and worklog management
│   └── attachments.py   # File attachment operations
├── utils/               # Shared utilities and helpers
│   ├── api.py          # Jira REST API client
│   ├── auth.py         # Authentication helpers
│   ├── formatting.py   # Output formatting (tables and rich panels)
│   ├── validation.py   # Input validation decorators
│   ├── error_handling.py # Enhanced error messaging system
│   └── markdown_to_adf.py # Markdown to Atlassian Document Format
├── main.py             # CLI entry point and command registration
├── models.py           # Pydantic data models
└── exceptions.py       # Custom exception classes
```

### Key Architectural Patterns

#### Command Structure
- Uses Typer for CLI framework with rich output support
- Commands are organized into domain-specific modules (issues, projects, etc.)
- Each command module has its own Typer app that gets added to main app
- All commands use rich formatted output (tables and detail panels)

#### Error Handling System
- Comprehensive validation system using decorators (`@validate_command`)
- Centralized error formatting with helpful examples and suggestions
- Input validation for issue keys, project keys, dates, JQL queries, etc.
- API error handling with context-aware messaging

#### API Client Architecture
- Centralized API client in `utils/api.py`
- Handles authentication, request formatting, and response parsing
- Supports both Jira Cloud and Server/DC
- Built-in retry logic and rate limiting handling

#### Output Formatting
- Rich formatted output using tables and detail panels
- Markdown support with conversion to Atlassian Document Format (ADF)
- Smart @mention parsing in comments with user lookup
- Consistent formatting across all commands

#### Validation and Error Handling
- Decorator-based validation system for input parameters
- Validates issue keys (PROJECT-123 format), project keys, dates, JQL, etc.
- Enhanced error messages with examples, suggestions, and command context
- Configuration validation with setup help

### Key Features

#### Issue Management
- Full CRUD operations for Jira issues
- Epic and story management with linking
- Subtask creation, linking, and management
- Comment system with @mention support and markdown parsing
- Timeline management with due dates

#### Smart Comment System
- Automatic @mention detection and conversion to Jira mention nodes
- Supports email-based mentions (@user@company.com)
- Account ID mentions (@accountid:123...)
- Username mentions (@username)
- Markdown support in comments and descriptions

#### Output Formatting
- All commands output rich formatted data using the Rich library
- Table views for list operations (issues, projects, worklogs, etc.)
- Detail panels for single item views (individual issues, projects, users)
- Consistent styling across all commands with color-coded fields

### Environment Configuration
Required environment variables:
```bash
JIRA_EMAIL="your.email@example.com"
JIRA_API_TOKEN="your_api_token"
JIRA_URL="https://your-domain.atlassian.net"  # Optional
```

### Version System
- Uses timestamp-based versioning: YYYY.M.D.HHMM
- Development versions: dev.YYYY.M.D.HHMM
- Version info shows installation timestamp and system details

### Testing Approach
- Pytest for test framework
- Coverage reporting enabled
- Error handling tests in test_error_handling.py
- Markdown conversion tests in test_markdown.py

## Development Notes

### Adding New Commands
1. Create command function in appropriate module (e.g., `commands/issues.py`)
2. Add validation decorators (`@validate_command`)
3. Use consistent error handling patterns
4. Use rich formatted output (tables for lists, panels for details)
5. Add comprehensive help text

### Error Handling Patterns
- Use `@validate_command` decorator for input validation
- Use `ErrorFormatter.print_formatted_error()` for custom errors
- Provide clear examples and suggestions in error messages
- Include command context for help navigation

### API Integration
- Use the centralized API client from `utils/api.py`
- Handle authentication through `utils/auth.py`
- Follow existing patterns for request/response handling
- Use `handle_api_error()` for consistent API error handling

### Code Style
- Black for code formatting (line length 88)
- isort for import sorting (black profile)
- Type hints required (mypy enforcement)
- Rich library for enhanced terminal output