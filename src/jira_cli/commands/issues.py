"""Issue-related commands for Jira CLI."""

import json
from typing import Optional, List
import typer
from rich.console import Console

from ..utils.api import JiraApiClient
from ..utils.formatting import (
    print_error,
    print_success,
    print_info,
    format_issue_table,
    format_issue_detail,
    print_yaml,
)
from ..utils.error_handling import ErrorFormatter, handle_api_error
from ..utils.validation import validate_command
from ..utils.markdown_to_adf import markdown_to_adf
from ..exceptions import JiraCliError

console = Console()
app = typer.Typer(help="Manage Jira issues")


def read_description_from_source(
    description: Optional[str], file_path: Optional[str]
) -> Optional[str]:
    """Read description from direct input or file.

    Args:
        description: Direct description text
        file_path: Path to file containing description

    Returns:
        Description text or None if neither provided

    Raises:
        JiraCliError: If file not found or cannot be read
    """
    if description and file_path:
        raise JiraCliError("Cannot specify both --description and --description-file")

    if file_path:
        try:
            import os

            if not os.path.exists(file_path):
                raise JiraCliError(f"Description file not found: {file_path}")

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    print_info(f"Warning: Description file {file_path} is empty")
                return content
        except Exception as e:
            raise JiraCliError(f"Failed to read description file {file_path}: {str(e)}")

    return description


@app.command("search")
@validate_command(jql_params=["jql"], command_context="issues search")
def search_issues(
    jql: str = typer.Argument(..., help="JQL query string"),
    fields: Optional[List[str]] = typer.Option(
        None, "--field", "-f", help="Fields to include in response"
    ),
    max_results: int = typer.Option(
        50, "--max-results", "-m", help="Maximum number of results"
    ),
    start_at: int = typer.Option(
        0, "--start-at", "-s", help="Starting index for pagination"
    ),
):
    """Search for issues using JQL."""
    try:
        client = JiraApiClient()

        # If no fields specified, use default fields for table display
        if fields is None:
            fields = [
                "summary",
                "issuetype",
                "status",
                "assignee",
                "reporter",
                "priority",
                "duedate",
                "created",
                "updated",
            ]

        result = client.search_issues(jql, fields, max_results, start_at)

        issues_table = format_issue_table(result.get("issues", []))
        console.print(issues_table)

    except JiraCliError as e:
        handle_api_error(e, "issues search")
        raise typer.Exit(1)


