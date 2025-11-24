"""Attachment-related commands for Jira CLI."""

import os
import json
from typing import Optional
import typer
from pathlib import Path

from ..utils.api import JiraApiClient
from ..utils.formatting import print_error, print_success, print_info
from ..utils.error_handling import ErrorFormatter, handle_api_error
from ..utils.validation import validate_command
from ..exceptions import JiraCliError

app = typer.Typer(help="Manage issue attachments", pretty_exceptions_enable=False, rich_markup_mode=None)


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


def format_attachments_table(attachments: list) -> str:
    """Format attachments data as plain text."""
    if not attachments:
        return "No attachments found."

    lines = []
    for attachment in attachments:
        size = format_size(attachment.get("size", 0))
        author = attachment.get("author", {}).get("displayName", "Unknown")
        created = attachment.get("created", "")

        # Format date
        if created:
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                created = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass

        lines.append(f"{attachment.get('id', '')}\t{attachment.get('filename', '')}\t{size}\t{author}\t{created}")

    return "\n".join(lines)


def format_attachment_detail(attachment: dict) -> str:
    """Format attachment details as plain text."""
    from datetime import datetime

    attachment_id = attachment.get("id", "Unknown")
    filename = attachment.get("filename", "Unknown")
    size = format_size(attachment.get("size", 0))
    author = attachment.get("author", {}).get("displayName", "Unknown")
    created = attachment.get("created", "")
    mime_type = attachment.get("mimeType", "Unknown")

    # Format date
    if created:
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            created = dt.strftime("%Y-%m-%d %H:%M")
        except:
            pass

    return f"""Filename: {filename}
ID: {attachment_id}
Size: {size}
MIME Type: {mime_type}
Author: {author}
Created: {created}"""


@app.command("list")
def list_attachments(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
):
    """List attachments for an issue."""
    try:
        client = JiraApiClient()
        issue = client.get_issue(issue_key, fields=["attachment"])

        attachments = issue.get("fields", {}).get("attachment", [])

        print(f"Attachments for {issue_key}:")

        if not attachments:
            print_info("No attachments found")
            return

        total_size = 0
        for attachment in attachments:
            filename = attachment.get("filename", "Unknown")
            size_bytes = attachment.get("size", 0)
            size = format_size(size_bytes)
            author = attachment.get("author", {}).get("displayName", "Unknown")
            created = attachment.get("created", "")
            attachment_id = attachment.get("id", "")

            # Format date
            if created:
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    created = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass

            print(f"\n  ID: {attachment_id}")
            print(f"  Filename: {filename}")
            print(f"  Size: {size}")
            print(f"  Author: {author}")
            print(f"  Created: {created}")

            total_size += size_bytes

        # Display total size
        if total_size > 0:
            print(f"\nTotal size: {format_size(total_size)}")

    except JiraCliError as e:
        print_error(f"Failed to get attachments: {e}")
        raise typer.Exit(1)


@app.command("upload")
@validate_command(issue_key_params=["issue_key"], command_context="attachments upload")
def upload_attachment(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    file_path: str = typer.Argument(..., help="Path to file to upload"),
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
                f"jira-cli attachments upload {issue_key} './My File.docx'",
            ],
            suggestions=[
                "Check the file path is correct",
                "Ensure the file exists in the specified location",
                "Use quotes around paths with spaces",
                "Use relative or absolute paths as needed",
                "Check file permissions if on Unix systems",
            ],
            command_context="attachments upload",
        )
        raise typer.Exit(1)

    try:
        client = JiraApiClient()

        file_size = os.path.getsize(file_path)
        print_info(
            f"Uploading {os.path.basename(file_path)} ({format_size(file_size)})..."
        )

        result = client.upload_attachment(issue_key, file_path)

        if result:
            attachment = result[0]
            filename = attachment.get("filename", "Unknown")
            size = format_size(attachment.get("size", 0))
            print_success(
                f"Successfully uploaded {filename} ({size}) to {issue_key}"
            )
        else:
            print_success(
                f"Successfully uploaded {os.path.basename(file_path)} to {issue_key}"
            )

    except JiraCliError as e:
        print_error(f"Failed to upload attachment: {e}")
        raise typer.Exit(1)


@app.command("download")
def download_attachment(
    attachment_id: str = typer.Argument(..., help="Attachment ID to download"),
    output_path: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path (defaults to original filename)"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
):
    """Download an attachment."""
    try:
        client = JiraApiClient()

        # Get attachment metadata first
        attachment_meta = client.get_attachment(attachment_id)
        filename = attachment_meta.get("filename", f"attachment_{attachment_id}")

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
        with open(output_file, "wb") as f:
            f.write(content)

        file_size = len(content)
        print_success(
            f"Downloaded {filename} ({format_size(file_size)}) to {output_file}"
        )

    except JiraCliError as e:
        print_error(f"Failed to download attachment: {e}")
        raise typer.Exit(1)


