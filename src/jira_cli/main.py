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
    from . import __version__, __author__, __email__
    import os
    import sys
    from datetime import datetime
    
    console.print(f"[bold blue]Jira CLI[/bold blue] version: [green]{__version__}[/green]")
    console.print(f"Author: {__author__} ({__email__})")
    
    # Parse version to show install time if it's not a dev version
    if not __version__.startswith('dev.'):
        try:
            # Parse YYYY.M.D.HHMM format
            parts = __version__.split('.')
            if len(parts) == 4:
                year, month, day, time_part = parts
                hour, minute = int(time_part[:2]), int(time_part[2:])
                
                install_time = datetime(int(year), int(month), int(day), hour, minute)
                console.print(f"Installed: {install_time.strftime('%Y-%m-%d at %H:%M')}")
        except Exception:
            pass
    else:
        console.print("[yellow]Development version[/yellow]")
    
    console.print(f"Python: {sys.version.split()[0]}")
    console.print(f"Platform: {sys.platform}")


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
def epics_main(
    project: str = typer.Option("ACCELERP", "--project", "-p", help="Project key"),
    action: Optional[str] = typer.Option(None, "--action", "-a", help="Action: create, edit, delete"),
    epic_key: Optional[str] = typer.Option(None, "--epic", help="Epic key for edit/delete actions"),
    summary: Optional[str] = typer.Option(None, "--summary", "-s", help="Epic summary (for create/edit)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    table: bool = typer.Option(False, "--table", help="Output as table")
):
    """List, create, edit, or delete epics in a project."""
    from .commands.issues import search_issues, create_epic_interactive, edit_epic_interactive, delete_epic_interactive
    
    if action == "create":
        create_epic_interactive(project, summary, json_output)
    elif action == "edit" and epic_key:
        edit_epic_interactive(epic_key, summary, json_output)
    elif action == "delete" and epic_key:
        delete_epic_interactive(epic_key, json_output)
    elif action and not epic_key and action in ["edit", "delete"]:
        print_error(f"Action '{action}' requires --epic parameter")
        raise typer.Exit(1)
    elif action and action not in ["create", "edit", "delete"]:
        print_error(f"Invalid action '{action}'. Valid actions: create, edit, delete")
        raise typer.Exit(1)
    else:
        # List epics (default behavior)
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
    action: Optional[str] = typer.Option(None, "--action", "-a", help="Action: edit, delete"),
    subtask_key: Optional[str] = typer.Option(None, "--subtask", help="Subtask key for edit/delete actions"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    table: bool = typer.Option(False, "--table", help="Output as table")
):
    """Quick command to list, edit, or delete subtasks of a parent issue."""
    from .commands.issues import list_subtasks, edit_subtask_interactive, delete_subtask_interactive
    
    if action == "edit" and subtask_key:
        edit_subtask_interactive(subtask_key, json_output)
    elif action == "delete" and subtask_key:
        delete_subtask_interactive(subtask_key, json_output)
    elif action and not subtask_key:
        print_error(f"Action '{action}' requires --subtask parameter")
        raise typer.Exit(1)
    elif action and action not in ["edit", "delete"]:
        print_error(f"Invalid action '{action}'. Valid actions: edit, delete")
        raise typer.Exit(1)
    else:
        list_subtasks(parent_key, json_output, table)


@app.command("tree")
def show_tree(
    issue_key: str = typer.Argument(..., help="Epic or Story key to show hierarchy tree"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    expand_all: bool = typer.Option(False, "--expand", help="Expand all levels (show subtasks)")
):
    """Show hierarchical tree view of Epic -> Stories -> Subtasks."""
    from .commands.issues import show_issue_tree
    show_issue_tree(issue_key, json_output, expand_all)


@app.command("hierarchy")
def show_hierarchy(
    issue_key: str = typer.Argument(..., help="Issue key to show in hierarchy context"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Show issue in its hierarchy context (parent and children)."""
    from .commands.issues import show_issue_hierarchy
    show_issue_hierarchy(issue_key, json_output)


@app.command("stories")
def stories_main(
    epic_key: str = typer.Argument(..., help="Epic key to list stories for"),
    action: Optional[str] = typer.Option(None, "--action", "-a", help="Action: create"),
    summary: Optional[str] = typer.Option(None, "--summary", "-s", help="Story summary (for create)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    table: bool = typer.Option(False, "--table", help="Output as table")
):
    """List or create stories under an epic."""
    from .commands.issues import search_issues, create_story_interactive
    
    if action == "create":
        create_story_interactive(epic_key, summary, json_output)
    elif action and action != "create":
        print_error(f"Invalid action '{action}'. Valid actions: create")
        raise typer.Exit(1)
    else:
        # List stories under epic (default behavior)
        jql = f"parent = {epic_key}"
        search_issues(jql, None, 50, 0, json_output, table)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()