@app.command("get")
@validate_command(issue_key_params=["issue_key"], command_context="issues get")
def get_issue(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    fields: Optional[List[str]] = typer.Option(
        None, "--field", "-f", help="Fields to include in response"
    ),
):
    """Get issue by key."""
    try:
        client = JiraApiClient()
        issue = client.get_issue(issue_key, fields)

        issue_panel = format_issue_detail(issue)
        console.print(issue_panel)

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("create")
@validate_command(
    project_key_params=["project_key"],
    issue_key_params=["epic", "parent"],
    date_params=["due_date"],
    required_params=["project_key", "summary"],
    command_context="issues create",
)
def create_issue(
    project_key: str = typer.Option(..., "--project", "-p", help="Project key"),
    summary: str = typer.Option(..., "--summary", "-s", help="Issue summary"),
    issue_type: str = typer.Option("Task", "--type", "-t", help="Issue type"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Issue description"
    ),
    description_file: Optional[str] = typer.Option(
        None, "--description-file", "-f", help="Read description from file"
    ),
    assignee: Optional[str] = typer.Option(
        None, "--assignee", "-a", help="Assignee account ID"
    ),
    priority: Optional[str] = typer.Option(None, "--priority", help="Priority name"),
    labels: Optional[List[str]] = typer.Option(
        None, "--label", "-l", help="Labels to add"
    ),
    epic: Optional[str] = typer.Option(
        None, "--epic", "-e", help="Epic issue key to link this story to"
    ),
    parent: Optional[str] = typer.Option(
        None, "--parent", help="Parent issue key (required for subtasks)"
    ),
    due_date: Optional[str] = typer.Option(
        None, "--due-date", help="Due date in YYYY-MM-DD format"
    ),
):
    """Create new issue."""
    try:
        client = JiraApiClient()

        # Validate subtask requirements
        if issue_type.lower() in ["subtask", "sub-task"]:
            if not parent:
                from ..utils.error_handling import ErrorFormatter

                ErrorFormatter.print_formatted_error(
                    "Missing Required Parameter",
                    "Subtasks require a parent issue to be specified.",
                    expected="Parent issue key using --parent parameter",
                    examples=[
                        f"jira-cli issues create --project {project_key} --type Subtask --summary '{summary}' --parent PROJ-123",
                        f"jira-cli issues create --project {project_key} --type Subtask --summary '{summary}' --parent {project_key}-1",
                    ],
                    suggestions=[
                        "Use --parent to specify the parent issue key",
                        "Ensure the parent issue exists and you have permission to create subtasks under it",
                        "Use 'jira-cli issues search' to find suitable parent issues",
                    ],
                    command_context="issues create",
                )
                raise typer.Exit(1)

        # Validate issue type against project configuration
        from ..utils.validation import validate_project_issue_type

        try:
            validated_issue_type = validate_project_issue_type(
                project_key, issue_type, "issues create"
            )
            if validated_issue_type != issue_type:
                print_info(f"Using project-specific issue type: {validated_issue_type}")
                issue_type = validated_issue_type
        except Exception as e:
            # If validation fails, the error is already displayed
            # Just exit without additional error messages
            if "Invalid issue type" in str(e):
                raise typer.Exit(1)
            else:
                print_info(f"Could not validate issue type against project: {e}")

        # Read description from source
        final_description = read_description_from_source(description, description_file)

        # Handle issue type specification - use ID for subtasks to avoid ambiguity
        issue_type_field = {"name": issue_type}
        if issue_type.lower() in ["subtask", "sub-task"]:
            # For subtasks, try to get the correct issue type from available types
            try:
                issue_types = client.get_issue_types()
                # Look for subtask types that match
                subtask_types = [
                    it
                    for it in issue_types
                    if it.get("subtask")
                    and it["name"].lower() in ["subtask", "sub-task"]
                ]

                if subtask_types:
                    # Use the first available subtask type ID
                    issue_type_field = {"id": subtask_types[0]["id"]}
                    print_info(
                        f"Using issue type: {subtask_types[0]['name']} (ID: {subtask_types[0]['id']})"
                    )
            except Exception as e:
                print_info(f"Could not resolve subtask type, using name: {e}")

        issue_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": issue_type_field,
            }
        }

        if final_description:
            issue_data["fields"]["description"] = markdown_to_adf(final_description)

        if assignee:
            issue_data["fields"]["assignee"] = {"accountId": assignee}

        if priority:
            issue_data["fields"]["priority"] = {"name": priority}

        if labels:
            issue_data["fields"]["labels"] = labels

        if due_date:
            issue_data["fields"]["duedate"] = due_date

        # Handle parent relationships
        if parent:
            issue_data["fields"]["parent"] = {"key": parent}
        elif epic and issue_type.lower() in ["story", "task", "bug"]:
            # Handle epic linking for stories (legacy support)
            issue_data["fields"]["parent"] = {"key": epic}

        result = client.create_issue(issue_data)

        issue_key = result.get("key")
        print_success(f"Issue created: {issue_key}")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("update")
def update_issue(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    summary: Optional[str] = typer.Option(None, "--summary", "-s", help="New summary"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="New description"
    ),
    description_file: Optional[str] = typer.Option(
        None, "--description-file", "-f", help="Read description from file"
    ),
    assignee: Optional[str] = typer.Option(
        None, "--assignee", "-a", help="New assignee account ID"
    ),
    priority: Optional[str] = typer.Option(
        None, "--priority", help="New priority name"
    ),
    labels: Optional[List[str]] = typer.Option(
        None, "--label", "-l", help="Labels to set"
    ),
    epic: Optional[str] = typer.Option(
        None, "--epic", "-e", help="Epic issue key to link this story to"
    ),
    due_date: Optional[str] = typer.Option(
        None, "--due-date", help="Due date in YYYY-MM-DD format"
    ),
):
    """Update existing issue."""
    try:
        client = JiraApiClient()

        # Read description from source
        final_description = read_description_from_source(description, description_file)

        fields = {}

        if summary:
            fields["summary"] = summary

        if final_description:
            fields["description"] = markdown_to_adf(final_description)

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
            ErrorFormatter.print_formatted_error(
                "No Fields to Update",
                "At least one field must be specified to update the issue.",
                expected="One or more update parameters",
                examples=[
                    f"jira-cli issues update {issue_key} --summary 'New summary'",
                    f"jira-cli issues update {issue_key} --description 'New description'",
                    f"jira-cli issues update {issue_key} --assignee user@company.com",
                    f"jira-cli issues update {issue_key} --priority High --due-date 2025-12-31",
                ],
                suggestions=[
                    "Use --summary to update the issue summary",
                    "Use --description to update the issue description",
                    "Use --assignee to change the assignee",
                    "Use --priority to change the priority",
                    "Use --due-date to set or change the due date",
                    "Use --labels to set issue labels",
                    "Multiple fields can be updated in one command",
                ],
                command_context="issues update",
            )
            raise typer.Exit(1)

        update_data = {"fields": fields}
        client.update_issue(issue_key, update_data)

        print_success(f"Issue {issue_key} updated successfully")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("assign")
