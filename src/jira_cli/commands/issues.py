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


@app.command("subtasks")
def list_subtasks(
    parent_key: str = typer.Argument(..., help="Parent issue key (e.g., PROJ-123)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    table: bool = typer.Option(False, "--table", help="Output as table")
):
    """List subtasks of a parent issue."""
    try:
        client = JiraApiClient()
        result = client.get_subtasks(parent_key)
        
        if json_output:
            print_json(result)
        elif table:
            subtasks = result.get('issues', [])
            if subtasks:
                subtasks_table = format_issue_table(subtasks)
                console.print(subtasks_table)
            else:
                print_info(f"No subtasks found for {parent_key}")
        else:
            subtasks = result.get('issues', [])
            if subtasks:
                print_json(result)
            else:
                print_info(f"No subtasks found for {parent_key}")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("create-subtask")
def create_subtask(
    parent_key: str = typer.Option(..., "--parent", "-p", help="Parent issue key"),
    summary: str = typer.Option(..., "--summary", "-s", help="Subtask summary"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Subtask description"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Assignee account ID"),
    priority: Optional[str] = typer.Option(None, "--priority", help="Priority name"),
    labels: Optional[List[str]] = typer.Option(None, "--label", "-l", help="Labels to add"),
    due_date: Optional[str] = typer.Option(None, "--due-date", help="Due date in YYYY-MM-DD format"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Create a subtask under a parent issue."""
    try:
        client = JiraApiClient()
        
        # Get parent issue to extract project information
        parent_issue = client.get_issue(parent_key, fields=['project'])
        project_key = parent_issue['fields']['project']['key']
        
        subtask_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary
            }
        }
        
        if description:
            subtask_data["fields"]["description"] = text_to_adf(description)
        
        if assignee:
            subtask_data["fields"]["assignee"] = {"accountId": assignee}
        
        if priority:
            subtask_data["fields"]["priority"] = {"name": priority}
        
        if labels:
            subtask_data["fields"]["labels"] = labels
        
        if due_date:
            subtask_data["fields"]["duedate"] = due_date
        
        result = client.create_subtask(parent_key, subtask_data)
        
        if json_output:
            print_json(result)
        else:
            subtask_key = result.get('key')
            print_success(f"Subtask created: {subtask_key} under parent {parent_key}")
            print_json(result)
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("link-subtask")
def link_subtask(
    subtask_key: str = typer.Argument(..., help="Subtask issue key (e.g., PROJ-456)"),
    parent_key: str = typer.Argument(..., help="Parent issue key (e.g., PROJ-123)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Link an existing issue as a subtask to a parent issue."""
    try:
        client = JiraApiClient()
        client.link_subtask_to_parent(subtask_key, parent_key)
        
        if json_output:
            print_json({"message": f"Issue {subtask_key} linked as subtask to {parent_key}"})
        else:
            print_success(f"Issue {subtask_key} linked as subtask to {parent_key}")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("unlink-subtask")
def unlink_subtask(
    subtask_key: str = typer.Argument(..., help="Subtask issue key (e.g., PROJ-456)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Unlink a subtask from its parent issue."""
    try:
        client = JiraApiClient()
        
        # Remove parent link by setting it to None
        update_data = {
            "fields": {
                "parent": None
            }
        }
        client.update_issue(subtask_key, update_data)
        
        if json_output:
            print_json({"message": f"Subtask {subtask_key} unlinked from parent"})
        else:
            print_success(f"Subtask {subtask_key} unlinked from parent")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


# New hierarchical management functions

@app.command("create-epic")
def create_epic(
    summary: str = typer.Option(..., "--summary", "-s", help="Epic summary"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Epic description (supports markdown)"),
    project_key: str = typer.Option("ACCELERP", "--project", "-p", help="Project key"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Assignee account ID"),
    labels: Optional[List[str]] = typer.Option(None, "--label", "-l", help="Labels to add"),
    due_date: Optional[str] = typer.Option(None, "--due-date", help="Due date in YYYY-MM-DD format"),
    no_markdown: bool = typer.Option(False, "--no-markdown", help="Treat description as plain text (disable markdown parsing)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Create a new epic."""
    try:
        client = JiraApiClient()
        
        epic_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": "Epic"}
            }
        }
        
        if description:
            epic_data["fields"]["description"] = text_to_adf(description)
        
        if assignee:
            epic_data["fields"]["assignee"] = {"accountId": assignee}
        
        if labels:
            epic_data["fields"]["labels"] = labels
        
        if due_date:
            epic_data["fields"]["duedate"] = due_date
        
        result = client.create_issue(epic_data)
        
        if json_output:
            print_json(result)
        else:
            epic_key = result.get('key')
            print_success(f"Epic created: {epic_key}")
            print_json(result)
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


def create_epic_interactive(project_key: str, summary: Optional[str] = None, json_output: bool = False):
    """Interactive epic creation function."""
    try:
        if not summary:
            summary = typer.prompt("Epic summary")
        
        description = typer.prompt("Epic description (press Enter to skip)", default="", show_default=False)
        assignee = typer.prompt("Assignee account ID (press Enter to skip)", default="", show_default=False)
        due_date = typer.prompt("Due date (YYYY-MM-DD, press Enter to skip)", default="", show_default=False)
        
        client = JiraApiClient()
        
        epic_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": "Epic"}
            }
        }
        
        if description.strip():
            epic_data["fields"]["description"] = text_to_adf(description.strip())
        
        if assignee.strip():
            epic_data["fields"]["assignee"] = {"accountId": assignee.strip()}
        
        if due_date.strip():
            epic_data["fields"]["duedate"] = due_date.strip()
        
        result = client.create_issue(epic_data)
        
        if json_output:
            print_json(result)
        else:
            epic_key = result.get('key')
            print_success(f"Epic created: {epic_key}")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


def edit_epic_interactive(epic_key: str, summary: Optional[str] = None, json_output: bool = False):
    """Interactive epic editing function."""
    try:
        print_info("Epic interactive editing not yet implemented")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


def delete_epic_interactive(epic_key: str, json_output: bool = False):
    """Interactive epic deletion function."""
    try:
        print_info("Epic interactive deletion not yet implemented")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


def show_issue_tree(issue_key: str, json_output: bool = False, expand_all: bool = False):
    """Show hierarchical tree view of issue and its descendants."""
    try:
        client = JiraApiClient()
        
        # Get the root issue
        root_issue = client.get_issue(issue_key, fields=['summary', 'issuetype', 'status', 'assignee'])
        root_fields = root_issue['fields']
        
        if json_output:
            # Simple tree structure for JSON output
            tree_data = {
                "key": issue_key,
                "summary": root_fields.get('summary', 'N/A'),
                "type": root_fields['issuetype']['name'],
                "status": root_fields.get('status', {}).get('name', 'N/A'),
                "assignee": root_fields.get('assignee', {}).get('displayName', 'Unassigned') if root_fields.get('assignee') else 'Unassigned',
                "children": []
            }
            print_json(tree_data)
        else:
            # Pretty print tree view
            from rich.tree import Tree
            
            issue_type = root_fields['issuetype']['name']
            status = root_fields.get('status', {}).get('name', 'N/A')
            assignee = root_fields.get('assignee', {}).get('displayName', 'Unassigned') if root_fields.get('assignee') else 'Unassigned'
            summary = root_fields.get('summary', 'N/A')
            
            # Create root tree
            tree = Tree(f"[bold blue]{issue_key}[/bold blue] {summary}")
            tree.add(f"[dim]Type: {issue_type} | Status: {status} | Assignee: {assignee}[/dim]")
            
            # Get and display children
            children_result = client.search_issues(f"parent = {issue_key}", fields=['summary', 'issuetype', 'status', 'assignee'])
            
            for child in children_result.get('issues', []):
                child_fields = child['fields']
                child_type = child_fields['issuetype']['name']
                child_status = child_fields.get('status', {}).get('name', 'N/A')
                child_assignee = child_fields.get('assignee', {}).get('displayName', 'Unassigned') if child_fields.get('assignee') else 'Unassigned'
                child_summary = child_fields.get('summary', 'N/A')
                
                # Add child to tree
                child_branch = tree.add(f"[green]{child['key']}[/green] {child_summary}")
                child_branch.add(f"[dim]Type: {child_type} | Status: {child_status} | Assignee: {child_assignee}[/dim]")
                
                # Add subtasks if expand_all is True or if this is a story and we want to show subtasks
                if expand_all or child_type.lower() == 'story':
                    subtasks_result = client.get_subtasks(child['key'])
                    for subtask in subtasks_result.get('issues', []):
                        subtask_fields = subtask['fields']
                        subtask_status = subtask_fields.get('status', {}).get('name', 'N/A')
                        subtask_assignee = subtask_fields.get('assignee', {}).get('displayName', 'Unassigned') if subtask_fields.get('assignee') else 'Unassigned'
                        subtask_summary = subtask_fields.get('summary', 'N/A')
                        
                        subtask_branch = child_branch.add(f"[yellow]{subtask['key']}[/yellow] {subtask_summary}")
                        subtask_branch.add(f"[dim]Type: Sub-task | Status: {subtask_status} | Assignee: {subtask_assignee}[/dim]")
            
            console.print(tree)
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


def show_issue_hierarchy(issue_key: str, json_output: bool = False):
    """Show issue in its hierarchy context (parent and children)."""
    try:
        client = JiraApiClient()
        
        # Get the issue
        issue = client.get_issue(issue_key, fields=['summary', 'issuetype', 'status', 'assignee', 'parent'])
        issue_fields = issue['fields']
        
        hierarchy_data = {
            "issue": {
                "key": issue_key,
                "summary": issue_fields.get('summary', 'N/A'),
                "type": issue_fields['issuetype']['name'],
                "status": issue_fields.get('status', {}).get('name', 'N/A'),
                "assignee": issue_fields.get('assignee', {}).get('displayName', 'Unassigned') if issue_fields.get('assignee') else 'Unassigned'
            },
            "parent": None,
            "children": []
        }
        
        # Get parent if exists
        if issue_fields.get('parent'):
            parent_key = issue_fields['parent']['key']
            parent_issue = client.get_issue(parent_key, fields=['summary', 'issuetype', 'status', 'assignee'])
            parent_fields = parent_issue['fields']
            
            hierarchy_data["parent"] = {
                "key": parent_key,
                "summary": parent_fields.get('summary', 'N/A'),
                "type": parent_fields['issuetype']['name'],
                "status": parent_fields.get('status', {}).get('name', 'N/A'),
                "assignee": parent_fields.get('assignee', {}).get('displayName', 'Unassigned') if parent_fields.get('assignee') else 'Unassigned'
            }
        
        # Get children
        children_result = client.search_issues(f"parent = {issue_key}", fields=['summary', 'issuetype', 'status', 'assignee'])
        for child in children_result.get('issues', []):
            child_fields = child['fields']
            hierarchy_data["children"].append({
                "key": child['key'],
                "summary": child_fields.get('summary', 'N/A'),
                "type": child_fields['issuetype']['name'],
                "status": child_fields.get('status', {}).get('name', 'N/A'),
                "assignee": child_fields.get('assignee', {}).get('displayName', 'Unassigned') if child_fields.get('assignee') else 'Unassigned'
            })
        
        if json_output:
            print_json(hierarchy_data)
        else:
            # Pretty print hierarchy
            console.print(f"\n[bold]Hierarchy for {issue_key}:[/bold]")
            
            # Show parent
            if hierarchy_data["parent"]:
                parent = hierarchy_data["parent"]
                console.print(f"[blue]↑ Parent:[/blue] [green]{parent['key']}[/green] {parent['summary']}")
                console.print(f"  [dim]Type: {parent['type']} | Status: {parent['status']} | Assignee: {parent['assignee']}[/dim]")
                console.print()
            
            # Show current issue
            current = hierarchy_data["issue"]
            console.print(f"[bold blue]→ Current:[/bold blue] [green]{current['key']}[/green] {current['summary']}")
            console.print(f"  [dim]Type: {current['type']} | Status: {current['status']} | Assignee: {current['assignee']}[/dim]")
            
            # Show children
            if hierarchy_data["children"]:
                console.print(f"\n[blue]↓ Children ({len(hierarchy_data['children'])}):[/blue]")
                for child in hierarchy_data["children"]:
                    console.print(f"  [green]{child['key']}[/green] {child['summary']}")
                    console.print(f"  [dim]Type: {child['type']} | Status: {child['status']} | Assignee: {child['assignee']}[/dim]")
            else:
                console.print("\n[dim]No children[/dim]")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


# Subtask enhancements

def edit_subtask_interactive(subtask_key: str, json_output: bool = False):
    """Interactive edit function for subtasks."""
    try:
        print_info("Interactive subtask editing not yet fully implemented")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


def delete_subtask_interactive(subtask_key: str, json_output: bool = False):
    """Interactive delete function for subtasks."""
    try:
        print_info("Interactive subtask deletion not yet fully implemented")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


# Story management functions

def create_story_interactive(epic_key: str, summary: Optional[str] = None, json_output: bool = False):
    """Interactive story creation function."""
    try:
        client = JiraApiClient()
        
        # Get epic info to determine project
        epic = client.get_issue(epic_key, fields=['project'])
        project_key = epic['fields']['project']['key']
        
        if not summary:
            summary = typer.prompt("Story summary")
        
        description = typer.prompt("Story description (press Enter to skip)", default="", show_default=False)
        assignee = typer.prompt("Assignee account ID (press Enter to skip)", default="", show_default=False)
        due_date = typer.prompt("Due date (YYYY-MM-DD, press Enter to skip)", default="", show_default=False)
        
        story_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": "Story"},
                "parent": {"key": epic_key}
            }
        }
        
        if description.strip():
            story_data["fields"]["description"] = text_to_adf(description.strip())
        
        if assignee.strip():
            story_data["fields"]["assignee"] = {"accountId": assignee.strip()}
        
        if due_date.strip():
            story_data["fields"]["duedate"] = due_date.strip()
        
        result = client.create_issue(story_data)
        
        if json_output:
            print_json(result)
        else:
            story_key = result.get('key')
            print_success(f"Story created: {story_key} under epic {epic_key}")
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)