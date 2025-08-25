"""Output formatting utilities for Jira CLI."""

import json
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

console = Console()


def _extract_text_from_adf(adf_content: Dict[str, Any]) -> str:
    """Extract plain text from Atlassian Document Format (ADF) content."""
    if not isinstance(adf_content, dict):
        return str(adf_content)
    
    text_parts = []
    
    def extract_from_node(node: Dict[str, Any]) -> None:
        """Recursively extract text from ADF nodes."""
        if isinstance(node, dict):
            if node.get('type') == 'text':
                text_parts.append(node.get('text', ''))
            elif node.get('content'):
                for child in node['content']:
                    extract_from_node(child)
            elif node.get('attrs', {}).get('text'):
                # For mention nodes
                text_parts.append(node['attrs']['text'])
    
    extract_from_node(adf_content)
    return ' '.join(text_parts).strip() or 'No description'


def print_json(data: Any, indent: int = 2) -> None:
    """Print data as formatted JSON."""
    json_str = json.dumps(data, indent=indent, default=str, ensure_ascii=False)
    console.print_json(json_str)


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[red]✗[/red] {message}")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[blue]ℹ[/blue] {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}")


def format_issue_table(issues: List[Dict[str, Any]]) -> Table:
    """Format issues as a table."""
    table = Table(title="Issues")
    
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Summary", style="white")
    table.add_column("Type", style="blue", no_wrap=True)
    table.add_column("Status", style="yellow")
    table.add_column("Due Date", style="magenta", no_wrap=True)
    table.add_column("Assignee", style="green")
    table.add_column("Priority", style="red")
    
    for issue in issues:
        fields = issue.get('fields', {})
        
        key = issue.get('key', 'N/A')
        summary = fields.get('summary', 'N/A')[:30] + ('...' if len(fields.get('summary', '')) > 30 else '')
        issue_type = fields.get('issuetype', {}).get('name', 'N/A')
        status = fields.get('status', {}).get('name', 'N/A')
        due_date = fields.get('duedate', 'None')[:10] if fields.get('duedate') else 'None'
        assignee = fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'
        priority = fields.get('priority', {}).get('name', 'N/A') if fields.get('priority') else 'N/A'
        
        table.add_row(key, summary, issue_type, status, due_date, assignee, priority)
    
    return table


def format_project_table(projects: List[Dict[str, Any]]) -> Table:
    """Format projects as a table."""
    table = Table(title="Projects")
    
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Type", style="yellow")
    table.add_column("Lead", style="green")
    
    for project in projects:
        key = project.get('key', 'N/A')
        name = project.get('name', 'N/A')
        project_type = project.get('projectTypeKey', 'N/A')
        lead = project.get('lead', {}).get('displayName', 'N/A') if project.get('lead') else 'N/A'
        
        table.add_row(key, name, project_type, lead)
    
    return table


def format_issue_types_table(issue_types: List[Dict[str, Any]]) -> Table:
    """Format issue types as a table."""
    table = Table(title="Issue Types")
    
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Description", style="yellow")
    
    for issue_type in issue_types:
        id_val = issue_type.get('id', 'N/A')
        name = issue_type.get('name', 'N/A')
        description = issue_type.get('description', 'N/A')[:50] + ('...' if len(issue_type.get('description', '')) > 50 else '')
        
        table.add_row(id_val, name, description)
    
    return table


def format_transitions_table(transitions: List[Dict[str, Any]]) -> Table:
    """Format transitions as a table."""
    table = Table(title="Available Transitions")
    
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("To Status", style="yellow")
    
    for transition in transitions:
        id_val = transition.get('id', 'N/A')
        name = transition.get('name', 'N/A')
        to_status = transition.get('to', {}).get('name', 'N/A')
        
        table.add_row(id_val, name, to_status)
    
    return table


def format_issue_detail(issue: Dict[str, Any]) -> Panel:
    """Format issue details as a panel."""
    fields = issue.get('fields', {})
    
    key = issue.get('key', 'N/A')
    summary = fields.get('summary', 'N/A')
    
    # Handle description field safely - it might be ADF format or string
    description_field = fields.get('description', 'No description')
    if isinstance(description_field, dict):
        # ADF format - extract text content
        description = _extract_text_from_adf(description_field)
    else:
        # Regular string
        description = str(description_field) if description_field else 'No description'
    
    # Safely truncate description
    description = description[:200] + ('...' if len(description) > 200 else '')
    
    status = fields.get('status', {}).get('name', 'N/A')
    assignee = fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'
    reporter = fields.get('reporter', {}).get('displayName', 'N/A') if fields.get('reporter') else 'N/A'
    priority = fields.get('priority', {}).get('name', 'N/A') if fields.get('priority') else 'N/A'
    issue_type = fields.get('issuetype', {}).get('name', 'N/A')
    created = fields.get('created', 'N/A')[:10] if fields.get('created') else 'N/A'
    updated = fields.get('updated', 'N/A')[:10] if fields.get('updated') else 'N/A'
    
    content = f"""[bold]Summary:[/bold] {summary}
[bold]Description:[/bold] {description}
[bold]Status:[/bold] {status}
[bold]Type:[/bold] {issue_type}
[bold]Priority:[/bold] {priority}
[bold]Assignee:[/bold] {assignee}
[bold]Reporter:[/bold] {reporter}
[bold]Created:[/bold] {created}
[bold]Updated:[/bold] {updated}"""
    
    return Panel(content, title=f"Issue: {key}", title_align="left")


def format_user_info(user: Dict[str, Any]) -> Panel:
    """Format user info as a panel."""
    account_id = user.get('accountId', 'N/A')
    display_name = user.get('displayName', 'N/A')
    email = user.get('emailAddress', 'N/A')
    active = user.get('active', False)
    
    content = f"""[bold]Display Name:[/bold] {display_name}
[bold]Email:[/bold] {email}
[bold]Account ID:[/bold] {account_id}
[bold]Active:[/bold] {'Yes' if active else 'No'}"""
    
    return Panel(content, title="Current User", title_align="left")


def format_users_table(users: List[Dict[str, Any]]) -> Table:
    """Format users as a table."""
    table = Table(title="Users")
    
    table.add_column("Display Name", style="cyan")
    table.add_column("Email", style="white") 
    table.add_column("Account ID", style="yellow", no_wrap=True)
    table.add_column("Active", style="green")
    
    for user in users:
        display_name = user.get('displayName', 'N/A')
        email = user.get('emailAddress', 'N/A')
        account_id = user.get('accountId', 'N/A')
        active = 'Yes' if user.get('active', False) else 'No'
        
        table.add_row(display_name, email, account_id, active)
    
    return table