def assign_issue(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    assignee: str = typer.Argument(
        ..., help="Assignee account ID (use 'none' to unassign)"
    ),
):
    """Assign issue to user."""
    try:
        client = JiraApiClient()

        assignee_data = None if assignee.lower() == "none" else {"accountId": assignee}
        update_data = {"fields": {"assignee": assignee_data}}

        client.update_issue(issue_key, update_data)

        action = (
            "unassigned"
            if assignee.lower() == "none"
            else f"assigned to {assignee}"
        )
        print_success(f"Issue {issue_key} {action}")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("transitions")
def get_transitions(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
):
    """Get available transitions for issue."""
    try:
        client = JiraApiClient()
        result = client.get_transitions(issue_key)

        from ..utils.formatting import format_transitions_table

        transitions = result.get("transitions", [])
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
):
    """Transition issue to new status."""
    try:
        client = JiraApiClient()
        client.transition_issue(issue_key, transition_id)

        print_success(
            f"Issue {issue_key} transitioned using transition {transition_id}"
        )

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("comment")
def add_comment(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    body: str = typer.Argument(..., help="Comment text"),
):
    """Add comment to issue."""
    try:
        client = JiraApiClient()
        result = client.add_comment(issue_key, body)

        comment_id = result.get("id")
        print_success(f"Comment added to {issue_key} (ID: {comment_id})")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("comments")
