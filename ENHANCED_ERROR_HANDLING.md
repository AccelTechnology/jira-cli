# Enhanced Error Handling Implementation - Jira CLI

## Overview

This document outlines the comprehensive error handling enhancements implemented in the Jira CLI to improve user experience through clear, actionable error messages and helpful examples.

## Key Improvements

### 1. Enhanced Error Message Formatting

**New Features:**
- Clear error type identification
- Detailed description of what went wrong
- Shows what was received vs. what was expected
- Provides multiple relevant examples
- Offers actionable suggestions for resolution
- Includes command context for getting more help

**Example Output:**
```
Error: Invalid Issue Key Format
Issue key must follow the format PROJECT-NUMBER.

Received: 'invalid-key'
Expected: Format: PROJECT-NUMBER (e.g., PROJ-123)

Example usage:
  PROJ-123
  MYPROJECT-456
  DEV-789

Suggestions:
  • Ensure project key contains only uppercase letters and numbers
  • Use a hyphen to separate project key from issue number
  • Issue number should contain only digits

Run 'jira-cli issues get --help' for more information.
```

### 2. Comprehensive Input Validation

**Validation Types Implemented:**
- **Issue Key Validation**: Format `PROJECT-NUMBER` with uppercase letters/numbers
- **Project Key Validation**: Uppercase letters and numbers only, starting with letter
- **Email Validation**: Standard email format validation
- **Date Validation**: `YYYY-MM-DD` format with actual date validation
- **Time Validation**: Jira time format (`1h`, `30m`, `2d`, `1h 30m`)
- **DateTime Validation**: `YYYY-MM-DD HH:MM` format
- **JQL Query Validation**: Basic JQL query structure validation
- **File Path Validation**: File existence checking
- **Required Parameter Validation**: Missing parameter detection
- **Choice Parameter Validation**: Valid option enforcement

### 3. Validation Decorators

**Decorator System:**
- `@validate_issue_key()` - Validates issue key parameters
- `@validate_project_key()` - Validates project key parameters  
- `@validate_email()` - Validates email parameters
- `@validate_date()` - Validates date parameters
- `@validate_time_spent()` - Validates time parameters
- `@validate_jql()` - Validates JQL query parameters
- `@validate_required()` - Validates required parameters
- `@validate_choice()` - Validates choice parameters
- `@validate_command()` - Combined validation for multiple parameter types
- `@handle_errors()` - Consistent error handling wrapper

**Example Usage:**
```python
@app.command("get")
@validate_command(issue_key_params=['issue_key'], command_context='issues get')
def get_issue(issue_key: str, ...):
    """Get issue by key."""
```

### 4. Configuration Validation and Setup Help

**Configuration Features:**
- Automatic validation of required environment variables
- Clear identification of configuration issues
- Setup help command with step-by-step instructions
- API token generation guidance

**New Commands:**
```bash
jira-cli config --setup-help  # Show detailed setup instructions
jira-cli config              # Show current config with validation status
```

### 5. Enhanced API Error Handling

**Improved Error Responses:**
- Authentication errors with credential guidance
- Permission errors with access suggestions  
- Resource not found errors with verification tips
- Connection errors with troubleshooting steps
- Generic API errors with helpful context

### 6. Command-Specific Improvements

#### Issues Commands
- **Create**: Required field validation, project key validation, date format validation
- **Update**: Better "no fields to update" message with examples
- **Search**: JQL query validation with helpful suggestions
- **Get**: Issue key format validation

#### Worklog Commands  
- **Add**: Time format validation, datetime format validation
- **Update**: Required field validation with specific examples
- **List**: Issue key validation

#### Attachments Commands
- **Upload**: File existence validation with path suggestions
- **Download**: Better error messages for missing files

#### Main Commands
- **Search**: JQL validation with query examples
- **Bulk Operations**: Issue key validation for comma-separated lists
- **Epic Management**: Action validation and parameter requirements
- **Subtask Management**: Parent/child key validation

## Files Created/Modified

### New Files Created:
1. **`src/jira_cli/utils/error_handling.py`** - Core error handling utilities
2. **`src/jira_cli/utils/validation.py`** - Validation decorators and functions
3. **`test_error_handling.py`** - Comprehensive test suite for error scenarios
4. **`ENHANCED_ERROR_HANDLING.md`** - This documentation

