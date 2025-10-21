# Markdown Support in Jira CLI

## Overview

The jira-cli now supports **full markdown formatting** when creating or updating Jira issues! No more manual copy-pasting through markdown viewers - just write your descriptions in markdown and they'll be automatically converted to Atlassian Document Format (ADF).

## What Was Fixed

Previously, the CLI was using a simple `text_to_adf()` function that treated all input as plain text. This has been completely rewritten to:

1. **Use proper markdown parsing** with the `mistune` library
2. **Convert markdown to ADF** using a custom token-based renderer
3. **Support all common markdown features** including formatting, lists, code blocks, and more

## Supported Markdown Features

### Text Formatting
- **Bold text**: `**bold**` or `__bold__`
- *Italic text*: `*italic*` or `_italic_`
- `Inline code`: `` `code` ``
- ~~Strikethrough~~: `~~strikethrough~~`
- Combined: `**bold and _italic_**`

### Headings
```markdown
# H1 Heading
## H2 Heading
### H3 Heading (up to H6)
```

### Lists

**Bullet lists:**
```markdown
- Item 1
- Item 2
  - Nested item
  - Another nested
```

**Ordered lists:**
```markdown
1. First item
2. Second item
   1. Nested numbered
3. Third item
```

**Task lists (checkboxes):**
```markdown
- [ ] Todo item
- [x] Completed item
- [ ] Another todo
```

### Code Blocks
````markdown
```javascript
function hello() {
  console.log("Hello, World!");
}
```
````

Supports syntax highlighting for: `javascript`, `python`, `java`, `bash`, `sql`, and many more!

### Tables
```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
```

### Links
```markdown
[Link text](https://example.com)
```

### Images
```markdown
![Alt text](https://example.com/image.png)
```

### Blockquotes
```markdown
> This is a blockquote
> It can span multiple lines
```

### Horizontal Rules
```markdown
---
```

## Usage Examples

### Creating an Issue with Markdown

**From command line:**
```bash
jira-cli issues create \
  --project PROJ \
  --summary "Implement new feature" \
  --description "## Overview

This feature adds **real-time** updates using WebSocket.

### Implementation
- Setup WebSocket server
- Create client library
- Add authentication

See [docs](https://example.com) for details."
```

**From file:**
```bash
# Create a markdown file
cat > feature.md << 'EOF'
# User Authentication Feature

## Description
Implement **secure** user authentication with:
- Email/password login
- OAuth integration
- Two-factor authentication

## Technical Details
```python
def authenticate_user(email, password):
    # Validate credentials
    return user_session
```
EOF

# Use it in the CLI
jira-cli issues create \
  --project PROJ \
  --summary "User Authentication" \
  --description-file feature.md
```

### Updating Issue Description

```bash
jira-cli issues update PROJ-123 \
  --description "## Updated Requirements

- Added OAuth support
- Implemented **2FA**
- Updated security policies

> **Note**: All changes are backward compatible."
```

## Example: Complex Markdown

Here's a full example showing all supported features:

```markdown
# Epic: API Redesign

## Overview
Complete redesign of our REST API with **improved performance** and *better documentation*.
~~Old API will be deprecated.~~

## Implementation Checklist

- [x] Design phase completed
- [x] Architecture approved
- [ ] Implementation in progress
- [ ] Testing pending
- [ ] Documentation pending

## Key Features

1. RESTful endpoints
2. GraphQL support
3. Real-time subscriptions via WebSocket

### Authentication
- JWT tokens
- OAuth 2.0
- API keys

## Code Examples

```javascript
// New API client
const client = new APIClient({
  baseURL: 'https://api.example.com',
  auth: { token: 'your-jwt-token' }
});

const data = await client.get('/users');
```

## Team Assignments

| Team Member | Role       | Component   | Status      |
|-------------|------------|-------------|-------------|
| Alice       | Backend    | API Core    | In Progress |
| Bob         | Frontend   | SDK         | Not Started |
| Carol       | DevOps     | Deployment  | Completed   |

## Architecture

![API Architecture](https://example.com/api-architecture.png)

## Important Notes

> **Breaking Change**: This version introduces breaking changes.
> Please review the [migration guide](https://docs.example.com/migrate).

---

**Priority**: High
**Estimate**: 2 weeks
```

This markdown will be properly converted to ADF and displayed beautifully in Jira with:
- Formatted headings
- **Bold** and *italic* text
- ~~Strikethrough~~ for deleted content
- ✅ Interactive checkboxes for tasks
- Tables with proper formatting
- Syntax-highlighted code blocks
- Embedded images
- Links and blockquotes

## Technical Details

### How It Works

1. **Markdown Parsing**: Uses `mistune` v3 to parse markdown into an AST (Abstract Syntax Tree)
2. **Token Rendering**: Custom `ADFRenderer` walks the AST and converts each token to ADF format
3. **Mark Application**: Formatting (bold, italic, code, links) is applied as "marks" on text nodes
4. **Structure Preservation**: Lists, headings, code blocks maintain their hierarchy

### Converter Location

The markdown to ADF converter is implemented in:
```
src/jira_cli/utils/markdown_to_adf.py
```

### Testing

Run the markdown converter tests:
```bash
# Run test script
python test_markdown.py

# Run pytest
pytest test_markdown.py -v
```

## Troubleshooting

### Description Not Formatted

If your markdown isn't being formatted:
1. Ensure you're using the latest version of jira-cli
2. Check that the markdown syntax is valid
3. Try testing with the `test_markdown.py` script first

### Special Characters

If you need to use markdown syntax literally (e.g., asterisks for multiplication):
- Use backticks for inline code: `` `x * y` ``
- Use code blocks for longer examples

## Migration from Old Versions

If you were previously using plain text descriptions, they'll continue to work. The converter gracefully handles both markdown and plain text.

**Old way (still works):**
```bash
jira-cli issues create --project PROJ --summary "Title" --description "Plain text"
```

**New way (recommended):**
```bash
jira-cli issues create --project PROJ --summary "Title" --description "**Formatted** text"
```

## Benefits

✅ **No more manual formatting** in Jira's editor
✅ **Write in your favorite editor** with markdown support
✅ **Version control** your issue descriptions in Git
✅ **Consistent formatting** across all issues
✅ **Fast creation** from templates

Enjoy your new markdown powers! 🎉
