# Jira CLI Agent Guide for Claude Code

This guide helps Claude Code users effectively use the `jira-cli` tool for Jira operations.

## Quick Reference

### Environment Variables Required

```bash
JIRA_EMAIL="your.email@example.com"
JIRA_API_TOKEN="your_api_token"
JIRA_URL="https://your-domain.atlassian.net"  # Optional
```

### Test Connection

```bash
jira-cli auth test
jira-cli auth whoami
```

## Common Operations

### 1. Search & View Issues

```bash
# Search with JQL
jira-cli search "project = PROJ AND assignee = currentUser()" --table

# Get specific issue
jira-cli issues get PROJ-123 --detail

# View in JSON for detailed inspection
jira-cli issues get PROJ-123 --json
```

### 2. Create Issues

#### Basic Creation

```bash
jira-cli issues create \
  --project PROJ \
  --summary "Issue title" \
  --type Story \
  --description "Simple description"
```

#### Create with Markdown File

```bash
# Step 1: Create markdown file
cat > feature.md << 'EOF'
# Feature: User Authentication

## Overview
Implement secure user authentication system.

## Tasks
- [] Design database schema
- [] Implement API endpoints
- [] Create UI components

## Technical Details
| Component | Technology |
|-----------|------------|
| Backend   | Node.js    |
| Frontend  | React      |

```javascript
// Example endpoint
app.post('/auth', (req, res) => {
  // Implementation
});
```

> **Note**: Use HTTPS for all endpoints
EOF

# Step 2: Create issue from file
jira-cli issues create \
  --project PROJ \
  --summary "Implement User Authentication" \
  --type Story \
  --description-file feature.md
```

### 3. Update Issues

#### Update Description from File

```bash
# Create updated markdown
cat > update.md << 'EOF'
# Updated Requirements

## Changes
- [x] Database schema completed
- [] API implementation in progress

## New Requirements
- Add OAuth support
- Implement 2FA

See [documentation](https://docs.example.com)
EOF

# Update issue
jira-cli issues update PROJ-123 --description-file update.md
```

#### Update Fields

```bash
# Update multiple fields
jira-cli issues update PROJ-123 \
  --summary "New title" \
  --priority "High" \
  --due-date "2025-12-31"
```

### 4. Comments

#### Add Comments

```bash
# Simple comment
jira-cli issues comment PROJ-123 "Status update: work in progress"

# Markdown comment
jira-cli issues comment PROJ-123 "## Progress Update

- [x] Phase 1 completed
- [] Phase 2 in progress

**Blockers**: None"

# Comment with mentions
jira-cli issues comment PROJ-123 "@john.doe@company.com please review this"
```

#### Fetch Comments

```bash
# List all comments on an issue (displays as formatted panels)
jira-cli issues comments PROJ-123

# Show newest comments first
jira-cli issues comments PROJ-123 --order-by=-created

# Limit results and use pagination
jira-cli issues comments PROJ-123 --max-results 10 --start-at 0

# View next page
jira-cli issues comments PROJ-123 --max-results 10 --start-at 10
```

**Features:**
- Rich formatted panels with author name and email
- Markdown content rendered beautifully (code blocks, lists, formatting)
- Created/Updated timestamps
- Automatic pagination with helpful info
- Sort by oldest first (default) or newest first (`--order-by=-created`)

### 5. Epic Management

```bash
# Create epic
jira-cli issues create \
  --project PROJ \
  --summary "Epic: User Management" \
  --type Epic \
  --description-file epic.md

# Create story under epic
jira-cli issues create \
  --project PROJ \
  --summary "User Login" \
  --type Story \
  --epic PROJ-1

# List stories in epic
jira-cli issues epic-stories PROJ-1 --table
```

### 6. Subtask Management

```bash
# Create subtask
jira-cli issues create-subtask \
  --parent PROJ-123 \
  --summary "Implement validation logic" \
  --description-file subtask.md

# List subtasks
jira-cli subtasks PROJ-123 --table
```

## Markdown Features

### Supported Syntax

When creating markdown files for Jira descriptions:

```markdown
# Headings (H1-H6)
## Subheading
### Sub-subheading

**Bold text**
*Italic text*
~~Strikethrough~~
`Inline code`

- Bullet list item 1
- Bullet list item 2
  - Nested item

1. Numbered list
2. Another item

- [] Todo item
- [x] Completed item

| Column 1 | Column 2 |
|----------|----------|
| Data A   | Data B   |

```python
# Code block with syntax highlighting
def example():
    return "Hello"
```

> Blockquote text

[Link text](https://example.com)

![Image alt](https://example.com/image.png)

---
Horizontal rule
```

### Example: Complete Issue Description

