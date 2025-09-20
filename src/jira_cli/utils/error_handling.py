"""Enhanced error handling utilities for Jira CLI."""

import re
from typing import Any, Dict, List, Optional, Tuple, Union
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..exceptions import JiraCliError, ValidationError

console = Console()


class ErrorFormatter:
    """Formats error messages with helpful examples and suggestions."""

    @staticmethod
    def format_error_message(
        error_type: str,
        description: str,
        received: Optional[str] = None,
        expected: Optional[str] = None,
        examples: Optional[List[str]] = None,
        suggestions: Optional[List[str]] = None,
        command_context: Optional[str] = None,
    ) -> str:
        """Format a comprehensive error message.

        Args:
            error_type: Type of error (e.g., "Invalid Parameter", "Missing Required Field")
            description: Clear description of what went wrong
            received: What the user actually provided
            expected: What was expected instead
            examples: List of valid example usage
            suggestions: List of helpful suggestions
            command_context: The command context for help reference

        Returns:
            Formatted error message string
        """
        parts = [f"[bold red]Error: {error_type}[/bold red]", f"{description}"]

        if received:
            parts.append(f"\n[dim]Received:[/dim] {received}")

        if expected:
            parts.append(f"[dim]Expected:[/dim] {expected}")

        if examples:
            parts.append(f"\n[bold]Example usage:[/bold]")
            for example in examples:
                parts.append(f"  [cyan]{example}[/cyan]")

        if suggestions:
            parts.append(f"\n[bold]Suggestions:[/bold]")
            for suggestion in suggestions:
                parts.append(f"  • {suggestion}")

        if command_context:
            parts.append(
                f"\nRun '[cyan]jira-cli {command_context} --help[/cyan]' for more information."
            )

        return "\n".join(parts)

    @staticmethod
    def print_formatted_error(
        error_type: str,
        description: str,
        received: Optional[str] = None,
        expected: Optional[str] = None,
        examples: Optional[List[str]] = None,
        suggestions: Optional[List[str]] = None,
        command_context: Optional[str] = None,
    ) -> None:
        """Print a formatted error message to console."""
        message = ErrorFormatter.format_error_message(
            error_type,
            description,
            received,
            expected,
            examples,
            suggestions,
            command_context,
        )
        console.print(message)


