"""Project-related commands for Jira CLI."""

import json
from typing import Optional
import typer
from rich.console import Console

from ..utils.api import JiraApiClient
from ..utils.formatting import (
    print_json,
    print_error,
    print_success,
    print_info,
    format_project_table,
    format_project_detail,
    format_issue_types_table,
    format_versions_table,
    format_components_table,
)
from ..exceptions import JiraCliError

console = Console()
app = typer.Typer(help="Manage Jira projects")


@app.command("list")
def list_projects(
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """List all projects."""
    try:
        client = JiraApiClient()
        projects = client.get_projects()

        if json_output:
            print_json(projects)
        else:
            projects_table = format_project_table(projects)
            console.print(projects_table)

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("get")
def get_project(
    project_key: str = typer.Argument(..., help="Project key"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """Get project details."""
    try:
        client = JiraApiClient()
        project = client.get(f"project/{project_key}")

        if json_output:
            print_json(project)
        else:
            project_panel = format_project_detail(project)
            console.print(project_panel)

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("issue-types")
def list_issue_types(
    project_key: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Project key (optional - shows project-specific types)",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """List issue types. Optionally specify a project to see project-specific types."""
    try:
        client = JiraApiClient()

        if project_key:
            # Get project-specific issue types
            try:
                project = client.get_project(project_key)
                issue_types = project.get("issueTypes", [])
                if not issue_types:
                    # Fallback to global types if project doesn't have specific ones
                    issue_types = client.get_issue_types()
                    print_success(
                        f"No project-specific issue types found for {project_key}. Showing global types."
                    )
                else:
                    print_success(f"Issue types available in project {project_key}:")
            except Exception as e:
                print_error(
                    f"Could not get project-specific issue types for {project_key}: {e}"
                )
                print_success("Showing global issue types instead:")
                issue_types = client.get_issue_types()
        else:
            # Get global issue types
            issue_types = client.get_issue_types()
            print_success(
                "Global issue types (use --project to see project-specific types):"
            )

        if json_output:
            print_json(issue_types)
        else:
            types_table = format_issue_types_table(issue_types)
            console.print(types_table)

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("versions")
def list_versions(
    project_key: str = typer.Argument(..., help="Project key"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """List project versions."""
    try:
        client = JiraApiClient()
        result = client.get(f"project/{project_key}/version")

        if json_output:
            print_json(result)
        else:
            versions = result.get("values", [])
            if versions:
                versions_table = format_versions_table(versions)
                console.print(versions_table)
            else:
                print_info(f"No versions found for project {project_key}")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("components")
def list_components(
    project_key: str = typer.Argument(..., help="Project key"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """List project components."""
    try:
        client = JiraApiClient()
        result = client.get(f"project/{project_key}/component")

        if json_output:
            print_json(result)
        else:
            components = result.get("values", [])
            if components:
                components_table = format_components_table(components)
                console.print(components_table)
            else:
                print_info(f"No components found for project {project_key}")

    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)