@validate_command(issue_key_params=["issue_key"], command_context="issues comments")
def list_comments(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    max_results: int = typer.Option(
        50, "--max-results", "-m", help="Maximum number of comments to retrieve"
    ),
    start_at: int = typer.Option(
        0, "--start-at", "-s", help="Starting index for pagination"
    ),
    order_by: str = typer.Option(
        "created",
        "--order-by",
        "-o",
        help="Sort order: 'created' (oldest first) or '-created' (newest first)",
    ),
):
    """List comments on an issue."""
    try:
        client = JiraApiClient()
        result = client.get_comments(issue_key, start_at, max_results, order_by)

        from ..utils.formatting import format_comments

        comments = result.get("comments", [])
        format_comments(comments, issue_key)

        # Show pagination info if there are more comments
        total = result.get("total", 0)
        if total > len(comments):
            remaining = total - (start_at + len(comments))
            print_info(
                f"\nShowing {len(comments)} of {total} comments. "
                f"{remaining} more available. "
                f"Use --start-at {start_at + max_results} to see more."
            )

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("epic-stories")
def list_epic_stories(
    epic_key: str = typer.Argument(..., help="Epic issue key (e.g., PROJ-1)"),
):
    """List all stories under an epic."""
    try:
        client = JiraApiClient()
        jql = f"parent = {epic_key}"

        # Use default fields for table display
        fields = [
            "summary",
            "issuetype",
            "status",
            "assignee",
            "reporter",
            "priority",
            "duedate",
            "created",
            "updated",
        ]

        result = client.search_issues(jql, fields)

        issues_table = format_issue_table(result.get("issues", []))
        console.print(issues_table)

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("delete")
def delete_issue(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """Delete an issue."""
    try:
        if not force:
            confirmation = typer.confirm(
                f"Are you sure you want to delete issue {issue_key}? This action cannot be undone."
            )
            if not confirmation:
                print_info("Delete cancelled.")
                return

        client = JiraApiClient()
        client.delete_issue(issue_key)

        print_success(f"Issue {issue_key} deleted successfully")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("subtasks")
def list_subtasks(
    parent_key: str = typer.Argument(..., help="Parent issue key (e.g., PROJ-123)"),
):
    """List subtasks of a parent issue."""
    try:
        client = JiraApiClient()
        result = client.get_subtasks(parent_key)

        subtasks = result.get("issues", [])
        if subtasks:
            subtasks_table = format_issue_table(subtasks)
            console.print(subtasks_table)
        else:
            print_info(f"No subtasks found for {parent_key}")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("create-subtask")
@validate_command(
    issue_key_params=["parent_key"],
    date_params=["due_date"],
    required_params=["parent_key", "summary"],
    command_context="issues create-subtask",
)
def create_subtask(
    parent_key: str = typer.Option(..., "--parent", "-p", help="Parent issue key"),
    summary: str = typer.Option(..., "--summary", "-s", help="Subtask summary"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Subtask description"
    ),
    description_file: Optional[str] = typer.Option(
        None, "--description-file", "-f", help="Read description from file"
    ),
    assignee: Optional[str] = typer.Option(
        None, "--assignee", "-a", help="Assignee email or account ID"
    ),
    priority: Optional[str] = typer.Option(None, "--priority", help="Priority name"),
    labels: Optional[List[str]] = typer.Option(
        None, "--label", "-l", help="Labels to add"
    ),
    due_date: Optional[str] = typer.Option(
        None, "--due-date", help="Due date in YYYY-MM-DD format"
    ),
):
    """Create a subtask under a parent issue."""
    try:
        client = JiraApiClient()

        # Read description from source
        final_description = read_description_from_source(description, description_file)

        # Get parent issue to extract project information and validate parent exists
        try:
            parent_issue = client.get_issue(
                parent_key, fields=["project", "issuetype", "status"]
            )
            project_key = parent_issue["fields"]["project"]["key"]
        except Exception as e:
            from ..utils.error_handling import ErrorFormatter

            ErrorFormatter.print_formatted_error(
                "Parent Issue Not Found",
                f"Could not retrieve parent issue '{parent_key}'. Verify the issue key exists and you have permission to view it.",
                received=f"Parent issue key: '{parent_key}'",
                expected="Valid issue key that exists and you can access",
                examples=[
                    f"{project_key}-123",
                    f"{project_key.upper()}-456" if project_key else "PROJ-789",
                ],
                suggestions=[
                    "Verify the issue key is correct",
                    "Check that the issue exists in Jira",
                    "Ensure you have permission to view the parent issue",
                    f"Use 'jira-cli issues get {parent_key}' to test access",
                ],
                command_context="issues create-subtask",
            )
            raise typer.Exit(1)

        # Resolve assignee if email provided
        account_id = None
        if assignee:
            if "@" in assignee:  # Email format
                try:
                    users = client.search_users(assignee, max_results=1)
                    if not users:
                        from ..utils.error_handling import ErrorFormatter

                        ErrorFormatter.print_formatted_error(
                            "User Not Found",
                            f"No user found with email '{assignee}'",
                            received=f"Email: '{assignee}'",
                            expected="Valid email address of a Jira user",
                            suggestions=[
                                "Verify the email address is correct",
                                "Check that the user exists in your Jira instance",
                                "Use account ID instead of email if known",
                            ],
                            command_context="issues create-subtask",
                        )
                        raise typer.Exit(1)
                    account_id = users[0]["accountId"]
                except Exception as e:
                    print_error(f"Error searching for user '{assignee}': {e}")
                    raise typer.Exit(1)
            else:  # Assume account ID
                account_id = assignee

        # Create subtask data - issue type resolution is handled in the API layer
        subtask_data = {"fields": {"project": {"key": project_key}, "summary": summary}}

        if final_description:
            subtask_data["fields"]["description"] = markdown_to_adf(final_description)

        if account_id:
            subtask_data["fields"]["assignee"] = {"accountId": account_id}

        if priority:
            subtask_data["fields"]["priority"] = {"name": priority}

        if labels:
            subtask_data["fields"]["labels"] = labels

        if due_date:
            subtask_data["fields"]["duedate"] = due_date

        result = client.create_subtask(parent_key, subtask_data)

        subtask_key = result.get("key")
        print_success(f"Subtask created: {subtask_key} under parent {parent_key}")
        if final_description:
            print_info(
                f"Description: {final_description[:100]}{'...' if len(final_description) > 100 else ''}"
            )

    except JiraCliError as e:
        handle_api_error(e, "issues create-subtask")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        raise typer.Exit(1)


@app.command("link-subtask")
def link_subtask(
    subtask_key: str = typer.Argument(..., help="Subtask issue key (e.g., PROJ-456)"),
    parent_key: str = typer.Argument(..., help="Parent issue key (e.g., PROJ-123)"),
):
    """Link an existing issue as a subtask to a parent issue."""
    try:
        client = JiraApiClient()
        client.link_subtask_to_parent(subtask_key, parent_key)

        print_success(f"Issue {subtask_key} linked as subtask to {parent_key}")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("unlink-subtask")
def unlink_subtask(
    subtask_key: str = typer.Argument(..., help="Subtask issue key (e.g., PROJ-456)"),
):
    """Unlink a subtask from its parent issue."""
    try:
        client = JiraApiClient()

        # Remove parent link by setting it to None
        update_data = {"fields": {"parent": None}}
        client.update_issue(subtask_key, update_data)

        print_success(f"Subtask {subtask_key} unlinked from parent")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


# New hierarchical management functions


@app.command("create-epic")
def create_epic(
    summary: str = typer.Option(..., "--summary", "-s", help="Epic summary"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Epic description (supports markdown)"
    ),
    project_key: str = typer.Option("ACCELERP", "--project", "-p", help="Project key"),
    assignee: Optional[str] = typer.Option(
        None, "--assignee", "-a", help="Assignee account ID"
    ),
    labels: Optional[List[str]] = typer.Option(
        None, "--label", "-l", help="Labels to add"
    ),
    due_date: Optional[str] = typer.Option(
        None, "--due-date", help="Due date in YYYY-MM-DD format"
    ),
    no_markdown: bool = typer.Option(
        False,
        "--no-markdown",
        help="Treat description as plain text (disable markdown parsing)",
    ),
):
    """Create a new epic."""
    try:
        client = JiraApiClient()

        epic_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": "Epic"},
            }
        }

        if description:
            epic_data["fields"]["description"] = markdown_to_adf(description)

        if assignee:
            epic_data["fields"]["assignee"] = {"accountId": assignee}

        if labels:
            epic_data["fields"]["labels"] = labels

        if due_date:
            epic_data["fields"]["duedate"] = due_date

        result = client.create_issue(epic_data)

        epic_key = result.get("key")
        print_success(f"Epic created: {epic_key}")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("create-epic")
