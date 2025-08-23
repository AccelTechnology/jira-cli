"""Issue-related commands for Jira CLI."""

import json
from typing import Optional, List
import typer
from rich.console import Console

from ..utils.api import JiraApiClient
from ..utils.formatting import (
    print_json, print_error, print_success, print_info,
    format_issue_table, format_issue_detail
)
from ..exceptions import JiraCliError

console = Console()
app = typer.Typer(help="Manage Jira issues")


def text_to_adf(text: str) -> dict:
    """Convert plain text to Atlassian Document Format (ADF)."""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "text": text,
                        "type": "text"
                    }
                ]
            }
        ]
    }


@app.command("search")
def search_issues(
    jql: str = typer.Argument(..., help="JQL query string"),
    fields: Optional[List[str]] = typer.Option(None, "--field", "-f", help="Fields to include in response"),
    max_results: int = typer.Option(50, "--max-results", "-m", help="Maximum number of results"),
    start_at: int = typer.Option(0, "--start-at", "-s", help="Starting index for pagination"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    table: bool = typer.Option(False, "--table", help="Output as table")
):
    """Search for issues using JQL."""
    try:
        client = JiraApiClient()
        result = client.search_issues(jql, fields, max_results, start_at)
        
        if json_output:
            print_json(result)
        elif table:
            issues_table = format_issue_table(result.get('issues', []))
            console.print(issues_table)
        else:
            print_json(result)
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("get")
def get_issue(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    fields: Optional[List[str]] = typer.Option(None, "--field", "-f", help="Fields to include in response"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    detail: bool = typer.Option(False, "--detail", help="Show detailed view")
):
    """Get issue by key."""
    try:
        client = JiraApiClient()
        issue = client.get_issue(issue_key, fields)
        
        if json_output:
            print_json(issue)
        elif detail:
            issue_panel = format_issue_detail(issue)
            console.print(issue_panel)
        else:
            print_json(issue)
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("create")
def create_issue(
    project_key: str = typer.Option(..., "--project", "-p", help="Project key"),
    summary: str = typer.Option(..., "--summary", "-s", help="Issue summary"),
    issue_type: str = typer.Option("Task", "--type", "-t", help="Issue type"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Issue description"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Assignee account ID"),
    priority: Optional[str] = typer.Option(None, "--priority", help="Priority name"),
    labels: Optional[List[str]] = typer.Option(None, "--label", "-l", help="Labels to add"),
    epic: Optional[str] = typer.Option(None, "--epic", "-e", help="Epic issue key to link this story to"),
    due_date: Optional[str] = typer.Option(None, "--due-date", help="Due date in YYYY-MM-DD format"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Create new issue."""
    try:
        client = JiraApiClient()
        
        issue_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": issue_type}
            }
        }
        
        if description:
            issue_data["fields"]["description"] = text_to_adf(description)
        
        if assignee:
            issue_data["fields"]["assignee"] = {"accountId": assignee}
        
        if priority:
            issue_data["fields"]["priority"] = {"name": priority}
        
        if labels:
            issue_data["fields"]["labels"] = labels
        
        if due_date:
            issue_data["fields"]["duedate"] = due_date
        
        # Handle epic linking for stories
        if epic and issue_type.lower() in ['story', 'task', 'bug']:
            issue_data["fields"]["parent"] = {"key": epic}
        
        result = client.create_issue(issue_data)
        
        if json_output:
            print_json(result)
        else:
            issue_key = result.get('key')
            print_success(f"Issue created: {issue_key}")
            print_json(result)
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("update")
def update_issue(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    summary: Optional[str] = typer.Option(None, "--summary", "-s", help="New summary"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="New description"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="New assignee account ID"),
    priority: Optional[str] = typer.Option(None, "--priority", help="New priority name"),
    labels: Optional[List[str]] = typer.Option(None, "--label", "-l", help="Labels to set"),
    epic: Optional[str] = typer.Option(None, "--epic", "-e", help="Epic issue key to link this story to"),
    due_date: Optional[str] = typer.Option(None, "--due-date", help="Due date in YYYY-MM-DD format"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Update existing issue."""
    try:
        client = JiraApiClient()
        
        fields = {}
        
        if summary:
            fields["summary"] = summary
        
        if description:
            fields["description"] = text_to_adf(description)
        
        if assignee:
            fields["assignee"] = {"accountId": assignee}
        
        if priority:
            fields["priority"] = {"name": priority}
        
        if labels:
            fields["labels"] = labels
        
        if epic:
            fields["parent"] = {"key": epic}
        
        if due_date:
            fields["duedate"] = due_date
        
        if not fields:
            print_error("No fields to update specified")
            raise typer.Exit(1)
        
        update_data = {"fields": fields}
        client.update_issue(issue_key, update_data)
        
        if json_output:
            print_json({"message": "Issue updated successfully"})
        else:
            print_success(f"Issue {issue_key} updated successfully")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("assign")
def assign_issue(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    assignee: str = typer.Argument(..., help="Assignee account ID (use 'none' to unassign)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Assign issue to user."""
    try:
        client = JiraApiClient()
        
        assignee_data = None if assignee.lower() == 'none' else {"accountId": assignee}
        update_data = {"fields": {"assignee": assignee_data}}
        
        client.update_issue(issue_key, update_data)
        
        if json_output:
            print_json({"message": "Issue assigned successfully"})
        else:
            action = "unassigned" if assignee.lower() == 'none' else f"assigned to {assignee}"
            print_success(f"Issue {issue_key} {action}")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("transitions")
def get_transitions(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Get available transitions for issue."""
    try:
        client = JiraApiClient()
        result = client.get_transitions(issue_key)
        
        if json_output:
            print_json(result)
        else:
            from ..utils.formatting import format_transitions_table
            transitions = result.get('transitions', [])
            if transitions:
                transitions_table = format_transitions_table(transitions)
                console.print(transitions_table)
            else:
                print_info("No transitions available")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("transition")
def transition_issue(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    transition_id: str = typer.Argument(..., help="Transition ID"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Transition issue to new status."""
    try:
        client = JiraApiClient()
        client.transition_issue(issue_key, transition_id)
        
        if json_output:
            print_json({"message": "Issue transitioned successfully"})
        else:
            print_success(f"Issue {issue_key} transitioned using transition {transition_id}")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("comment")
def add_comment(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    body: str = typer.Argument(..., help="Comment text"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Add comment to issue."""
    try:
        client = JiraApiClient()
        result = client.add_comment(issue_key, body)
        
        if json_output:
            print_json(result)
        else:
            comment_id = result.get('id')
            print_success(f"Comment added to {issue_key} (ID: {comment_id})")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("epic-stories")
def list_epic_stories(
    epic_key: str = typer.Argument(..., help="Epic issue key (e.g., PROJ-1)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    table: bool = typer.Option(False, "--table", help="Output as table")
):
    """List all stories under an epic."""
    try:
        client = JiraApiClient()
        jql = f"parent = {epic_key}"
        result = client.search_issues(jql)
        
        if json_output:
            print_json(result)
        elif table:
            issues_table = format_issue_table(result.get('issues', []))
            console.print(issues_table)
        else:
            print_json(result)
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("delete")
def delete_issue(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")
):
    """Delete an issue."""
    try:
        if not force:
            confirmation = typer.confirm(f"Are you sure you want to delete issue {issue_key}? This action cannot be undone.")
            if not confirmation:
                print_info("Delete cancelled.")
                return
        
        client = JiraApiClient()
        client.delete_issue(issue_key)
        
        if json_output:
            print_json({"message": f"Issue {issue_key} deleted successfully"})
        else:
            print_success(f"Issue {issue_key} deleted successfully")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)