### Modified Files:
1. **`src/jira_cli/main.py`** - Enhanced main commands with validation
2. **`src/jira_cli/commands/issues.py`** - Issues commands with validation
3. **`src/jira_cli/commands/worklog.py`** - Worklog commands with validation  
4. **`src/jira_cli/commands/attachments.py`** - Attachment commands with validation

## Error Handling Patterns

### 1. Input Validation Pattern
```python
from ..utils.validation import validate_command

@app.command("example")
@validate_command(
    issue_key_params=['issue_key'],
    project_key_params=['project_key'], 
    date_params=['due_date'],
    required_params=['summary'],
    command_context='example'
)
def example_command(issue_key, project_key, due_date, summary):
    # Command implementation
```

### 2. Custom Error Handling Pattern
```python
from ..utils.error_handling import ErrorFormatter

if not required_condition:
    ErrorFormatter.print_formatted_error(
        "Error Type",
        "Clear description of the problem",
        received="What user provided",
        expected="What should be provided",
        examples=["example 1", "example 2"],
        suggestions=["suggestion 1", "suggestion 2"],
        command_context="command name"
    )
    raise typer.Exit(1)
```

### 3. API Error Handling Pattern
```python
from ..utils.error_handling import handle_api_error

try:
    # API operation
    result = client.some_operation()
except Exception as e:
    handle_api_error(e, 'command context')
    raise typer.Exit(1)
```

## Testing Results

### Test Scenarios Covered:
- ✅ Configuration validation and setup help
- ✅ Invalid issue key formats (various patterns)
- ✅ Invalid project key formats  
- ✅ Empty and invalid JQL queries
- ✅ Missing required parameters
- ✅ Invalid date formats and values
- ✅ Invalid time formats for worklogs
- ✅ Invalid datetime formats
- ✅ Missing action parameters
- ✅ File not found errors
- ✅ No fields to update scenarios
- ✅ Invalid email formats
- ✅ Bulk operation validation

### Sample Test Output:
```bash
# Invalid issue key
$ jira-cli issues get invalid-key
Error: Invalid Issue Key Format
Issue key must follow the format PROJECT-NUMBER.
[... detailed error message with examples and suggestions ...]

# Invalid time format  
$ jira-cli worklog add PROJ-123 "invalid_time"
Error: Invalid Time Format
Time must be in Jira time format using d (days), h (hours), m (minutes).
[... detailed error message with examples and suggestions ...]

# Configuration help
$ jira-cli config --setup-help
[... comprehensive setup instructions with examples ...]
```

## Benefits

### For Users:
- **Clear Understanding**: Users immediately understand what went wrong
- **Quick Resolution**: Examples and suggestions help users fix issues quickly  
- **Learning Tool**: Error messages teach proper CLI usage
- **Less Frustration**: No more cryptic error messages

### For Developers:
- **Consistent Patterns**: Reusable validation decorators
- **Easy Maintenance**: Centralized error handling logic
- **Better Debugging**: Clear error contexts and command information
- **Extensible**: Easy to add new validation types

### For Support:
- **Reduced Support Tickets**: Users can self-resolve common issues
- **Better Bug Reports**: Clear error contexts help diagnose issues
- **Training Material**: Error messages serve as usage examples

## Future Enhancements

### Potential Improvements:
1. **Interactive Correction**: Suggest corrections for typos in commands
2. **Context-Aware Help**: Show relevant help based on error context
3. **Usage Analytics**: Track common errors to improve UX
4. **Localization**: Multi-language error messages
5. **Configuration Wizard**: Interactive setup for first-time users

### Additional Validation:
1. **Custom Field Validation**: Project-specific field validation
2. **Workflow State Validation**: Valid transition checking
3. **Permission Validation**: Pre-flight permission checks
4. **Rate Limit Handling**: Graceful handling of API rate limits

## Conclusion

The enhanced error handling system transforms the Jira CLI from a tool with cryptic error messages into a user-friendly interface that guides users toward successful operations. The comprehensive validation system catches errors early, provides clear explanations, and offers actionable solutions, significantly improving the overall user experience.

The modular design using decorators makes it easy to apply consistent validation across all commands while maintaining clean, readable code. The centralized error formatting ensures consistent messaging and makes it simple to enhance error handling further in the future.