def create_epic_command(
    project_key: str = typer.Option(..., "--project", "-p", help="Project key"),
    summary: str = typer.Option(..., "--summary", "-s", help="Epic summary"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Epic description"
    ),
    description_file: Optional[str] = typer.Option(
        None, "--description-file", "-f", help="Read description from file"
    ),
    assignee: Optional[str] = typer.Option(
        None, "--assignee", "-a", help="Assignee email or account ID"
    ),
    due_date: Optional[str] = typer.Option(
        None, "--due-date", help="Due date in YYYY-MM-DD format"
    ),
    priority: Optional[str] = typer.Option(None, "--priority", help="Priority name"),
    labels: Optional[List[str]] = typer.Option(
        None, "--label", "-l", help="Labels to add"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Use interactive mode"
    ),
):
    """Create a new epic."""
    if interactive:
        return create_epic_interactive(project_key, summary)

    try:
        client = JiraApiClient()

        # Read description from source
        final_description = read_description_from_source(description, description_file)

        # Resolve assignee if email provided
        account_id = None
        if assignee:
            if "@" in assignee:  # Email format
                users = client.search_users(assignee, max_results=1)
                if not users:
                    print_error(f"User with email '{assignee}' not found")
                    raise typer.Exit(1)
                account_id = users[0]["accountId"]
            else:  # Assume account ID
                account_id = assignee

        epic_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": "Epic"},
            }
        }

        if final_description:
            epic_data["fields"]["description"] = markdown_to_adf(final_description)

        if account_id:
            epic_data["fields"]["assignee"] = {"accountId": account_id}

        if due_date:
            epic_data["fields"]["duedate"] = due_date

        if priority:
            epic_data["fields"]["priority"] = {"name": priority}

        if labels:
            epic_data["fields"]["labels"] = labels

        result = client.create_issue(epic_data)

        epic_key = result.get("key")
        print_success(f"Epic created: {epic_key}")
        if final_description:
            print_info(
                f"Description: {final_description[:100]}{'...' if len(final_description) > 100 else ''}"
            )

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


def create_epic_interactive(
    project_key: str, summary: Optional[str] = None
):
    """Interactive epic creation function."""
    try:
        if not summary:
            summary = typer.prompt("Epic summary")

        description = typer.prompt(
            "Epic description (press Enter to skip)", default="", show_default=False
        )
        assignee = typer.prompt(
            "Assignee account ID (press Enter to skip)", default="", show_default=False
        )
        due_date = typer.prompt(
            "Due date (YYYY-MM-DD, press Enter to skip)", default="", show_default=False
        )

        client = JiraApiClient()

        epic_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": "Epic"},
            }
        }

        if description.strip():
            epic_data["fields"]["description"] = markdown_to_adf(description.strip())

        if assignee.strip():
            epic_data["fields"]["assignee"] = {"accountId": assignee.strip()}

        if due_date.strip():
            epic_data["fields"]["duedate"] = due_date.strip()

        result = client.create_issue(epic_data)

        epic_key = result.get("key")
        print_success(f"Epic created: {epic_key}")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


def edit_epic_interactive(
    epic_key: str, summary: Optional[str] = None
):
    """Interactive epic editing function."""
    try:
        print_info("Epic interactive editing not yet implemented")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


def delete_epic_interactive(epic_key: str):
    """Interactive epic deletion function."""
    try:
        print_info("Epic interactive deletion not yet implemented")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


