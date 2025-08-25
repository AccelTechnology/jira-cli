"""Main CLI entry point for Jira CLI."""

import typer
from typing import Optional
from rich.console import Console
from rich import print as rprint

from .commands import issues, projects, auth
from .utils.formatting import print_success, print_error, print_info

console = Console()

# Create main app
app = typer.Typer(
    name="jira-cli",
    help="Command Line Interface for Jira REST API operations",
    add_completion=False,
    rich_markup_mode="rich"
)

# Add subcommands
app.add_typer(issues.app, name="issues", help="Manage Jira issues")
app.add_typer(projects.app, name="projects", help="Manage Jira projects")
app.add_typer(auth.app, name="auth", help="Authentication and user info")


@app.command("version")
def version():
    """Show version information."""
    from . import __version__
    console.print(f"Jira CLI version: {__version__}")


@app.command("config")
def show_config():
    """Show current configuration."""
    import os
    
    config_info = {
        "JIRA_URL": os.getenv('JIRA_URL', 'https://acceldevs.atlassian.net'),
        "JIRA_EMAIL": os.getenv('JIRA_EMAIL', 'Not set'),
        "JIRA_API_TOKEN": "Set" if os.getenv('JIRA_API_TOKEN') else "Not set"
    }
    
    console.print("[bold]Current Configuration:[/bold]")
    for key, value in config_info.items():
        if key == "JIRA_API_TOKEN":
            console.print(f"  {key}: {value}")
        else:
            console.print(f"  {key}: {value}")


@app.command("search")
def quick_search(
    query: str = typer.Argument(..., help="JQL query string"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    table: bool = typer.Option(False, "--table", help="Output as table")
):
    """Quick issue search (shortcut for 'issues search')."""
    from .commands.issues import search_issues
    search_issues(query, None, 50, 0, json_output, table)


@app.command("epics")
def list_epics(
    project: str = typer.Option("ACCELERP", "--project", "-p", help="Project key"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    table: bool = typer.Option(False, "--table", help="Output as table")
):
    """List epics in a project."""
    from .commands.issues import search_issues
    jql = f"project = {project} AND issuetype = Epic"
    search_issues(jql, None, 50, 0, json_output, table)


@app.command("my-issues")
def my_issues(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Filter by project key"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    table: bool = typer.Option(False, "--table", help="Output as table")
):
    """List issues assigned to current user."""
    from .commands.issues import search_issues
    
    jql_parts = ["assignee = currentUser()"]
    
    if project:
        jql_parts.append(f"project = {project}")
    
    if status:
        if status.lower() == "open":
            jql_parts.append("status != Done")
        else:
            jql_parts.append(f"status = \"{status}\"")
    
    jql = " AND ".join(jql_parts)
    search_issues(jql, None, 50, 0, json_output, table)


@app.command("subtasks")
def list_subtasks_quick(
    parent_key: str = typer.Argument(..., help="Parent issue key (e.g., PROJ-123)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    table: bool = typer.Option(False, "--table", help="Output as table")
):
    """Quick command to list subtasks of a parent issue."""
    from .commands.issues import list_subtasks
    list_subtasks(parent_key, json_output, table)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()