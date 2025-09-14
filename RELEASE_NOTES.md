# Release Notes - Jira CLI

## Version 2025.1.14 - Enhanced Subtask Management & Validation

### 🎯 Major Fixes

#### Subtask Creation Issues Resolved
**Fixed critical subtask creation failures** that were preventing users from creating subtasks in projects with non-standard issue type configurations.

- **Root Cause**: API client hardcoded `'Subtask'` issue type, failing in projects using `'Sub-task'` or other variations
- **Impact**: All `create-subtask` commands and subtask creation via `create --type Subtask` were failing
- **Resolution**: Complete overhaul of subtask type resolution with dynamic lookup and project-specific validation

### 🚀 New Features

#### Dynamic Issue Type Resolution
- **Smart Type Detection**: Automatically detects and uses correct subtask issue types for each project
- **Multiple Name Support**: Handles `'Subtask'`, `'Sub-task'`, `'Sub task'` variations seamlessly
- **ID-Based Reliability**: Uses issue type IDs instead of names for better API reliability
- **Transparent Feedback**: Shows which issue type is being used: `"Using subtask type: Sub-task (ID: 10035)"`

#### Project-Specific Issue Type Validation
- **Pre-Creation Validation**: Validates issue types against project configuration before API calls
- **Helpful Error Messages**: Shows available issue types when validation fails
- **Smart Suggestions**: Provides context-aware suggestions for subtask types
- **Example Output**:
  ```
  Error: Invalid Issue Type
  Issue type 'Subtask' is not available in project 'PD'.

  Available types: Story, Task, Bug, Sub-task, Epic
  Suggestions:
  • For subtasks, use: Sub-task
  • Check project configuration for issue type restrictions
  ```

#### Enhanced Project Commands
- **Project-Specific Issue Types**: `jira-cli projects issue-types --project PD`
- **Discovery Tool**: Easily find available issue types for any project
- **Fallback Support**: Shows global types when project-specific ones aren't available

### 🛠️ Improvements

#### Enhanced Error Handling
- **Comprehensive Validation**: Added `@validate_command` decorators to subtask commands
- **Better User Search**: Improved assignee resolution with detailed error messages
- **Parent Issue Validation**: Validates parent issue exists and is accessible
- **Graceful Degradation**: Falls back gracefully when validation cannot be performed

#### API Client Robustness
- **Dynamic Type Resolution**: `create_subtask()` method now resolves types dynamically
- **Multiple Fallback Levels**: Primary lookup → fallback name → final fallback
- **Error Recovery**: Continues operation even when type resolution partially fails

#### Command Consistency
- **Unified Error Patterns**: Consistent error formatting across all subtask operations
- **Enhanced Feedback**: Better progress indication and status messages
- **Improved Help**: More informative command descriptions and examples

### 🐛 Bug Fixes

#### Fixed Issues from JIRA_SUBTASK_ERROR.md
1. **✅ "issuetype: Specify a valid issue type"**: Now resolves correct project-specific issue types
2. **✅ ID Mismatch (10002 vs 10035)**: Uses actual project issue type IDs from API
3. **✅ Hardcoded Type Names**: Supports all project-specific subtask type variations
4. **✅ Poor Error Messages**: Comprehensive validation with examples and suggestions

#### Additional Fixes
- **Parent Issue Access**: Better validation and error messages for inaccessible parent issues
- **User Assignment**: Enhanced user search with email validation and helpful errors
- **Date Validation**: Improved due date format validation for subtasks
- **File Description**: Better handling of description files in subtask creation

### 📚 Usage Examples

#### Working Subtask Creation Commands
```bash
# Create subtask using dedicated command (now works!)
jira-cli issues create-subtask \
  --parent PD-10 \
  --summary "Implement Email Processor" \
  --description "Create the main entry point function" \
  --assignee "user@company.com" \
  --due-date "2025-02-15"

# Create subtask using main create command (now works!)
jira-cli issues create \
  --project PD \
  --type "Sub-task" \
  --summary "Database Schema Update" \
  --parent PD-10

# Discover available issue types for your project
jira-cli projects issue-types --project PD --table
```

#### Enhanced Error Messages
```bash
$ jira-cli issues create-subtask --parent INVALID-123 --summary "Test"

Error: Parent Issue Not Found
Could not retrieve parent issue 'INVALID-123'. Verify the issue key exists and you have permission to view it.

Received: Parent issue key: 'INVALID-123'
Expected: Valid issue key that exists and you can access

Examples:
  PD-123
  PD-456

Suggestions:
  • Verify the issue key is correct
  • Check that the issue exists in Jira
  • Ensure you have permission to view the parent issue
  • Use 'jira-cli issues get INVALID-123' to test access
```

### 🔧 Technical Improvements

#### Code Architecture
- **New Validation Module**: `validate_project_issue_type()` function for reusable validation
- **Enhanced API Client**: Improved `create_subtask()` method with dynamic resolution
- **Better Error Handling**: Centralized error formatting with context-aware messages
- **Decorator Pattern**: Consistent validation using `@validate_command` decorators

#### Testing & Reliability
- **Edge Case Handling**: Covers various project configurations and issue type setups
- **Graceful Failures**: Operations continue with warnings when validation cannot complete
- **Comprehensive Coverage**: Addresses all scenarios from the original bug report

### 🎉 User Impact

#### Before This Release
```bash
$ jira-cli issues create-subtask -p PD-10 -s "Test Subtask"
✗ issuetype: Specify a valid issue type
```

#### After This Release
```bash
$ jira-cli issues create-subtask -p PD-10 -s "Test Subtask"
ℹ Using subtask type: Sub-task (ID: 10035)
✅ Subtask created: PD-75 under parent PD-10
```

### 📋 Migration Notes

#### For Existing Users
- **No Breaking Changes**: All existing commands continue to work
- **Better Error Messages**: May see more detailed validation errors (this is good!)
- **New Discovery**: Use `jira-cli projects issue-types --project YOUR_PROJECT` to see available types

#### For Developers
- **Enhanced Validation**: New validation functions available for custom implementations
- **Improved Patterns**: Better error handling patterns to follow
- **API Changes**: `create_subtask()` method now handles type resolution automatically

### 🔍 Technical Details

#### Files Modified
- `src/jira_cli/utils/api.py`: Enhanced subtask creation with dynamic type resolution
- `src/jira_cli/commands/issues.py`: Improved create-subtask command with comprehensive validation
- `src/jira_cli/utils/validation.py`: Added project-specific issue type validation
- `src/jira_cli/commands/projects.py`: Enhanced issue-types command with project support

#### Validation Flow
1. **Input Validation**: Parameter format and requirement validation
2. **Parent Validation**: Verify parent issue exists and is accessible
3. **Type Resolution**: Dynamic lookup of project-specific issue types
4. **User Resolution**: Email-to-account-ID conversion with validation
5. **Creation**: API call with validated and resolved parameters

### 🎯 Next Steps

This release focuses on **reliability and user experience** for subtask operations. Future releases will continue to enhance:

- Workflow validation (checking valid transitions)
- Custom field support for project-specific requirements
- Bulk subtask operations
- Interactive subtask creation wizard

---

**Full Changelog**: All changes maintain backward compatibility while significantly improving reliability and user experience for subtask management operations.