def show_issue_tree(
    issue_key: str, expand_all: bool = False
):
    """Show hierarchical tree view of issue and its descendants."""
    try:
        client = JiraApiClient()

        # Get the root issue
        root_issue = client.get_issue(
            issue_key, fields=["summary", "issuetype", "status", "assignee"]
        )
        root_fields = root_issue["fields"]

        # Pretty print tree view
        from rich.tree import Tree

        issue_type = root_fields["issuetype"]["name"]
        status = root_fields.get("status", {}).get("name", "N/A")
        assignee = (
            root_fields.get("assignee", {}).get("displayName", "Unassigned")
            if root_fields.get("assignee")
            else "Unassigned"
        )
        summary = root_fields.get("summary", "N/A")

        # Create root tree
        tree = Tree(f"[bold blue]{issue_key}[/bold blue] {summary}")
        tree.add(
            f"[dim]Type: {issue_type} | Status: {status} | Assignee: {assignee}[/dim]"
        )

        # Get and display children
        children_result = client.search_issues(
            f"parent = {issue_key}",
            fields=["summary", "issuetype", "status", "assignee"],
        )

        for child in children_result.get("issues", []):
            child_fields = child["fields"]
            child_type = child_fields["issuetype"]["name"]
            child_status = child_fields.get("status", {}).get("name", "N/A")
            child_assignee = (
                child_fields.get("assignee", {}).get("displayName", "Unassigned")
                if child_fields.get("assignee")
                else "Unassigned"
            )
            child_summary = child_fields.get("summary", "N/A")

            # Add child to tree
            child_branch = tree.add(
                f"[green]{child['key']}[/green] {child_summary}"
            )
            child_branch.add(
                f"[dim]Type: {child_type} | Status: {child_status} | Assignee: {child_assignee}[/dim]"
            )

            # Add subtasks if expand_all is True or if this is a story and we want to show subtasks
            if expand_all or child_type.lower() == "story":
                subtasks_result = client.get_subtasks(child["key"])
                for subtask in subtasks_result.get("issues", []):
                    subtask_fields = subtask["fields"]
                    subtask_status = subtask_fields.get("status", {}).get(
                        "name", "N/A"
                    )
                    subtask_assignee = (
                        subtask_fields.get("assignee", {}).get(
                            "displayName", "Unassigned"
                        )
                        if subtask_fields.get("assignee")
                        else "Unassigned"
                    )
                    subtask_summary = subtask_fields.get("summary", "N/A")

                    subtask_branch = child_branch.add(
                        f"[yellow]{subtask['key']}[/yellow] {subtask_summary}"
                    )
                    subtask_branch.add(
                        f"[dim]Type: Sub-task | Status: {subtask_status} | Assignee: {subtask_assignee}[/dim]"
                    )

        console.print(tree)

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


def show_issue_hierarchy(issue_key: str):
    """Show issue in its hierarchy context (parent, children, and subtasks)."""
    try:
        client = JiraApiClient()

        # Get the issue
        issue = client.get_issue(
            issue_key, fields=["summary", "issuetype", "status", "assignee", "parent"]
        )
        issue_fields = issue["fields"]

        hierarchy_data = {
            "issue": {
                "key": issue_key,
                "summary": issue_fields.get("summary", "N/A"),
                "type": issue_fields["issuetype"]["name"],
                "status": issue_fields.get("status", {}).get("name", "N/A"),
                "assignee": (
                    issue_fields.get("assignee", {}).get("displayName", "Unassigned")
                    if issue_fields.get("assignee")
                    else "Unassigned"
                ),
            },
            "parent": None,
            "children": [],
            "subtasks": [],
        }

        # Get parent if exists
        if issue_fields.get("parent"):
            parent_key = issue_fields["parent"]["key"]
            parent_issue = client.get_issue(
                parent_key, fields=["summary", "issuetype", "status", "assignee"]
            )
            parent_fields = parent_issue["fields"]

            hierarchy_data["parent"] = {
                "key": parent_key,
                "summary": parent_fields.get("summary", "N/A"),
                "type": parent_fields["issuetype"]["name"],
                "status": parent_fields.get("status", {}).get("name", "N/A"),
                "assignee": (
                    parent_fields.get("assignee", {}).get("displayName", "Unassigned")
                    if parent_fields.get("assignee")
                    else "Unassigned"
                ),
            }

        # Get children (for epics, these are stories)
        children_result = client.search_issues(
            f"parent = {issue_key}",
            fields=["summary", "issuetype", "status", "assignee"],
        )
        for child in children_result.get("issues", []):
            child_fields = child["fields"]
            # Distinguish between stories/tasks (children) and subtasks
            is_subtask = child_fields["issuetype"].get("subtask", False)

            child_data = {
                "key": child["key"],
                "summary": child_fields.get("summary", "N/A"),
                "type": child_fields["issuetype"]["name"],
                "status": child_fields.get("status", {}).get("name", "N/A"),
                "assignee": (
                    child_fields.get("assignee", {}).get(
                        "displayName", "Unassigned"
                    )
                    if child_fields.get("assignee")
                    else "Unassigned"
                ),
                "subtasks": [],  # Will be populated for children
            }

            if is_subtask:
                hierarchy_data["subtasks"].append(child_data)
            else:
                # For each child (story), fetch its subtasks
                child_subtasks_result = client.search_issues(
                    f"parent = {child['key']}",
                    fields=["summary", "issuetype", "status", "assignee"],
                )
                for subtask in child_subtasks_result.get("issues", []):
                    subtask_fields = subtask["fields"]
                    child_data["subtasks"].append({
                        "key": subtask["key"],
                        "summary": subtask_fields.get("summary", "N/A"),
                        "type": subtask_fields["issuetype"]["name"],
                        "status": subtask_fields.get("status", {}).get("name", "N/A"),
                        "assignee": (
                            subtask_fields.get("assignee", {}).get(
                                "displayName", "Unassigned"
                            )
                            if subtask_fields.get("assignee")
                            else "Unassigned"
                        ),
                    })
                hierarchy_data["children"].append(child_data)

        # Pretty print hierarchy
        console.print(f"\n[bold]Hierarchy for {issue_key}:[/bold]")

        # Show parent
        if hierarchy_data["parent"]:
            parent = hierarchy_data["parent"]
            console.print(
                f"[blue]↑ Parent:[/blue] [green]{parent['key']}[/green] {parent['summary']}"
            )
            console.print(
                f"  [dim]Type: {parent['type']} | Status: {parent['status']} | Assignee: {parent['assignee']}[/dim]"
            )
            console.print()

        # Show current issue
        current = hierarchy_data["issue"]
        console.print(
            f"[bold blue]→ Current:[/bold blue] [green]{current['key']}[/green] {current['summary']}"
        )
        console.print(
            f"  [dim]Type: {current['type']} | Status: {current['status']} | Assignee: {current['assignee']}[/dim]"
        )

        # Show children (stories under epic) with their subtasks in tree format
        if hierarchy_data["children"]:
            console.print(
                f"\n[blue]↓ Children ({len(hierarchy_data['children'])}):[/blue]"
            )
            for idx, child in enumerate(hierarchy_data["children"]):
                is_last_child = idx == len(hierarchy_data["children"]) - 1
                tree_char = "└─" if is_last_child else "├─"

                console.print(f"  {tree_char} [green]{child['key']}[/green] {child['summary']}")
                console.print(
                    f"     [dim]Type: {child['type']} | Status: {child['status']} | Assignee: {child['assignee']}[/dim]"
                )

                # Show subtasks for this child
                if child.get("subtasks"):
                    continuation = "   " if is_last_child else "│  "
                    for sub_idx, subtask in enumerate(child["subtasks"]):
                        is_last_subtask = sub_idx == len(child["subtasks"]) - 1
                        sub_tree_char = "└─" if is_last_subtask else "├─"

                        console.print(
                            f"  {continuation} {sub_tree_char} [yellow]{subtask['key']}[/yellow] {subtask['summary']}"
                        )
                        console.print(
                            f"  {continuation}    [dim]Type: {subtask['type']} | Status: {subtask['status']} | Assignee: {subtask['assignee']}[/dim]"
                        )
        else:
            console.print("\n[dim]No children[/dim]")

        # Show direct subtasks (subtasks of current issue, not of children)
        if hierarchy_data["subtasks"]:
            console.print(
                f"\n[blue]↓ Subtasks ({len(hierarchy_data['subtasks'])}):[/blue]"
            )
            for idx, subtask in enumerate(hierarchy_data["subtasks"]):
                is_last = idx == len(hierarchy_data["subtasks"]) - 1
                tree_char = "└─" if is_last else "├─"

                console.print(f"  {tree_char} [yellow]{subtask['key']}[/yellow] {subtask['summary']}")
                console.print(
                    f"     [dim]Type: {subtask['type']} | Status: {subtask['status']} | Assignee: {subtask['assignee']}[/dim]"
                )

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


