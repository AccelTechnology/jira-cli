"""Attachment-related commands for Jira CLI."""

import os
import json
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path

from ..utils.api import JiraApiClient
from ..utils.formatting import print_json, print_error, print_success, print_info
from ..utils.error_handling import ErrorFormatter, handle_api_error
from ..utils.validation import validate_command
from ..exceptions import JiraCliError

console = Console()
app = typer.Typer(help="Manage issue attachments")


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def format_attachments_table(attachments: list) -> Table:
    """Format attachments data as a table."""
    table = Table(title="Attachments")
    table.add_column("ID", style="dim")
    table.add_column("Filename", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Author", style="blue")
    table.add_column("Created", style="white")
    
    for attachment in attachments:
        size = format_size(attachment.get('size', 0))
        author = attachment.get('author', {}).get('displayName', 'Unknown')
        created = attachment.get('created', '')
        
        # Format date
        if created:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                created = dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        table.add_row(
            attachment.get('id', ''),
            attachment.get('filename', ''),
            size,
            author,
            created
        )
    
    return table


@app.command("list")
def list_attachments(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    table: bool = typer.Option(False, "--table", help="Output as table")
):
    """List attachments for an issue."""
    try:
        client = JiraApiClient()
        issue = client.get_issue(issue_key, fields=['attachment'])
        
        attachments = issue.get('fields', {}).get('attachment', [])
        
        if json_output:
            print_json(attachments)
        elif table:
            attachments_table = format_attachments_table(attachments)
            console.print(attachments_table)
        else:
            console.print(f"[bold blue]Attachments for {issue_key}:[/bold blue]")
            
            if not attachments:
                console.print("  No attachments found")
                return
                
            total_size = 0
            for attachment in attachments:
                filename = attachment.get('filename', 'Unknown')
                size_bytes = attachment.get('size', 0)
                size = format_size(size_bytes)
                author = attachment.get('author', {}).get('displayName', 'Unknown')
                created = attachment.get('created', '')
                attachment_id = attachment.get('id', '')
                
                # Format date
                if created:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        created = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
                
                console.print(f"\n  [dim]ID:[/dim] {attachment_id}")
                console.print(f"  [cyan]Filename:[/cyan] {filename}")
                console.print(f"  [green]Size:[/green] {size}")
                console.print(f"  [blue]Author:[/blue] {author}")
                console.print(f"  [white]Created:[/white] {created}")
                
                total_size += size_bytes
            
            # Display total size
            if total_size > 0:
                console.print(f"\n[bold]Total size: {format_size(total_size)}[/bold]")
                
    except JiraCliError as e:
        print_error(f"Failed to get attachments: {e}")
        raise typer.Exit(1)


@app.command("upload")
@validate_command(issue_key_params=['issue_key'], command_context='attachments upload')
def upload_attachment(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    file_path: str = typer.Argument(..., help="Path to file to upload"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Upload an attachment to an issue."""
    if not os.path.exists(file_path):
        ErrorFormatter.print_formatted_error(
            "File Not Found",
            f"The specified file does not exist: {file_path}",
            expected="Path to an existing file",
            examples=[
                f"jira-cli attachments upload {issue_key} ./document.pdf",
                f"jira-cli attachments upload {issue_key} /path/to/screenshot.png",
                f"jira-cli attachments upload {issue_key} './My File.docx'"
            ],
            suggestions=[
                "Check the file path is correct",
                "Ensure the file exists in the specified location",
                "Use quotes around paths with spaces",
                "Use relative or absolute paths as needed",
                "Check file permissions if on Unix systems"
            ],
            command_context="attachments upload"
        )
        raise typer.Exit(1)
    
    try:
        client = JiraApiClient()
        
        file_size = os.path.getsize(file_path)
        print_info(f"Uploading {os.path.basename(file_path)} ({format_size(file_size)})...")
        
        result = client.upload_attachment(issue_key, file_path)
        
        if json_output:
            print_json(result)
        else:
            if result:
                attachment = result[0]
                filename = attachment.get('filename', 'Unknown')
                size = format_size(attachment.get('size', 0))
                print_success(f"Successfully uploaded {filename} ({size}) to {issue_key}")
            else:
                print_success(f"Successfully uploaded {os.path.basename(file_path)} to {issue_key}")
                
    except JiraCliError as e:
        print_error(f"Failed to upload attachment: {e}")
        raise typer.Exit(1)


@app.command("download")
def download_attachment(
    attachment_id: str = typer.Argument(..., help="Attachment ID to download"),
    output_path: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path (defaults to original filename)"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files")
):
    """Download an attachment."""
    try:
        client = JiraApiClient()
        
        # Get attachment metadata first
        attachment_meta = client.get_attachment(attachment_id)
        filename = attachment_meta.get('filename', f"attachment_{attachment_id}")
        
        # Determine output path
        if output_path:
            output_file = Path(output_path)
        else:
            output_file = Path(filename)
        
        # Check if file exists
        if output_file.exists() and not force:
            if not typer.confirm(f"File {output_file} already exists. Overwrite?"):
                print_info("Download cancelled")
                return
        
        print_info(f"Downloading {filename}...")
        
        # Download attachment content
        content = client.download_attachment(attachment_id)
        
        # Write to file
        with open(output_file, 'wb') as f:
            f.write(content)
        
        file_size = len(content)
        print_success(f"Downloaded {filename} ({format_size(file_size)}) to {output_file}")
                
    except JiraCliError as e:
        print_error(f"Failed to download attachment: {e}")
        raise typer.Exit(1)


@app.command("delete")
def delete_attachment(
    attachment_id: str = typer.Argument(..., help="Attachment ID to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")
):
    """Delete an attachment."""
    try:
        client = JiraApiClient()
        
        # Get attachment metadata for confirmation
        attachment_meta = client.get_attachment(attachment_id)
        filename = attachment_meta.get('filename', f"attachment_{attachment_id}")
        
        if not yes:
            confirm = typer.confirm(f"Delete attachment '{filename}' (ID: {attachment_id})?")
            if not confirm:
                print_info("Cancelled")
                return
        
        client.delete_attachment(attachment_id)
        print_success(f"Deleted attachment '{filename}' (ID: {attachment_id})")
                
    except JiraCliError as e:
        print_error(f"Failed to delete attachment: {e}")
        raise typer.Exit(1)


@app.command("info")
def get_attachment_info(
    attachment_id: str = typer.Argument(..., help="Attachment ID"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Get detailed information about an attachment."""
    try:
        client = JiraApiClient()
        attachment = client.get_attachment(attachment_id)
        
        if json_output:
            print_json(attachment)
        else:
            console.print(f"[bold blue]Attachment Details:[/bold blue]")
            
            filename = attachment.get('filename', 'Unknown')
            size = format_size(attachment.get('size', 0))
            author = attachment.get('author', {}).get('displayName', 'Unknown')
            created = attachment.get('created', '')
            mime_type = attachment.get('mimeType', 'Unknown')
            
            # Format date
            if created:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    created = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            console.print(f"  [dim]ID:[/dim] {attachment_id}")
            console.print(f"  [cyan]Filename:[/cyan] {filename}")
            console.print(f"  [green]Size:[/green] {size}")
            console.print(f"  [blue]Author:[/blue] {author}")
            console.print(f"  [white]Created:[/white] {created}")
            console.print(f"  [yellow]MIME Type:[/yellow] {mime_type}")
                
    except JiraCliError as e:
        print_error(f"Failed to get attachment info: {e}")
        raise typer.Exit(1)