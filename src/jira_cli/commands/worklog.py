"""Worklog-related commands for Jira CLI."""

import json
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from datetime import datetime

from ..utils.api import JiraApiClient
from ..utils.formatting import print_json, print_error, print_success, print_info
from ..utils.error_handling import ErrorFormatter, handle_api_error
from ..utils.validation import validate_command
from ..exceptions import JiraCliError

console = Console()
app = typer.Typer(help="Manage worklogs and time tracking")


def format_worklog_table(worklogs: list) -> Table:
    """Format worklogs data as a table."""
    table = Table(title="Worklogs")
    table.add_column("ID", style="dim")
    table.add_column("Author", style="cyan")
    table.add_column("Time Spent", style="green")
    table.add_column("Started", style="blue")
    table.add_column("Comment", style="white", max_width=50)

    for worklog in worklogs:
        author = worklog.get("author", {}).get("displayName", "Unknown")
        time_spent = worklog.get("timeSpent", "Unknown")
        started = worklog.get("started", "")

        # Parse and format the started date
        if started:
            try:
                dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                started = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass

        # Extract comment text from ADF format
        comment = ""
        if worklog.get("comment", {}).get("content"):
            for content_item in worklog["comment"]["content"]:
                if content_item.get("content"):
                    for text_item in content_item["content"]:
                        if text_item.get("text"):
                            comment += text_item["text"]

        table.add_row(
            worklog.get("id", ""),
            author,
            time_spent,
            started,
            comment[:47] + "..." if len(comment) > 50 else comment,
        )

    return table