# Subtask enhancements


def edit_subtask_interactive(subtask_key: str):
    """Interactive edit function for subtasks."""
    try:
        print_info("Interactive subtask editing not yet fully implemented")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


def delete_subtask_interactive(subtask_key: str):
    """Interactive delete function for subtasks."""
    try:
        print_info("Interactive subtask deletion not yet fully implemented")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


# Story management functions


@app.command("watchers")
def list_watchers(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
):
    """List watchers for an issue."""
    try:
        client = JiraApiClient()
        watchers = client.get_watchers(issue_key)

        console.print(f"[bold blue]Watchers for {issue_key}:[/bold blue]")

        if watchers.get("watchers"):
            for watcher in watchers["watchers"]:
                display_name = watcher.get("displayName", "Unknown")
                account_id = watcher.get("accountId", "")
                email = watcher.get("emailAddress", "")
                console.print(f"  • {display_name} ({email}) - {account_id}")
        else:
            console.print("  No watchers found")

        console.print(f"\nTotal watchers: {watchers.get('watchCount', 0)}")

    except JiraCliError as e:
        print_error(f"Failed to get watchers: {e}")
        raise typer.Exit(1)


@app.command("watch")
def add_watcher(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    user_email: Optional[str] = typer.Option(
        None,
        "--user",
        "-u",
        help="User email to add as watcher (defaults to current user)",
    ),
):
    """Add a watcher to an issue."""
    try:
        client = JiraApiClient()

        account_id = None
        if user_email:
            users = client.search_users(user_email, max_results=1)
            if not users:
                print_error(f"User with email '{user_email}' not found")
                raise typer.Exit(1)
            account_id = users[0]["accountId"]

        client.add_watcher(issue_key, account_id)

        if user_email:
            print_success(f"Added {user_email} as watcher to {issue_key}")
        else:
            print_success(f"You are now watching {issue_key}")

    except JiraCliError as e:
        print_error(f"Failed to add watcher: {e}")
        raise typer.Exit(1)


