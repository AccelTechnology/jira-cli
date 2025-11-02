"""Authentication-related commands for Jira CLI."""

import typer
from rich.console import Console

from ..utils.api import JiraApiClient
from ..utils.formatting import (
    print_error,
    print_success,
    print_info,
    format_user_info,
)
from ..exceptions import JiraCliError

console = Console()
app = typer.Typer(help="Authentication and user info")


@app.command("whoami")
def whoami():
    """Show current user information."""
    try:
        client = JiraApiClient()
        user = client.get_current_user()

        user_panel = format_user_info(user)
        console.print(user_panel)

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("test")
def test_connection():
    """Test Jira API connection and authentication."""
    try:
        client = JiraApiClient()
        user = client.get_current_user()

        display_name = user.get("displayName", "Unknown")
        email = user.get("emailAddress", "Unknown")
        print_success(
            f"Connection successful! Authenticated as {display_name} ({email})"
        )

    except JiraCliError as e:
        print_error(f"Connection failed: {str(e)}")
        raise typer.Exit(1)
