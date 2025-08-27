#!/usr/bin/env python3
"""Test script to validate enhanced error handling in Jira CLI."""

import subprocess
import sys
import os
from typing import List, Tuple

def run_command(command: List[str]) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

def test_error_scenario(description: str, command: List[str], expected_keywords: List[str] = None):
    """Test an error scenario and validate the error message."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")
    
    exit_code, stdout, stderr = run_command(command)
    output = stdout + stderr
    
    print(f"Exit code: {exit_code}")
    if output.strip():
        print(f"Output:\n{output}")
    else:
        print("No output captured")
    
    # Check for expected keywords in output
    if expected_keywords:
        found_keywords = []
        missing_keywords = []
        for keyword in expected_keywords:
            if keyword.lower() in output.lower():
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        if found_keywords:
            print(f"✓ Found expected keywords: {', '.join(found_keywords)}")
        if missing_keywords:
            print(f"✗ Missing expected keywords: {', '.join(missing_keywords)}")
    
    return exit_code != 0  # Return True if command failed as expected

def main():
    """Run comprehensive error handling tests."""
    print("Jira CLI Enhanced Error Handling Test Suite")
    print("=" * 60)
    
    # Set up test environment - unset credentials to test config errors
    original_env = {}
    for var in ['JIRA_URL', 'JIRA_EMAIL', 'JIRA_API_TOKEN']:
        original_env[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]
    
    test_scenarios = [
        # Configuration errors
        (
            "Missing configuration",
            ["python", "-m", "jira_cli.main", "config"],
            ["Configuration issues found", "JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"]
        ),
        (
            "Configuration setup help",
            ["python", "-m", "jira_cli.main", "config", "--setup-help"],
            ["Configuration Setup", "environment variables", "API token"]
        ),
        
        # Invalid issue key formats
        (
            "Invalid issue key format - no hyphen",
            ["python", "-m", "jira_cli.main", "issues", "get", "PROJ123"],
            ["Invalid Issue Key Format", "PROJECT-NUMBER", "hyphen", "Example usage"]
        ),
        (
            "Invalid issue key format - lowercase",
            ["python", "-m", "jira_cli.main", "issues", "get", "proj-123"],
            ["Invalid Issue Key Format", "uppercase", "PROJECT-NUMBER"]
        ),
        (
            "Empty issue key",
            ["python", "-m", "jira_cli.main", "issues", "get", ""],
            ["Missing Required Parameter", "Issue key is required"]
        ),
        
        # Invalid project key formats
        (
            "Invalid project key format - lowercase",
            ["python", "-m", "jira_cli.main", "issues", "create", "--project", "proj", "--summary", "Test"],
            ["Invalid Project Key Format", "uppercase", "Example"]
        ),
        (
            "Invalid project key format - special chars",
            ["python", "-m", "jira_cli.main", "issues", "create", "--project", "PROJ-123", "--summary", "Test"],
            ["Invalid Project Key Format", "letters and numbers", "Remove spaces, hyphens"]
        ),
        
        # JQL validation
        (
            "Empty JQL query",
            ["python", "-m", "jira_cli.main", "search", ""],
            ["Invalid JQL Query", "too short", "field, operator, and value"]
        ),
        (
            "Very short JQL query",
            ["python", "-m", "jira_cli.main", "search", "a"],
            ["Invalid JQL Query", "too short", "Complete JQL query"]
        ),
        
        # Missing required fields
        (
            "Missing summary for issue creation",
            ["python", "-m", "jira_cli.main", "issues", "create", "--project", "PROJ"],
            ["Missing Required Parameter", "summary", "required"]
        ),
        
        # Invalid dates
        (
            "Invalid date format",
            ["python", "-m", "jira_cli.main", "issues", "create", "--project", "PROJ", "--summary", "Test", "--due-date", "12/31/2024"],
            ["Invalid Date Format", "YYYY-MM-DD", "Use hyphens"]
        ),
        (
            "Invalid date value",
            ["python", "-m", "jira_cli.main", "issues", "create", "--project", "PROJ", "--summary", "Test", "--due-date", "2024-13-45"],
            ["Invalid Date Value", "valid calendar date"]
        ),
        
        # Invalid time formats for worklogs
        (
            "Invalid time format",
            ["python", "-m", "jira_cli.main", "worklog", "add", "PROJ-123", "invalid_time"],
            ["Invalid Time Format", "d/h/m units", "1h 30m"]
        ),
        (
            "Missing time for worklog",
            ["python", "-m", "jira_cli.main", "worklog", "add", "PROJ-123", ""],
            ["Time spent is required", "Jira time format"]
        ),
        
        # Invalid datetime formats
        (
            "Invalid datetime format for worklog",
            ["python", "-m", "jira_cli.main", "worklog", "add", "PROJ-123", "2h", "--started", "2024/12/31 09:00"],
            ["Invalid DateTime Format", "YYYY-MM-DD HH:MM", "4-digit year"]
        ),
        
        # Missing required action parameters
        (
            "Epic action without epic key",
            ["python", "-m", "jira_cli.main", "epics", "--action", "edit"],
            ["Missing Required Parameter", "requires --epic parameter", "Example usage"]
        ),
        (
            "Invalid epic action",
            ["python", "-m", "jira_cli.main", "epics", "--action", "invalid"],
            ["Invalid Parameter Value", "create, edit, delete"]
        ),
        
        # File not found for attachments
        (
            "File not found for upload",
            ["python", "-m", "jira_cli.main", "attachments", "upload", "PROJ-123", "/nonexistent/file.txt"],
            ["File Not Found", "does not exist", "Check the file path"]
        ),
        
        # No fields to update
        (
            "No fields specified for issue update",
            ["python", "-m", "jira_cli.main", "issues", "update", "PROJ-123"],
            ["No Fields to Update", "at least one field", "Use --summary"]
        ),
        (
            "No fields specified for worklog update",
            ["python", "-m", "jira_cli.main", "worklog", "update", "PROJ-123", "12345"],
            ["No Fields to Update", "at least one field", "Use --time"]
        ),
        
        # Invalid email format
        (
            "Invalid email format",
            ["python", "-m", "jira_cli.main", "bulk-assign", "PROJ-123", "--assignee", "invalid-email"],
            ["Invalid Email Format", "@", "user@company.com"]
        ),
        
        # Bulk operations with invalid issue keys
        (
            "Bulk watch with invalid issue key",
            ["python", "-m", "jira_cli.main", "bulk-watch", "proj-123,PROJ-456"],
            ["Invalid Issue Key Format", "uppercase", "PROJECT-NUMBER"]
        ),
    ]
    
    # Restore environment for some tests that need valid config
    for var, value in original_env.items():
        if value is not None:
            os.environ[var] = value
    
    # Run tests
    passed = 0
    failed = 0
    
    for description, command, expected_keywords in test_scenarios:
        try:
            success = test_error_scenario(description, command, expected_keywords)
            if success:
                passed += 1
                print("✅ PASSED")
            else:
                failed += 1
                print("❌ FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ ERROR: {e}")
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print(f"\n❌ Some tests failed. Check the output above for details.")
        return 1
    else:
        print(f"\n✅ All tests passed! Error handling is working correctly.")
        return 0

if __name__ == "__main__":
    sys.exit(main())