@app.command("unwatch")
def remove_watcher(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    user_email: Optional[str] = typer.Option(
        None,
        "--user",
        "-u",
        help="User email to remove as watcher (defaults to current user)",
    ),
):
    """Remove a watcher from an issue."""
    try:
        client = JiraApiClient()

        account_id = None
        if user_email:
            users = client.search_users(user_email, max_results=1)
            if not users:
                print_error(f"User with email '{user_email}' not found")
                raise typer.Exit(1)
            account_id = users[0]["accountId"]

        client.remove_watcher(issue_key, account_id)

        if user_email:
            print_success(f"Removed {user_email} from watching {issue_key}")
        else:
            print_success(f"You are no longer watching {issue_key}")

    except JiraCliError as e:
        print_error(f"Failed to remove watcher: {e}")
        raise typer.Exit(1)


@app.command("create-story")
def create_story_command(
    epic_key: str = typer.Option(
        ..., "--epic", "-e", help="Epic key to create story under"
    ),
    summary: str = typer.Option(..., "--summary", "-s", help="Story summary"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Story description"
    ),
    description_file: Optional[str] = typer.Option(
        None, "--description-file", "-f", help="Read description from file"
    ),
    assignee: Optional[str] = typer.Option(
        None, "--assignee", "-a", help="Assignee email or account ID"
    ),
    due_date: Optional[str] = typer.Option(
        None, "--due-date", help="Due date in YYYY-MM-DD format"
    ),
    priority: Optional[str] = typer.Option(None, "--priority", help="Priority name"),
    labels: Optional[List[str]] = typer.Option(
        None, "--label", "-l", help="Labels to add"
    ),
    story_points: Optional[int] = typer.Option(
        None, "--story-points", help="Story points estimation"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Use interactive mode"
    ),
):
    """Create a new story under an epic."""
    if interactive:
        return create_story_interactive(epic_key, summary)

    try:
        client = JiraApiClient()

        # Read description from source
        final_description = read_description_from_source(description, description_file)

        # Get epic info to determine project
        epic = client.get_issue(epic_key, fields=["project"])
        project_key = epic["fields"]["project"]["key"]

        # Resolve assignee if email provided
        account_id = None
        if assignee:
            if "@" in assignee:  # Email format
                users = client.search_users(assignee, max_results=1)
                if not users:
                    print_error(f"User with email '{assignee}' not found")
                    raise typer.Exit(1)
                account_id = users[0]["accountId"]
            else:  # Assume account ID
                account_id = assignee

        story_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": "Story"},
                "parent": {"key": epic_key},
            }
        }

        if final_description:
            story_data["fields"]["description"] = markdown_to_adf(final_description)

        if account_id:
            story_data["fields"]["assignee"] = {"accountId": account_id}

        if due_date:
            story_data["fields"]["duedate"] = due_date

        if priority:
            story_data["fields"]["priority"] = {"name": priority}

        if labels:
            story_data["fields"]["labels"] = labels

        if story_points:
            # Note: The field name for story points varies by Jira setup
            # Common field names: "customfield_10002", "customfield_10016", etc.
            story_data["fields"][
                "customfield_10002"
            ] = story_points  # Default Jira Cloud story points field

        result = client.create_issue(story_data)

        story_key = result.get("key")
        print_success(f"Story created: {story_key} under epic {epic_key}")
        if final_description:
            print_info(
                f"Description: {final_description[:100]}{'...' if len(final_description) > 100 else ''}"
            )

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


def create_story_interactive(
    epic_key: str, summary: Optional[str] = None
):
    """Interactive story creation function."""
    try:
        client = JiraApiClient()

        # Get epic info to determine project
        epic = client.get_issue(epic_key, fields=["project"])
        project_key = epic["fields"]["project"]["key"]

        if not summary:
            summary = typer.prompt("Story summary")

        description = typer.prompt(
            "Story description (press Enter to skip)", default="", show_default=False
        )
        assignee = typer.prompt(
            "Assignee account ID (press Enter to skip)", default="", show_default=False
        )
        due_date = typer.prompt(
            "Due date (YYYY-MM-DD, press Enter to skip)", default="", show_default=False
        )

        story_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": "Story"},
                "parent": {"key": epic_key},
            }
        }

        if description.strip():
            story_data["fields"]["description"] = markdown_to_adf(description.strip())

        if assignee.strip():
            story_data["fields"]["assignee"] = {"accountId": assignee.strip()}

        if due_date.strip():
            story_data["fields"]["duedate"] = due_date.strip()

        result = client.create_issue(story_data)

        story_key = result.get("key")
        print_success(f"Story created: {story_key} under epic {epic_key}")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)
