"""Output formatting utilities for Jira CLI."""

import json
import yaml
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

console = Console()


def _extract_text_from_adf(adf_content: Dict[str, Any]) -> str:
    """Extract formatted text from Atlassian Document Format (ADF) content with rich formatting."""
    if not isinstance(adf_content, dict):
        return str(adf_content)

    result_parts = []

    def format_node(node: Dict[str, Any], indent_level: int = 0) -> None:
        """Recursively format ADF nodes with proper structure."""
        if not isinstance(node, dict):
            return

        node_type = node.get("type", "")
        content = node.get("content", [])
        attrs = node.get("attrs", {})

        if node_type == "text":
            text = node.get("text", "")
            marks = node.get("marks", [])

            # Apply text formatting based on marks
            formatted_text = text
            for mark in marks:
                mark_type = mark.get("type", "")
                if mark_type == "strong":
                    formatted_text = f"[bold]{formatted_text}[/bold]"
                elif mark_type == "em":
                    formatted_text = f"[italic]{formatted_text}[/italic]"
                elif mark_type == "code":
                    formatted_text = f"[yellow]{formatted_text}[/yellow]"
                elif mark_type == "link":
                    href = mark.get("attrs", {}).get("href", "")
                    formatted_text = f"[link={href}]{formatted_text}[/link]"

            result_parts.append(formatted_text)

        elif node_type == "paragraph":
            if result_parts and result_parts[-1] != "\n":
                result_parts.append("\n")
            if content:
                for child in content:
                    format_node(child, indent_level)
            result_parts.append("\n")

        elif node_type == "heading":
            level = attrs.get("level", 1)
            if result_parts and result_parts[-1] != "\n":
                result_parts.append("\n")
            result_parts.append(f"\n[bold cyan]{'#' * level} ")
            for child in content:
                format_node(child, indent_level)
            result_parts.append("[/bold cyan]\n")

        elif node_type in ["bulletList", "orderedList"]:
            if result_parts and result_parts[-1] != "\n":
                result_parts.append("\n")
            for i, child in enumerate(content):
                if node_type == "orderedList":
                    result_parts.append(f"\n{i + 1}. ")
                else:
                    result_parts.append("\n• ")
                format_node(child, indent_level + 1)

        elif node_type == "listItem":
            # For list items, process content directly without adding paragraph breaks
            for child in content:
                if child.get("type") == "paragraph":
                    # Handle paragraph content directly for list items
                    for para_child in child.get("content", []):
                        format_node(para_child, indent_level)
                else:
                    format_node(child, indent_level)

        elif node_type == "codeBlock":
            language = attrs.get("language", "")
            if result_parts and result_parts[-1] != "\n":
                result_parts.append("\n")
            result_parts.append(f"\n[dim]```{language}[/dim]\n")
            for child in content:
                if child.get("type") == "text":
                    result_parts.append(f"[yellow]{child.get('text', '')}[/yellow]")
            result_parts.append("\n[dim]```[/dim]\n")

        elif node_type == "blockquote":
            if result_parts and result_parts[-1] != "\n":
                result_parts.append("\n")
            result_parts.append("\n[dim]> [/dim]")
            for child in content:
                format_node(child, indent_level)
            result_parts.append("\n")

        elif node_type == "rule":
            result_parts.append(
                "\n[dim]────────────────────────────────────────[/dim]\n"
            )

        elif node_type == "mediaSingle":
            # Handle media/attachments
            media = next(
                (child for child in content if child.get("type") == "media"), None
            )
            if media:
                alt_text = media.get("attrs", {}).get("alt", "Media")
                result_parts.append(f"\n[cyan]📎 {alt_text}[/cyan]\n")

        elif content:
            # Handle other node types with content
            for child in content:
                format_node(child, indent_level)

    format_node(adf_content)
    return "".join(result_parts).strip() or "No description"


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
        fields = issue.get("fields", {})

        key = issue.get("key", "N/A")
        summary = fields.get("summary", "N/A")[:30] + (
            "..." if len(fields.get("summary", "")) > 30 else ""
        )
        issue_type = fields.get("issuetype", {}).get("name", "N/A")
        status = fields.get("status", {}).get("name", "N/A")
        due_date = (
            fields.get("duedate", "None")[:10] if fields.get("duedate") else "None"
        )
        assignee = (
            fields.get("assignee", {}).get("displayName", "Unassigned")
            if fields.get("assignee")
            else "Unassigned"
        )
        priority = (
            fields.get("priority", {}).get("name", "N/A")
            if fields.get("priority")
            else "N/A"
        )

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
        key = project.get("key", "N/A")
        name = project.get("name", "N/A")
        project_type = project.get("projectTypeKey", "N/A")
        lead = (
            project.get("lead", {}).get("displayName", "N/A")
            if project.get("lead")
            else "N/A"
        )

        table.add_row(key, name, project_type, lead)

    return table