@app.command("list")
@validate_command(issue_key_params=["issue_key"], command_context="worklog list")
def list_worklogs(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    max_results: int = typer.Option(
        50, "--max-results", "-m", help="Maximum number of results"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    table: bool = typer.Option(False, "--table", help="Output as table"),
):
    """List worklogs for an issue."""
    try:
        client = JiraApiClient()
        result = client.get_worklogs(issue_key, max_results=max_results)

        if json_output:
            print_json(result)
        elif table:
            worklogs_table = format_worklog_table(result.get("worklogs", []))
            console.print(worklogs_table)
        else:
            console.print(f"[bold blue]Worklogs for {issue_key}:[/bold blue]")

            worklogs = result.get("worklogs", [])
            if not worklogs:
                console.print("  No worklogs found")
                return

            total_seconds = 0
            for worklog in worklogs:
                author = worklog.get("author", {}).get("displayName", "Unknown")
                time_spent = worklog.get("timeSpent", "Unknown")
                started = worklog.get("started", "")
                worklog_id = worklog.get("id", "")

                # Parse and format the started date
                if started:
                    try:
                        dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                        started = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass

                # Extract comment text from ADF format
                comment = ""
                if worklog.get("comment", {}).get("content"):
                    for content_item in worklog["comment"]["content"]:
                        if content_item.get("content"):
                            for text_item in content_item["content"]:
                                if text_item.get("text"):
                                    comment += text_item["text"]

                console.print(f"\n  [dim]ID:[/dim] {worklog_id}")
                console.print(f"  [cyan]Author:[/cyan] {author}")
                console.print(f"  [green]Time Spent:[/green] {time_spent}")
                console.print(f"  [blue]Started:[/blue] {started}")
                if comment:
                    console.print(f"  [white]Comment:[/white] {comment}")

                # Calculate total time (approximate)
                if worklog.get("timeSpentSeconds"):
                    total_seconds += worklog["timeSpentSeconds"]

            # Display total time
            if total_seconds > 0:
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                console.print(f"\n[bold]Total time logged: {hours}h {minutes}m[/bold]")

    except JiraCliError as e:
        print_error(f"Failed to get worklogs: {e}")
        raise typer.Exit(1)


@app.command("add")
@validate_command(
    issue_key_params=["issue_key"],
    time_params=["time_spent"],
    command_context="worklog add",
)
def add_worklog(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    time_spent: str = typer.Argument(
        ..., help="Time spent (e.g., '1h 30m', '2d', '4h')"
    ),
    comment: Optional[str] = typer.Option(
        None, "--comment", "-c", help="Comment for the worklog"
    ),
    started: Optional[str] = typer.Option(
        None, "--started", "-s", help="Start time (YYYY-MM-DD HH:MM format)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """Add a worklog to an issue."""
    try:
        client = JiraApiClient()

        # Convert started time to ISO format if provided
        started_iso = None
        if started:
            try:
                dt = datetime.strptime(started, "%Y-%m-%d %H:%M")
                started_iso = dt.isoformat() + ".000+0000"
            except ValueError:
                ErrorFormatter.print_formatted_error(
                    "Invalid DateTime Format",
                    "Start time must be in YYYY-MM-DD HH:MM format.",
                    received=f"'{started}'",
                    expected="YYYY-MM-DD HH:MM format",
                    examples=[
                        "jira-cli worklog add PROJ-123 2h --started '2025-08-27 09:00'",
                        "jira-cli worklog add PROJ-123 '1h 30m' --started '2025-08-27 14:30'",
                        "jira-cli worklog add PROJ-123 4h --started '2025-08-26 08:00'",
                    ],
                    suggestions=[
                        "Use 4-digit year (e.g., 2025)",
                        "Use 2-digit month and day with leading zeros if needed",
                        "Use 24-hour time format (HH:MM)",
                        "Separate date and time with a space",
                        "Enclose the entire datetime in quotes",
                    ],
                    command_context="worklog add",
                )
                raise typer.Exit(1)

        result = client.add_worklog(issue_key, time_spent, comment, started_iso)

        if json_output:
            print_json(result)
        else:
            print_success(f"Added {time_spent} worklog to {issue_key}")
            if comment:
                console.print(f"  Comment: {comment}")

    except JiraCliError as e:
        print_error(f"Failed to add worklog: {e}")
        raise typer.Exit(1)


@app.command("delete")
def delete_worklog(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    worklog_id: str = typer.Argument(..., help="Worklog ID to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete a worklog from an issue."""
    if not yes:
        confirm = typer.confirm(f"Delete worklog {worklog_id} from {issue_key}?")
        if not confirm:
            print_info("Cancelled")
            return

    try:
        client = JiraApiClient()
        client.delete_worklog(issue_key, worklog_id)
        print_success(f"Deleted worklog {worklog_id} from {issue_key}")

    except JiraCliError as e:
        print_error(f"Failed to delete worklog: {e}")
        raise typer.Exit(1)


@app.command("update")
def update_worklog(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    worklog_id: str = typer.Argument(..., help="Worklog ID to update"),
    time_spent: Optional[str] = typer.Option(
        None, "--time", "-t", help="Time spent (e.g., '1h 30m', '2d', '4h')"
    ),
    comment: Optional[str] = typer.Option(
        None, "--comment", "-c", help="Comment for the worklog"
    ),
    started: Optional[str] = typer.Option(
        None, "--started", "-s", help="Start time (YYYY-MM-DD HH:MM format)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """Update a worklog."""
    if not any([time_spent, comment, started]):
        ErrorFormatter.print_formatted_error(
            "No Fields to Update",
            "At least one field must be specified to update the worklog.",
            expected="One or more update parameters",
            examples=[
                f"jira-cli worklog update {issue_key} {worklog_id} --time '2h 30m'",
                f"jira-cli worklog update {issue_key} {worklog_id} --comment 'Updated work description'",
                f"jira-cli worklog update {issue_key} {worklog_id} --started '2025-08-27 10:00'",
                f"jira-cli worklog update {issue_key} {worklog_id} --time 4h --comment 'Completed feature'",
            ],
            suggestions=[
                "Use --time to update the time spent",
                "Use --comment to update the worklog comment",
                "Use --started to update the start time",
                "Multiple fields can be updated in one command",
            ],
            command_context="worklog update",
        )
        raise typer.Exit(1)

    try:
        client = JiraApiClient()

        # Convert started time to ISO format if provided
        started_iso = None
        if started:
            try:
                dt = datetime.strptime(started, "%Y-%m-%d %H:%M")
                started_iso = dt.isoformat() + ".000+0000"
            except ValueError:
                print_error(f"Invalid date format. Use YYYY-MM-DD HH:MM format")
                raise typer.Exit(1)

        result = client.update_worklog(
            issue_key, worklog_id, time_spent, comment, started_iso
        )

        if json_output:
            print_json(result)
        else:
            print_success(f"Updated worklog {worklog_id} in {issue_key}")

    except JiraCliError as e:
        print_error(f"Failed to update worklog: {e}")
        raise typer.Exit(1)