class InputValidator:
    """Validates various types of CLI inputs with helpful error messages."""

    @staticmethod
    def validate_issue_key(issue_key: str, command_context: str = "") -> str:
        """Validate Jira issue key format.

        Args:
            issue_key: The issue key to validate
            command_context: Command context for error messages

        Returns:
            Validated issue key

        Raises:
            ValidationError: If issue key format is invalid
        """
        if not issue_key:
            ErrorFormatter.print_formatted_error(
                "Missing Required Parameter",
                "Issue key is required but not provided.",
                expected="A valid Jira issue key",
                examples=[
                    "jira-cli issues get PROJ-123",
                    "jira-cli issues get MYPROJECT-456",
                ],
                command_context=command_context,
            )
            raise ValidationError("Issue key is required")

        # Validate issue key format (PROJECT-NUMBER)
        issue_key_pattern = r"^[A-Z][A-Z0-9]*-\d+$"
        if not re.match(issue_key_pattern, issue_key.upper()):
            ErrorFormatter.print_formatted_error(
                "Invalid Issue Key Format",
                "Issue key must follow the format PROJECT-NUMBER.",
                received=f"'{issue_key}'",
                expected="Format: PROJECT-NUMBER (e.g., PROJ-123)",
                examples=["PROJ-123", "MYPROJECT-456", "DEV-789"],
                suggestions=[
                    "Ensure project key contains only uppercase letters and numbers",
                    "Use a hyphen to separate project key from issue number",
                    "Issue number should contain only digits",
                ],
                command_context=command_context,
            )
            raise ValidationError(f"Invalid issue key format: {issue_key}")

        return issue_key.upper()

    @staticmethod
    def validate_project_key(project_key: str, command_context: str = "") -> str:
        """Validate Jira project key format.

        Args:
            project_key: The project key to validate
            command_context: Command context for error messages

        Returns:
            Validated project key

        Raises:
            ValidationError: If project key format is invalid
        """
        if not project_key:
            ErrorFormatter.print_formatted_error(
                "Missing Required Parameter",
                "Project key is required but not provided.",
                expected="A valid Jira project key",
                examples=[
                    "jira-cli issues create --project PROJ --summary 'Task summary'",
                    "jira-cli projects get MYPROJECT",
                ],
                command_context=command_context,
            )
            raise ValidationError("Project key is required")

        # Validate project key format (uppercase letters and numbers only)
        project_key_pattern = r"^[A-Z][A-Z0-9]*$"
        if not re.match(project_key_pattern, project_key.upper()):
            ErrorFormatter.print_formatted_error(
                "Invalid Project Key Format",
                "Project key must contain only uppercase letters and numbers, starting with a letter.",
                received=f"'{project_key}'",
                expected="Uppercase letters and numbers only (e.g., PROJ, MYPROJECT, DEV123)",
                examples=["PROJ", "MYPROJECT", "DEV123", "ACCELERP"],
                suggestions=[
                    "Use only uppercase letters and numbers",
                    "Start with a letter, not a number",
                    "Remove spaces, hyphens, and special characters",
                ],
                command_context=command_context,
            )
            raise ValidationError(f"Invalid project key format: {project_key}")

        return project_key.upper()

    @staticmethod
    def validate_email(email: str, command_context: str = "") -> str:
        """Validate email address format.

        Args:
            email: The email to validate
            command_context: Command context for error messages

        Returns:
            Validated email

        Raises:
            ValidationError: If email format is invalid
        """
        if not email:
            ErrorFormatter.print_formatted_error(
                "Missing Required Parameter",
                "Email address is required but not provided.",
                expected="A valid email address",
                examples=["user@company.com", "developer@example.org"],
                command_context=command_context,
            )
            raise ValidationError("Email is required")

        # Basic email validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            ErrorFormatter.print_formatted_error(
                "Invalid Email Format",
                "Email address format is not valid.",
                received=f"'{email}'",
                expected="Valid email address format",
                examples=[
                    "user@company.com",
                    "developer@example.org",
                    "jane.doe@acme.co.uk",
                ],
                suggestions=[
                    "Ensure email contains @ symbol",
                    "Check domain name is properly formatted",
                    "Verify top-level domain (e.g., .com, .org)",
                ],
                command_context=command_context,
            )
            raise ValidationError(f"Invalid email format: {email}")

        return email

    @staticmethod
    def validate_date_format(date_str: str, command_context: str = "") -> str:
        """Validate date format (YYYY-MM-DD).

        Args:
            date_str: The date string to validate
            command_context: Command context for error messages

        Returns:
            Validated date string

        Raises:
            ValidationError: If date format is invalid
        """
        if not date_str:
            return date_str

        # Validate date format
        date_pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(date_pattern, date_str):
            ErrorFormatter.print_formatted_error(
                "Invalid Date Format",
                "Date must be in YYYY-MM-DD format.",
                received=f"'{date_str}'",
                expected="YYYY-MM-DD format",
                examples=["2024-12-31", "2025-01-15", "2025-08-27"],
                suggestions=[
                    "Use 4-digit year",
                    "Use 2-digit month (01-12)",
                    "Use 2-digit day (01-31)",
                    "Use hyphens to separate components",
                ],
                command_context=command_context,
            )
            raise ValidationError(f"Invalid date format: {date_str}")

        # Additional validation for date values
        try:
            from datetime import datetime

            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError as e:
            ErrorFormatter.print_formatted_error(
                "Invalid Date Value",
                f"Date value is not valid: {str(e)}",
                received=f"'{date_str}'",
                expected="Valid calendar date in YYYY-MM-DD format",
                examples=["2024-12-31", "2025-02-28", "2025-08-27"],
                suggestions=[
                    "Check month is between 01 and 12",
                    "Check day is valid for the given month",
                    "Consider leap years for February dates",
                ],
                command_context=command_context,
            )
            raise ValidationError(f"Invalid date value: {date_str}")

        return date_str

    @staticmethod
    def validate_time_format(time_str: str, command_context: str = "") -> str:
        """Validate Jira time format (e.g., 1h 30m, 2d, 4h).

        Args:
            time_str: The time string to validate
            command_context: Command context for error messages

        Returns:
            Validated time string

        Raises:
            ValidationError: If time format is invalid
        """
        if not time_str:
            ErrorFormatter.print_formatted_error(
                "Missing Required Parameter",
                "Time spent value is required but not provided.",
                expected="Valid Jira time format",
                examples=["1h", "30m", "2d", "1h 30m", "2d 4h"],
                command_context=command_context,
            )
            raise ValidationError("Time spent is required")

        # Validate Jira time format
        time_pattern = r"^(\d+[dwh]\s*)*\d*[mh]?$"
        if not re.match(time_pattern, time_str.strip()):
            ErrorFormatter.print_formatted_error(
                "Invalid Time Format",
                "Time must be in Jira time format using d (days), h (hours), m (minutes).",
                received=f"'{time_str}'",
                expected="Jira time format with d/h/m units",
                examples=["1h", "30m", "2d", "1h 30m", "2d 4h 15m", "8h"],
                suggestions=[
                    "Use 'd' for days, 'h' for hours, 'm' for minutes",
                    "Separate multiple units with spaces",
                    "Use only numbers followed by time units",
                    "Example: '1h 30m' for 1 hour and 30 minutes",
                ],
                command_context=command_context,
            )
            raise ValidationError(f"Invalid time format: {time_str}")

        return time_str.strip()

    @staticmethod
    def validate_jql_query(jql: str, command_context: str = "") -> str:
        """Validate basic JQL query format.

        Args:
            jql: The JQL query to validate
            command_context: Command context for error messages

        Returns:
            Validated JQL query

        Raises:
            ValidationError: If JQL query appears invalid
        """
        if not jql:
            ErrorFormatter.print_formatted_error(
                "Missing Required Parameter",
                "JQL query is required but not provided.",
                expected="A valid JQL (Jira Query Language) query",
                examples=[
                    'project = "PROJ"',
                    "assignee = currentUser()",
                    "status != Done AND project = MYPROJECT",
                    "created >= -7d",
                ],
                command_context=command_context,
            )
            raise ValidationError("JQL query is required")

        # Basic validation - check for obviously malformed queries
        if len(jql.strip()) < 3:
            ErrorFormatter.print_formatted_error(
                "Invalid JQL Query",
                "JQL query appears too short to be valid.",
                received=f"'{jql}'",
                expected="Complete JQL query with field, operator, and value",
                examples=[
                    'project = "PROJ"',
                    "assignee = currentUser()",
                    'status = "In Progress"',
                    "created >= -7d",
                ],
                suggestions=[
                    "Include a field name (e.g., project, assignee, status)",
                    "Use a comparison operator (=, !=, >, <, etc.)",
                    "Provide a value to compare against",
                    "Use quotes around values with spaces",
                ],
                command_context=command_context,
            )
            raise ValidationError(f"JQL query too short: {jql}")

        return jql.strip()

    @staticmethod
    def validate_required_parameter(
        value: Any,
        parameter_name: str,
        command_context: str = "",
        examples: Optional[List[str]] = None,
    ) -> Any:
        """Validate that a required parameter is provided.

        Args:
            value: The parameter value to check
            parameter_name: Name of the parameter
            command_context: Command context for error messages
            examples: Example usage strings

        Returns:
            The validated value

        Raises:
            ValidationError: If parameter is missing or empty
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            ErrorFormatter.print_formatted_error(
                "Missing Required Parameter",
                f"The parameter '{parameter_name}' is required but not provided.",
                expected=f"A valid {parameter_name} value",
                examples=examples or [f"--{parameter_name.replace('_', '-')} <value>"],
                command_context=command_context,
            )
            raise ValidationError(f"Required parameter '{parameter_name}' is missing")

        return value

    @staticmethod
    def validate_choice_parameter(
        value: str,
        valid_choices: List[str],
        parameter_name: str,
        command_context: str = "",
    ) -> str:
        """Validate that a parameter value is one of the allowed choices.

        Args:
            value: The value to validate
            valid_choices: List of valid choices
            parameter_name: Name of the parameter
            command_context: Command context for error messages

        Returns:
            The validated value

        Raises:
            ValidationError: If value is not in valid choices
        """
        if value not in valid_choices:
            # Find close matches for helpful suggestions
            suggestions = []
            value_lower = value.lower()
            for choice in valid_choices:
                if (
                    choice.lower().startswith(value_lower)
                    or value_lower in choice.lower()
                ):
                    suggestions.append(f"Did you mean '{choice}'?")

            ErrorFormatter.print_formatted_error(
                "Invalid Parameter Value",
                f"The value '{value}' is not valid for parameter '{parameter_name}'.",
                received=f"'{value}'",
                expected=f"One of: {', '.join(valid_choices)}",
                examples=[
                    f"--{parameter_name.replace('_', '-')} {choice}"
                    for choice in valid_choices[:3]
                ],
                suggestions=suggestions
                or ["Use one of the valid choices listed above"],
                command_context=command_context,
            )
            raise ValidationError(f"Invalid {parameter_name}: {value}")

        return value


def handle_api_error(error: Exception, command_context: str = "") -> None:
    """Handle and format API-related errors with helpful messages.

    Args:
        error: The exception that occurred
        command_context: Command context for error messages
    """
    if isinstance(error, ValidationError):
        # Validation errors are already formatted, just re-raise
        raise error

    error_message = str(error)

    # Common error patterns and their solutions
    if "Invalid Jira credentials" in error_message:
        ErrorFormatter.print_formatted_error(
            "Authentication Failed",
            "Your Jira credentials are invalid or expired.",
            suggestions=[
                "Check your JIRA_EMAIL environment variable",
                "Verify your JIRA_API_TOKEN is correct and not expired",
                "Ensure your JIRA_URL points to the correct instance",
                "Generate a new API token if the current one has expired",
            ],
            examples=[
                "export JIRA_EMAIL='your-email@company.com'",
                "export JIRA_API_TOKEN='your-api-token'",
                "export JIRA_URL='https://your-company.atlassian.net'",
            ],
            command_context="auth test",
        )

    elif "Resource not found" in error_message:
        ErrorFormatter.print_formatted_error(
            "Resource Not Found",
            "The requested resource could not be found.",
            suggestions=[
                "Verify the issue key or project key is correct",
                "Check that you have permission to access this resource",
                "Ensure the resource exists in your Jira instance",
            ],
            examples=[
                "jira-cli issues get PROJ-123",
                "jira-cli projects get MYPROJECT",
            ],
            command_context=command_context,
        )

    elif "Insufficient permissions" in error_message:
        ErrorFormatter.print_formatted_error(
            "Insufficient Permissions",
            "You don't have permission to perform this action.",
            suggestions=[
                "Contact your Jira administrator for required permissions",
                "Verify you're accessing the correct project",
                "Check if your account has the necessary role or permission scheme",
            ],
            command_context=command_context,
        )

    elif "Request failed" in error_message:
        ErrorFormatter.print_formatted_error(
            "Connection Error",
            "Failed to connect to Jira API.",
            suggestions=[
                "Check your internet connection",
                "Verify the JIRA_URL is correct and accessible",
                "Try again in a few moments (temporary network issue)",
            ],
            examples=["jira-cli auth test  # Test your connection"],
            command_context="auth test",
        )

    else:
        # Generic error formatting
        ErrorFormatter.print_formatted_error(
            "API Error",
            error_message,
            suggestions=[
                "Check your internet connection and Jira instance status",
                "Verify your authentication credentials",
                "Try the command again",
            ],
            command_context=command_context,
        )


def validate_configuration() -> Tuple[bool, List[str]]:
    """Validate Jira CLI configuration and return status with helpful messages.

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    import os

    issues = []

    # Check required environment variables
    # Note: JIRA_URL has a default value in auth.py, so we use the same logic
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")

    # Only validate URL format if it's explicitly set or default
    if jira_url and not jira_url.startswith(("http://", "https://")):
        issues.append("JIRA_URL should start with http:// or https://")

    if not jira_email:
        issues.append("JIRA_EMAIL environment variable is not set")
    elif "@" not in jira_email:
        issues.append("JIRA_EMAIL should be a valid email address")

    if not jira_token:
        issues.append("JIRA_API_TOKEN environment variable is not set")
    elif len(jira_token) < 10:  # API tokens are typically longer
        issues.append("JIRA_API_TOKEN appears to be too short")

    return len(issues) == 0, issues


def print_configuration_help() -> None:
    """Print helpful configuration setup instructions."""
    console.print(
        Panel.fit(
            """[bold]Jira CLI Configuration Setup[/bold]

To use Jira CLI, you need to set up these environment variables:

[bold cyan]1. JIRA_URL[/bold cyan] - Your Jira instance URL
   Example: export JIRA_URL='https://your-company.atlassian.net'

[bold cyan]2. JIRA_EMAIL[/bold cyan] - Your Jira account email
   Example: export JIRA_EMAIL='your-email@company.com'

[bold cyan]3. JIRA_API_TOKEN[/bold cyan] - Your Jira API token
   Example: export JIRA_API_TOKEN='your-api-token-here'

[bold yellow]How to get an API token:[/bold yellow]
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a label and copy the generated token

[bold green]Test your setup:[/bold green]
jira-cli auth test

[bold blue]Quick start:[/bold blue]
jira-cli config  # View current configuration
jira-cli my-issues  # List your assigned issues""",
            title="Setup Help",
            border_style="blue",
        )
    )
