"""Output formatting utilities for Jira CLI."""

import json
import yaml
from typing import Any, Dict, List, Optional


def _extract_text_from_adf(adf_content: Dict[str, Any]) -> str:
    """Extract plain text from Atlassian Document Format (ADF) content."""
    if not isinstance(adf_content, dict):
        return str(adf_content)

    result_parts = []

    def format_node(node: Dict[str, Any], indent_level: int = 0) -> None:
        """Recursively format ADF nodes."""
        if not isinstance(node, dict):
            return

        node_type = node.get("type", "")
        content = node.get("content", [])
        attrs = node.get("attrs", {})

        if node_type == "text":
            text = node.get("text", "")
            result_parts.append(text)

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
            result_parts.append(f"\n{'#' * level} ")
            for child in content:
                format_node(child, indent_level)
            result_parts.append("\n")

        elif node_type in ["bulletList", "orderedList"]:
            if result_parts and result_parts[-1] != "\n":
                result_parts.append("\n")
            for i, child in enumerate(content):
                if node_type == "orderedList":
                    result_parts.append(f"\n{i + 1}. ")
                else:
                    result_parts.append("\n- ")
                format_node(child, indent_level + 1)

        elif node_type == "listItem":
            for child in content:
                if child.get("type") == "paragraph":
                    for para_child in child.get("content", []):
                        format_node(para_child, indent_level)
                else:
                    format_node(child, indent_level)

        elif node_type == "codeBlock":
            language = attrs.get("language", "")
            if result_parts and result_parts[-1] != "\n":
                result_parts.append("\n")
            result_parts.append(f"\n```{language}\n")
            for child in content:
                if child.get("type") == "text":
                    result_parts.append(child.get("text", ""))
            result_parts.append("\n```\n")

        elif node_type == "blockquote":
            if result_parts and result_parts[-1] != "\n":
                result_parts.append("\n")
            result_parts.append("\n> ")
            for child in content:
                format_node(child, indent_level)
            result_parts.append("\n")

        elif node_type == "rule":
            result_parts.append("\n---\n")

        elif node_type == "mediaSingle":
            media = next(
                (child for child in content if child.get("type") == "media"), None
            )
            if media:
                alt_text = media.get("attrs", {}).get("alt", "Media")
                result_parts.append(f"\n[Attachment: {alt_text}]\n")

        elif content:
            for child in content:
                format_node(child, indent_level)

    format_node(adf_content)
    return "".join(result_parts).strip() or "No description"


def print_success(message: str) -> None:
    """Print success message."""
    print(f"OK: {message}")


def print_error(message: str) -> None:
    """Print error message."""
    print(f"ERROR: {message}")


