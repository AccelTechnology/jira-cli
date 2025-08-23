"""Project-related commands for Jira CLI."""

import json
from typing import Optional
import typer
from rich.console import Console

from ..utils.api import JiraApiClient
from ..utils.formatting import (
    print_json, print_error, print_success,
    format_project_table, format_issue_types_table
)
from ..exceptions import JiraCliError

console = Console()
app = typer.Typer(help="Manage Jira projects")


@app.command("list")
def list_projects(
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    table: bool = typer.Option(False, "--table", help="Output as table")
):
    """List all projects."""
    try:
        client = JiraApiClient()
        projects = client.get_projects()
        
        if json_output:
            print_json(projects)
        elif table:
            projects_table = format_project_table(projects)
            console.print(projects_table)
        else:
            print_json(projects)
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("get")
def get_project(
    project_key: str = typer.Argument(..., help="Project key"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Get project details."""
    try:
        client = JiraApiClient()
        project = client.get(f'project/{project_key}')
        
        if json_output:
            print_json(project)
        else:
            print_json(project)
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("issue-types")
def list_issue_types(
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    table: bool = typer.Option(False, "--table", help="Output as table")
):
    """List all issue types."""
    try:
        client = JiraApiClient()
        issue_types = client.get_issue_types()
        
        if json_output:
            print_json(issue_types)
        elif table:
            types_table = format_issue_types_table(issue_types)
            console.print(types_table)
        else:
            print_json(issue_types)
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("versions")
def list_versions(
    project_key: str = typer.Argument(..., help="Project key"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """List project versions."""
    try:
        client = JiraApiClient()
        versions = client.get(f'project/{project_key}/version')
        
        if json_output:
            print_json(versions)
        else:
            print_json(versions)
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("components")
def list_components(
    project_key: str = typer.Argument(..., help="Project key"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """List project components."""
    try:
        client = JiraApiClient()
        components = client.get(f'project/{project_key}/component')
        
        if json_output:
            print_json(components)
        else:
            print_json(components)
            
    except JiraCliError as e:
        print_error(str(e))
        raise typer.Exit(1)