@app.command("delete")
def delete_attachment(
    attachment_id: str = typer.Argument(..., help="Attachment ID to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete an attachment."""
    try:
        client = JiraApiClient()

        # Get attachment metadata for confirmation
        attachment_meta = client.get_attachment(attachment_id)
        filename = attachment_meta.get("filename", f"attachment_{attachment_id}")

        if not yes:
            confirm = typer.confirm(
                f"Delete attachment '{filename}' (ID: {attachment_id})?"
            )
            if not confirm:
                print_info("Cancelled")
                return

        client.delete_attachment(attachment_id)
        print_success(f"Deleted attachment '{filename}' (ID: {attachment_id})")

    except JiraCliError as e:
        print_error(f"Failed to delete attachment: {e}")
        raise typer.Exit(1)


@app.command("delete-all")
def delete_all_attachments(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    pattern: Optional[str] = typer.Option(None, "--pattern", "-p", help="Only delete attachments matching this pattern"),
):
    """Delete all attachments from an issue."""
    try:
        client = JiraApiClient()

        # Get all attachments for the issue
        issue = client.get_issue(issue_key, fields=["attachment"])
        attachments = issue.get("fields", {}).get("attachment", [])

        if not attachments:
            print_info(f"No attachments found on {issue_key}")
            return

        # Filter by pattern if provided
        if pattern:
            import re
            filtered = [a for a in attachments if re.search(pattern, a.get("filename", ""))]
            if not filtered:
                print_info(f"No attachments matching pattern '{pattern}' found on {issue_key}")
                return
            attachments = filtered
            print_info(f"Found {len(attachments)} attachment(s) matching pattern '{pattern}'")
        else:
            print_info(f"Found {len(attachments)} attachment(s) on {issue_key}")

        # Show what will be deleted
        print("\nAttachments to delete:")
        for att in attachments:
            filename = att.get("filename", "Unknown")
            size = format_size(att.get("size", 0))
            print(f"  {filename} ({size})")

        if not yes:
            if not typer.confirm(f"\nDelete {len(attachments)} attachment(s)?"):
                print_info("Cancelled")
                return

        # Delete attachments
        deleted = 0
        failed = 0
        for att in attachments:
            try:
                attachment_id = att.get("id")
                filename = att.get("filename", "Unknown")
                client.delete_attachment(attachment_id)
                print(f"  Deleted: {filename}")
                deleted += 1
            except Exception as e:
                print(f"  Failed: {filename} - {e}")
                failed += 1

        print_success(f"Deleted {deleted} attachment(s)")
        if failed > 0:
            print_error(f"Failed to delete {failed} attachment(s)")

    except JiraCliError as e:
        print_error(f"Failed to delete attachments: {e}")
        raise typer.Exit(1)


@app.command("delete-duplicates")
def delete_duplicate_attachments(
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    keep: str = typer.Option("latest", "--keep", help="Which to keep: 'latest' or 'oldest'"),
):
    """Delete duplicate attachments from an issue (same filename)."""
    try:
        client = JiraApiClient()

        # Get all attachments for the issue
        issue = client.get_issue(issue_key, fields=["attachment"])
        attachments = issue.get("fields", {}).get("attachment", [])

        if not attachments:
            print_info(f"No attachments found on {issue_key}")
            return

        # Group by filename
        from collections import defaultdict
        from datetime import datetime

        filename_groups = defaultdict(list)
        for att in attachments:
            filename = att.get("filename", "")
            filename_groups[filename].append(att)

        # Find duplicates
        duplicates = {k: v for k, v in filename_groups.items() if len(v) > 1}

        if not duplicates:
            print_info(f"No duplicate attachments found on {issue_key}")
            return

        print_info(f"Found {len(duplicates)} file(s) with duplicates:")

        to_delete = []
        for filename, atts in duplicates.items():
            print(f"\n{filename} ({len(atts)} copies)")

            # Sort by created date
            sorted_atts = sorted(atts, key=lambda a: a.get("created", ""))

            # Determine which to keep
            if keep == "latest":
                keep_att = sorted_atts[-1]
                delete_atts = sorted_atts[:-1]
            else:  # oldest
                keep_att = sorted_atts[0]
                delete_atts = sorted_atts[1:]

            print(f"  Keep: {keep_att.get('created', 'Unknown')} (ID: {keep_att.get('id')})")
            for att in delete_atts:
                print(f"  Delete: {att.get('created', 'Unknown')} (ID: {att.get('id')})")
                to_delete.append(att)

        if not yes:
            if not typer.confirm(f"\nDelete {len(to_delete)} duplicate attachment(s)?"):
                print_info("Cancelled")
                return

        # Delete duplicates
        deleted = 0
        failed = 0
        for att in to_delete:
            try:
                attachment_id = att.get("id")
                filename = att.get("filename", "Unknown")
                client.delete_attachment(attachment_id)
                print(f"  Deleted: {filename} ({att.get('created', 'Unknown')})")
                deleted += 1
            except Exception as e:
                print(f"  Failed: {filename} - {e}")
                failed += 1

        print_success(f"Deleted {deleted} duplicate attachment(s)")
        if failed > 0:
            print_error(f"Failed to delete {failed} attachment(s)")

    except JiraCliError as e:
        print_error(f"Failed to delete duplicates: {e}")
        raise typer.Exit(1)


@app.command("info")
def get_attachment_info(
    attachment_id: str = typer.Argument(..., help="Attachment ID"),
):
    """Get detailed information about an attachment."""
    try:
        client = JiraApiClient()
        attachment = client.get_attachment(attachment_id)

        attachment_detail = format_attachment_detail(attachment)
        print(attachment_detail)

    except JiraCliError as e:
        print_error(f"Failed to get attachment info: {e}")
        raise typer.Exit(1)