def print_info(message: str) -> None:
    """Print info message."""
    print(f"INFO: {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    print(f"WARNING: {message}")


def format_issue_table(issues: List[Dict[str, Any]]) -> str:
    """Format issues as plain text output."""
    if not issues:
        return "No issues found."

    lines = []
    for issue in issues:
        fields = issue.get("fields", {})

        key = issue.get("key", "N/A")
        summary = fields.get("summary", "N/A")
        issue_type = fields.get("issuetype", {}).get("name", "N/A")
        status = fields.get("status", {}).get("name", "N/A")
        due_date = fields.get("duedate", "None") or "None"
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

        lines.append(f"{key}\t{summary}\t{issue_type}\t{status}\t{due_date}\t{assignee}\t{priority}")

    return "\n".join(lines)


def format_project_table(projects: List[Dict[str, Any]]) -> str:
    """Format projects as plain text output."""
    if not projects:
        return "No projects found."

    lines = []
    for project in projects:
        key = project.get("key", "N/A")
        name = project.get("name", "N/A")
        project_type = project.get("projectTypeKey", "N/A")
        lead = (
            project.get("lead", {}).get("displayName", "N/A")
            if project.get("lead")
            else "N/A"
        )

        lines.append(f"{key}\t{name}\t{project_type}\t{lead}")

    return "\n".join(lines)


def format_issue_types_table(issue_types: List[Dict[str, Any]]) -> str:
    """Format issue types as plain text output."""
    if not issue_types:
        return "No issue types found."

    lines = []
    for issue_type in issue_types:
        id_val = issue_type.get("id", "N/A")
        name = issue_type.get("name", "N/A")
        description = issue_type.get("description", "N/A")

        lines.append(f"{id_val}\t{name}\t{description}")

    return "\n".join(lines)


def format_transitions_table(transitions: List[Dict[str, Any]]) -> str:
    """Format transitions as plain text output."""
    if not transitions:
        return "No transitions available."

    lines = []
    for transition in transitions:
        id_val = transition.get("id", "N/A")
        name = transition.get("name", "N/A")
        to_status = transition.get("to", {}).get("name", "N/A")

        lines.append(f"{id_val}\t{name}\t{to_status}")

    return "\n".join(lines)


def format_issue_detail(issue: Dict[str, Any]) -> str:
    """Format issue details as plain text."""
    fields = issue.get("fields", {})

    key = issue.get("key", "N/A")
    summary = fields.get("summary", "N/A")

    description_field = fields.get("description", "No description")
    if isinstance(description_field, dict):
        description = _extract_text_from_adf(description_field)
    else:
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

    return f"""Key: {key}
Summary: {summary}
Description: {description}
Status: {status}
Type: {issue_type}
Priority: {priority}
Assignee: {assignee}
Reporter: {reporter}
Created: {created}
Updated: {updated}"""


def format_user_info(user: Dict[str, Any]) -> str:
    """Format user info as plain text."""
    account_id = user.get("accountId", "N/A")
    display_name = user.get("displayName", "N/A")
    email = user.get("emailAddress", "N/A")
    active = user.get("active", False)

    return f"""Display Name: {display_name}
Email: {email}
Account ID: {account_id}
Active: {'Yes' if active else 'No'}"""


def format_users_table(users: List[Dict[str, Any]]) -> str:
    """Format users as plain text output."""
    if not users:
        return "No users found."

    lines = []
    for user in users:
        display_name = user.get("displayName", "N/A")
        email = user.get("emailAddress", "N/A")
        account_id = user.get("accountId", "N/A")
        active = "Yes" if user.get("active", False) else "No"

        lines.append(f"{display_name}\t{email}\t{account_id}\t{active}")

    return "\n".join(lines)


def format_versions_table(versions: List[Dict[str, Any]]) -> str:
    """Format project versions as plain text output."""
    if not versions:
        return "No versions found."

    lines = []
    for version in versions:
        version_id = version.get("id", "N/A")
        name = version.get("name", "N/A")
        released = "Yes" if version.get("released", False) else "No"
        release_date = version.get("releaseDate", "N/A")
        description = version.get("description", "")

        lines.append(f"{version_id}\t{name}\t{released}\t{release_date}\t{description}")

    return "\n".join(lines)


def format_components_table(components: List[Dict[str, Any]]) -> str:
    """Format project components as plain text output."""
    if not components:
        return "No components found."

    lines = []
    for component in components:
        component_id = component.get("id", "N/A")
        name = component.get("name", "N/A")
        lead = (
            component.get("lead", {}).get("displayName", "Unassigned")
            if component.get("lead")
            else "Unassigned"
        )
        description = component.get("description", "")

        lines.append(f"{component_id}\t{name}\t{lead}\t{description}")

    return "\n".join(lines)


def format_project_detail(project: Dict[str, Any]) -> str:
    """Format project details as plain text."""
    key = project.get("key", "N/A")
    name = project.get("name", "N/A")
    project_type = project.get("projectTypeKey", "N/A")
    description = project.get("description", "No description")

    lead = "N/A"
    if project.get("lead"):
        lead = project["lead"].get("displayName", "N/A")

    project_url = project.get("self", "")
    if project_url:
        base_url = "/".join(project_url.split("/")[:3])
        browse_url = f"{base_url}/browse/{key}"
    else:
        browse_url = "N/A"

    return f"""Key: {key}
Name: {name}
Type: {project_type}
Lead: {lead}
Description: {description}
URL: {browse_url}"""


def format_comments(comments: List[Dict[str, Any]], issue_key: str) -> None:
    """Format and print comments for an issue.

    Args:
        comments: List of comment objects from Jira API
        issue_key: The issue key these comments belong to
    """
    if not comments:
        print_info(f"No comments found for {issue_key}")
        return

    print(f"\nComments for {issue_key} ({len(comments)} total)\n")

    for idx, comment in enumerate(comments, 1):
        author = comment.get("author", {})
        author_name = author.get("displayName", "Unknown")
        author_email = author.get("emailAddress", "")

        created = comment.get("created", "N/A")
        updated = comment.get("updated", "N/A")

        created_display = created[:19].replace("T", " ") if created != "N/A" else "N/A"
        updated_display = updated[:19].replace("T", " ") if updated != "N/A" else "N/A"

        body_field = comment.get("body", {})
        if isinstance(body_field, dict):
            body = _extract_text_from_adf(body_field)
        else:
            body = str(body_field) if body_field else "No content"

        print(f"Comment #{idx}")
        print(f"Author: {author_name}", end="")
        if author_email:
            print(f" ({author_email})")
        else:
            print()
        print(f"Created: {created_display}", end="")
        if updated != created:
            print(f" | Updated: {updated_display}")
        else:
            print()
        print(f"\n{body}\n")


def print_yaml(data: Any) -> None:
    """Print data as formatted YAML."""
    try:
        yaml_str = yaml.dump(
            data, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
        print(yaml_str)
    except Exception as e:
        print_error(f"Failed to format YAML: {e}")
        print(json.dumps(data, indent=2, default=str))