def format_issue_types_table(issue_types: List[Dict[str, Any]]) -> Table:
    """Format issue types as a table."""
    table = Table(title="Issue Types")

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Description", style="yellow")

    for issue_type in issue_types:
        id_val = issue_type.get("id", "N/A")
        name = issue_type.get("name", "N/A")
        description = issue_type.get("description", "N/A")[:50] + (
            "..." if len(issue_type.get("description", "")) > 50 else ""
        )

        table.add_row(id_val, name, description)

    return table


def format_transitions_table(transitions: List[Dict[str, Any]]) -> Table:
    """Format transitions as a table."""
    table = Table(title="Available Transitions")

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("To Status", style="yellow")

    for transition in transitions:
        id_val = transition.get("id", "N/A")
        name = transition.get("name", "N/A")
        to_status = transition.get("to", {}).get("name", "N/A")

        table.add_row(id_val, name, to_status)

    return table


def format_issue_detail(issue: Dict[str, Any]) -> Panel:
    """Format issue details as a panel."""
    fields = issue.get("fields", {})

    key = issue.get("key", "N/A")
    summary = fields.get("summary", "N/A")

    # Handle description field safely - it might be ADF format or string
    description_field = fields.get("description", "No description")
    if isinstance(description_field, dict):
        # ADF format - extract text content with rich formatting
        description = _extract_text_from_adf(description_field)
    else:
        # Regular string
        description = str(description_field) if description_field else "No description"

    status = fields.get("status", {}).get("name", "N/A")
    assignee = (
        fields.get("assignee", {}).get("displayName", "Unassigned")
        if fields.get("assignee")
        else "Unassigned"
    )
    reporter = (
        fields.get("reporter", {}).get("displayName", "N/A")
        if fields.get("reporter")
        else "N/A"
    )
    priority = (
        fields.get("priority", {}).get("name", "N/A")
        if fields.get("priority")
        else "N/A"
    )
    issue_type = fields.get("issuetype", {}).get("name", "N/A")
    created = fields.get("created", "N/A")[:10] if fields.get("created") else "N/A"
    updated = fields.get("updated", "N/A")[:10] if fields.get("updated") else "N/A"

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
    account_id = user.get("accountId", "N/A")
    display_name = user.get("displayName", "N/A")
    email = user.get("emailAddress", "N/A")
    active = user.get("active", False)

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
        display_name = user.get("displayName", "N/A")
        email = user.get("emailAddress", "N/A")
        account_id = user.get("accountId", "N/A")
        active = "Yes" if user.get("active", False) else "No"

        table.add_row(display_name, email, account_id, active)

    return table


def format_versions_table(versions: List[Dict[str, Any]]) -> Table:
    """Format project versions as a table."""
    table = Table(title="Project Versions")

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Released", style="green")
    table.add_column("Release Date", style="blue", no_wrap=True)
    table.add_column("Description", style="yellow")

    for version in versions:
        version_id = version.get("id", "N/A")
        name = version.get("name", "N/A")
        released = "Yes" if version.get("released", False) else "No"
        release_date = version.get("releaseDate", "N/A")
        description = version.get("description", "")[:50] + (
            "..." if len(version.get("description", "")) > 50 else ""
        )

        table.add_row(version_id, name, released, release_date, description)

    return table