```markdown
# User Story

**As a** system administrator,
**I want** automated backup functionality,
**So that** data is protected against loss.

---

## Acceptance Criteria

### Backup System
- [] Automated daily backups
- [] Retention policy (30 days)
- [] Backup verification

### Monitoring
- [] Alert on backup failure
- [] Dashboard showing backup status

---

## Technical Implementation

### Architecture
| Component | Technology |
|-----------|------------|
| Storage   | AWS S3     |
| Scheduler | Cron       |
| Alerts    | Email/Slack|

### Code Example

```python
def create_backup():
    """Create daily database backup."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backup_{timestamp}.sql"

    # Create backup
    os.system(f"pg_dump mydb > {backup_file}")

    # Upload to S3
    s3.upload_file(backup_file, 'backups-bucket', backup_file)
```

---

## Resources

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [PostgreSQL Backup Guide](https://www.postgresql.org/docs/current/backup.html)

---

**Priority**: High
**Estimate**: 3 days
```

## Best Practices for Claude Code Users

### 1. Always Use Markdown Files for Complex Descriptions

```bash
# Instead of inline descriptions:
# ❌ jira-cli issues create --description "Very long text..."

# Use files:
# ✅
cat > description.md << 'EOF'
# Complex content here
EOF
jira-cli issues create --description-file description.md
```

### 2. Leverage Tables for Structured Data

```markdown
## Requirements Matrix

| Requirement | Priority | Status | Owner |
|-------------|----------|--------|-------|
| Auth System | High     | Done   | Alice |
| Dashboard   | Medium   | Progress | Bob |
| Reports     | Low      | Todo   | Carol |
```

### 3. Use Task Lists for Tracking

```markdown
## Implementation Checklist

### Backend
- [x] Database schema
- [x] API endpoints
- [] Testing

### Frontend
- [] UI components
- [] Integration
- [] Testing
```

### 4. Include Code Examples

````markdown
## API Integration

```bash
# Installation
npm install @auth/sdk

# Usage
const auth = require('@auth/sdk');
auth.login(credentials);
```
````

### 5. Link Related Resources

```markdown
## Documentation

- [Architecture Diagram](https://wiki.company.com/arch)
- [API Specification](https://api.company.com/docs)
- [Design Mockups](https://figma.com/file/xyz)
```

## Workflow Examples

### Example 1: Create Feature Epic with Stories

```bash
# 1. Create epic description
cat > epic-auth.md << 'EOF'
# Epic: Authentication System

## Overview
Comprehensive authentication and authorization system.

## Features
- Multi-factor authentication
- Social login (Google, GitHub)
- Role-based access control

## Success Criteria
- [] All auth methods working
- [] Security audit passed
- [] Documentation complete
EOF

# 2. Create epic
EPIC_KEY=$(jira-cli issues create \
  --project PROJ \
  --summary "Epic: Authentication System" \
  --type Epic \
  --description-file epic-auth.md \
  --json | jq -r '.key')

echo "Created epic: $EPIC_KEY"

# 3. Create stories under epic
jira-cli issues create \
  --project PROJ \
  --summary "Implement JWT Authentication" \
  --type Story \
  --epic $EPIC_KEY \
  --description "## Story
JWT-based authentication implementation

## Tasks
- [] Generate tokens
- [] Validate tokens
- [] Refresh mechanism"

jira-cli issues create \
  --project PROJ \
  --summary "Add Social Login" \
  --type Story \
  --epic $EPIC_KEY \
  --description "## Story
Google and GitHub OAuth integration

## Tasks
- [] Google OAuth setup
- [] GitHub OAuth setup
- [] User profile mapping"
```

### Example 2: Update Issue with Progress

```bash
# 1. Get current issue
jira-cli issues get PROJ-123 --json > current.json

# 2. Create progress update
cat > progress.md << 'EOF'
# Implementation Progress

## Completed
- [x] Database schema design
- [x] API endpoint implementation
- [x] Unit tests

## In Progress
- [] Integration testing
- [] Documentation

## Blockers
None currently

## Next Steps
1. Complete integration tests
2. Deploy to staging
3. QA review

## Metrics
| Metric | Value |
|--------|-------|
| Code Coverage | 85% |
| Test Cases | 47 |
| Bugs Fixed | 12 |
EOF

# 3. Update issue
jira-cli issues update PROJ-123 --description-file progress.md

# 4. Add comment
jira-cli issues comment PROJ-123 "Updated progress - 75% complete"

# 5. Review all comments to see discussion history
jira-cli issues comments PROJ-123 --order-by=-created
```

### Example 2b: Review Issue Discussion

```bash
# View all comments to understand context
jira-cli issues comments PROJ-123

# Check recent comments only
jira-cli issues comments PROJ-123 --order-by=-created --max-results 5

# Add your comment to the discussion
jira-cli issues comment PROJ-123 "@team.lead@company.com Ready for review. See latest test results in comment above."
```

### Example 3: Create Technical Specification

```bash
cat > spec.md << 'EOF'
# Technical Specification: API Gateway

## Architecture

### Components
| Component | Technology | Purpose |
|-----------|------------|---------|
| Gateway   | Kong       | Routing |
| Auth      | JWT        | Security |
| Cache     | Redis      | Performance |

### Flow Diagram
![Architecture](https://wiki.company.com/images/api-gateway.png)

## Endpoints

### Authentication
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secret"
}
```

### User Management
```http
GET /api/v1/users/:id
Authorization: Bearer <token>
```

## Implementation Tasks

### Phase 1: Infrastructure
- [] Kong setup
- [] SSL certificates
- [] Rate limiting config

### Phase 2: Integration
- [] Auth service integration
- [] Cache layer
- [] Monitoring

## Security Considerations

> **Critical**: All endpoints must use HTTPS
> **Important**: Implement rate limiting (100 req/min)

## References
- [Kong Documentation](https://docs.konghq.com)
- [JWT Best Practices](https://jwt.io/introduction)
EOF

jira-cli issues create \
  --project PROJ \
  --summary "Implement API Gateway" \
  --type Story \
  --description-file spec.md \
  --priority High
```

## Tips for AI Agents (Claude Code)

### 1. Check Issue Before Updating

```bash
# Always get current state first
jira-cli issues get PROJ-123 --detail

# Review discussion history for context
jira-cli issues comments PROJ-123
```

### 2. Use JSON Output for Parsing

```bash
# Get machine-readable output
jira-cli issues get PROJ-123 --json | jq '.fields.summary'
```

### 3. Search for Context

```bash
# Find related issues
jira-cli search "project = PROJ AND summary ~ 'authentication'" --table

# Check recent comments to understand current discussion
jira-cli issues comments PROJ-123 --order-by=-created --max-results 5
```

### 4. Validate Environment

```bash
# Before operations, verify connection
jira-cli auth test || echo "Check JIRA_EMAIL and JIRA_API_TOKEN"
```

### 5. Create Atomic Updates

```bash
# One logical change per update
jira-cli issues update PROJ-123 --description-file new-description.md
# Separate comment for discussion
jira-cli issues comment PROJ-123 "Updated requirements based on team feedback"
```

## Troubleshooting

### Connection Issues

```bash
# Test connection
jira-cli auth test

# Check environment
echo $JIRA_EMAIL
echo $JIRA_URL

# Verify credentials
jira-cli auth whoami --json
```

### Markdown Not Rendering

```bash
# Verify file exists and is readable
cat description.md

# Check file encoding (should be UTF-8)
file description.md

# Test with simple markdown first
echo "# Test\n\n**Bold** text" > test.md
jira-cli issues update PROJ-123 --description-file test.md
```

### Finding Issue Keys

```bash
# Search by summary
jira-cli search "summary ~ 'keyword'" --table

# Your assigned issues
jira-cli my-issues --project PROJ --table

# Recent issues
jira-cli search "project = PROJ ORDER BY created DESC" --table --max-results 10
```

## Quick Command Reference

| Task | Command |
|------|---------|
| **Create issue** | `jira-cli issues create --project PROJ --summary "Title" --type Story --description-file desc.md` |
| **Update issue** | `jira-cli issues update PROJ-123 --description-file update.md` |
| **Add comment** | `jira-cli issues comment PROJ-123 "Message"` |
| **List comments** | `jira-cli issues comments PROJ-123` |
| **Get issue** | `jira-cli issues get PROJ-123 --detail` |
| **Search issues** | `jira-cli search "JQL query" --table` |
| **Create epic** | `jira-cli issues create --project PROJ --summary "Epic" --type Epic --description-file epic.md` |
| **Create story** | `jira-cli issues create --project PROJ --summary "Story" --type Story --epic PROJ-1` |
| **Create subtask** | `jira-cli issues create-subtask --parent PROJ-123 --summary "Task" --description-file task.md` |
| **List my issues** | `jira-cli my-issues --project PROJ --table` |
| **List epics** | `jira-cli epics --project PROJ --table` |
| **List subtasks** | `jira-cli subtasks PROJ-123 --table` |

## Additional Resources

- **Full Documentation**: See `MARKDOWN_SUPPORT.md` for comprehensive markdown guide
- **CLI Help**: Run `jira-cli --help` or `jira-cli <command> --help`
- **Repository**: https://github.com/AccelTechnology/jira-cli
- **Jira REST API**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/

---

**Note**: This guide is optimized for Claude Code and AI agents. For human users, refer to the main README.md.