def format_components_table(components: List[Dict[str, Any]]) -> Table:
    """Format project components as a table."""
    table = Table(title="Project Components")

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Lead", style="green")
    table.add_column("Description", style="yellow")

    for component in components:
        component_id = component.get("id", "N/A")
        name = component.get("name", "N/A")
        lead = (
            component.get("lead", {}).get("displayName", "Unassigned")
            if component.get("lead")
            else "Unassigned"
        )
        description = component.get("description", "")[:50] + (
            "..." if len(component.get("description", "")) > 50 else ""
        )

        table.add_row(component_id, name, lead, description)

    return table


def format_project_detail(project: Dict[str, Any]) -> Panel:
    """Format project details as a panel."""
    key = project.get("key", "N/A")
    name = project.get("name", "N/A")
    project_type = project.get("projectTypeKey", "N/A")
    description = project.get("description", "No description")

    # Get lead information
    lead = "N/A"
    if project.get("lead"):
        lead = project["lead"].get("displayName", "N/A")

    # Get project URL if available
    project_url = project.get("self", "")
    if project_url:
        # Extract base URL and create browse URL
        base_url = "/".join(project_url.split("/")[:3])
        browse_url = f"{base_url}/browse/{key}"
    else:
        browse_url = "N/A"

    content = f"""[bold]Name:[/bold] {name}
[bold]Key:[/bold] {key}
[bold]Type:[/bold] {project_type}
[bold]Lead:[/bold] {lead}
[bold]Description:[/bold] {description}
[bold]URL:[/bold] [link={browse_url}]{browse_url}[/link]"""

    return Panel(content, title=f"Project: {key}", title_align="left")


def format_comments(comments: List[Dict[str, Any]], issue_key: str) -> None:
    """Format and print comments for an issue.

    Args:
        comments: List of comment objects from Jira API
        issue_key: The issue key these comments belong to
    """
    if not comments:
        print_info(f"No comments found for {issue_key}")
        return

    console.print(f"\n[bold cyan]Comments for {issue_key}[/bold cyan] ({len(comments)} total)\n")

    for idx, comment in enumerate(comments, 1):
        author = comment.get("author", {})
        author_name = author.get("displayName", "Unknown")
        author_email = author.get("emailAddress", "")

        created = comment.get("created", "N/A")
        updated = comment.get("updated", "N/A")

        # Format timestamps - extract date and time
        created_display = created[:19].replace("T", " ") if created != "N/A" else "N/A"
        updated_display = updated[:19].replace("T", " ") if updated != "N/A" else "N/A"

        # Extract and format comment body
        body_field = comment.get("body", {})
        if isinstance(body_field, dict):
            body = _extract_text_from_adf(body_field)
        else:
            body = str(body_field) if body_field else "No content"

        # Build header with author and timestamp info
        header_parts = [f"[bold]{author_name}[/bold]"]
        if author_email:
            header_parts.append(f"[dim]({author_email})[/dim]")

        header = " ".join(header_parts)

        # Build timestamp info
        timestamp_info = f"[dim]Created: {created_display}"
        if updated != created:
            timestamp_info += f" | Updated: {updated_display}"
        timestamp_info += "[/dim]"

        # Create content with body
        content = f"{header}\n{timestamp_info}\n\n{body}"

        # Create panel for each comment
        panel = Panel(
            content,
            title=f"Comment #{idx}",
            title_align="left",
            border_style="blue",
        )
        console.print(panel)

        # Add spacing between comments (except after the last one)
        if idx < len(comments):
            console.print()


def print_yaml(data: Any) -> None:
    """Print data as formatted YAML."""
    try:
        yaml_str = yaml.dump(
            data, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
        console.print(yaml_str)
    except Exception as e:
        print_error(f"Failed to format YAML: {e}")
        print_json(data)
