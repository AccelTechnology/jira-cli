"""Markdown to Atlassian Document Format (ADF) converter."""

import re
from typing import Dict, List, Any, Optional
import mistune
from mistune import BaseRenderer


class ADFRenderer(BaseRenderer):
    """Custom mistune renderer that outputs ADF format instead of HTML."""

    def __init__(self):
        super().__init__()
        self.current_content = []

    def finalize_data(self) -> Dict[str, Any]:
        """Finalize and return ADF document structure."""
        return {
            "type": "doc",
            "version": 1,
            "content": (
                self.current_content
                if self.current_content
                else [{"type": "paragraph", "content": [{"type": "text", "text": ""}]}]
            ),
        }

    def render_token(self, token: Dict[str, Any], state: Any) -> Any:
        """Render a single token."""
        func = self._get_method(token["type"])
        return func(token, state)

    def render_tokens(self, tokens: List[Dict[str, Any]], state: Any) -> List[Any]:
        """Render a list of tokens."""
        results = []
        for token in tokens:
            result = self.render_token(token, state)
            if result is not None:
                if isinstance(result, list):
                    results.extend(result)
                else:
                    results.append(result)
        return results

    def render_children(self, token: Dict[str, Any], state: Any) -> List[Dict[str, Any]]:
        """Render children tokens and return as ADF content."""
        if "children" in token:
            return self.render_tokens(token["children"], state)
        return []

    def paragraph(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle paragraph elements."""
        content = self.render_children(token, state)
        adf_node = {"type": "paragraph", "content": content if content else [{"type": "text", "text": ""}]}
        self.current_content.append(adf_node)
        return adf_node

    def heading(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle heading elements (h1-h6)."""
        content = self.render_children(token, state)
        level = token.get("attrs", {}).get("level", 1)
        adf_node = {
            "type": "heading",
            "attrs": {"level": min(max(level, 1), 6)},
            "content": content if content else [{"type": "text", "text": ""}],
        }
        self.current_content.append(adf_node)
        return adf_node

    def text(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle plain text."""
        return {"type": "text", "text": token.get("raw", "")}

    def strong(self, token: Dict[str, Any], state: Any) -> List[Dict[str, Any]]:
        """Handle bold/strong text."""
        children = self.render_children(token, state)
        # Apply strong mark to all text children
        result = []
        for child in children:
            if child.get("type") == "text":
                marks = child.get("marks", [])
                marks.append({"type": "strong"})
                child["marks"] = marks
                result.append(child)
            else:
                result.append(child)
        return result

    def emphasis(self, token: Dict[str, Any], state: Any) -> List[Dict[str, Any]]:
        """Handle italic/emphasis text."""
        children = self.render_children(token, state)
        # Apply em mark to all text children
        result = []
        for child in children:
            if child.get("type") == "text":
                marks = child.get("marks", [])
                marks.append({"type": "em"})
                child["marks"] = marks
                result.append(child)
            else:
                result.append(child)
        return result

    def strikethrough(self, token: Dict[str, Any], state: Any) -> List[Dict[str, Any]]:
        """Handle strikethrough text."""
        children = self.render_children(token, state)
        # Apply strike mark to all text children
        result = []
        for child in children:
            if child.get("type") == "text":
                marks = child.get("marks", [])
                marks.append({"type": "strike"})
                child["marks"] = marks
                result.append(child)
            else:
                result.append(child)
        return result

    def codespan(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle inline code."""
        return {
            "type": "text",
            "text": token.get("raw", ""),
            "marks": [{"type": "code"}],
        }

    def link(self, token: Dict[str, Any], state: Any) -> List[Dict[str, Any]]:
        """Handle links."""
        children = self.render_children(token, state)
        url = token.get("attrs", {}).get("url", "")

        # Apply link mark to all text children
        result = []
        for child in children:
            if child.get("type") == "text":
                marks = child.get("marks", [])
                marks.append({"type": "link", "attrs": {"href": url}})
                child["marks"] = marks
                result.append(child)
            else:
                result.append(child)
        return result

    def block_code(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle code block elements."""
        attrs = {}
        info = token.get("attrs", {}).get("info")
        if info:
            attrs["language"] = info.strip()

        adf_node = {
            "type": "codeBlock",
            "attrs": attrs,
            "content": [{"type": "text", "text": token.get("raw", "")}],
        }
        self.current_content.append(adf_node)
        return adf_node

    def list(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle list elements (ul/ol)."""
        ordered = token.get("attrs", {}).get("ordered", False)
        children = token.get("children", [])

        # Check if this is a task list (has task_list_item children)
        is_task_list = any(child.get("type") == "task_list_item" for child in children)

        if is_task_list:
            # Convert task lists to regular bullet lists with [] / [x] syntax
            # Note: Jira Cloud may not support taskList in all configurations
            items = []
            for child in children:
                if child.get("type") == "task_list_item":
                    checked = child.get("attrs", {}).get("checked", False)
                    checkbox = "[x]" if checked else "[]"

                    # Render child content
                    child_content = []
                    for grandchild in child.get("children", []):
                        if grandchild.get("type") == "block_text":
                            inline_content = self.render_children(grandchild, state)
                            if inline_content:
                                child_content.extend(inline_content)

                    # Prepend checkbox to content
                    final_content = [{"type": "text", "text": f"{checkbox} "}]
                    final_content.extend(child_content)

                    items.append({
                        "type": "listItem",
                        "content": [{"type": "paragraph", "content": final_content}]
                    })

            if items:
                adf_node = {"type": "bulletList", "content": items}
                self.current_content.append(adf_node)
                return adf_node
        else:
            # Regular list
            list_type = "orderedList" if ordered else "bulletList"
            items = []
            for child in children:
                if child.get("type") == "list_item":
                    item_content = self.list_item(child, state)
                    if item_content:
                        items.append(item_content)

            if items:
                adf_node = {"type": list_type, "content": items}
                self.current_content.append(adf_node)
                return adf_node
        return None

    def list_item(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle list item elements."""
        # Render children (which could be paragraphs, nested lists, etc.)
        children = token.get("children", [])
        item_content = []

        for child in children:
            child_type = child.get("type")

            if child_type == "block_text":
                # Inline content directly in the list item
                inline_content = self.render_children(child, state)
                if inline_content:
                    item_content.append({"type": "paragraph", "content": inline_content})

            elif child_type == "paragraph":
                # Paragraph in list item
                para_content = self.render_children(child, state)
                if para_content:
                    item_content.append({"type": "paragraph", "content": para_content})

            elif child_type == "list":
                # Nested list
                nested_list = self.list(child, state)
                if nested_list:
                    item_content.append(nested_list)

        return {"type": "listItem", "content": item_content if item_content else [{"type": "paragraph", "content": [{"type": "text", "text": ""}]}]}

    def task_list_item(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle task list item elements (checkboxes)."""
        checked = token.get("attrs", {}).get("checked", False)
        children = token.get("children", [])
        item_content = []

        for child in children:
            child_type = child.get("type")

            if child_type == "block_text":
                # Inline content directly in the list item
                inline_content = self.render_children(child, state)
                if inline_content:
                    item_content.append({"type": "paragraph", "content": inline_content})

            elif child_type == "paragraph":
                # Paragraph in list item
                para_content = self.render_children(child, state)
                if para_content:
                    item_content.append({"type": "paragraph", "content": para_content})

        return {
            "type": "taskItem",
            "attrs": {"localId": f"task-{id(token)}", "state": "DONE" if checked else "TODO"},
            "content": item_content if item_content else [{"type": "paragraph", "content": [{"type": "text", "text": ""}]}]
        }

    def blockquote(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle blockquote elements."""
        children = token.get("children", [])
        content = []

        for child in children:
            # Store current_content temporarily
            temp_content = self.current_content
            self.current_content = []

            # Render child (usually paragraphs)
            self.render_token(child, state)

            # Get rendered content
            content.extend(self.current_content)

            # Restore current_content
            self.current_content = temp_content

        if content:
            adf_node = {"type": "blockquote", "content": content}
            self.current_content.append(adf_node)
            return adf_node
        return None

    def block_quote(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle blockquote elements (alternate naming)."""
        return self.blockquote(token, state)

    def thematic_break(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle horizontal rules."""
        adf_node = {"type": "rule"}
        self.current_content.append(adf_node)
        return adf_node

    def block_html(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle raw HTML blocks (convert to text)."""
        # Strip HTML tags and treat as plain text
        html = token.get("raw", "")
        text = re.sub(r"<[^>]+>", "", html)
        if text.strip():
            adf_node = {
                "type": "paragraph",
                "content": [{"type": "text", "text": text.strip()}],
            }
            self.current_content.append(adf_node)
            return adf_node
        return None

    def block_text(self, token: Dict[str, Any], state: Any) -> List[Dict[str, Any]]:
        """Handle block text (used in list items)."""
        return self.render_children(token, state)

    def linebreak(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle line breaks."""
        # ADF doesn't have explicit linebreak, use text with newline
        return {"type": "text", "text": "\n"}

    def softbreak(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle soft breaks."""
        # Treat as space
        return {"type": "text", "text": " "}

    def blank_line(self, token: Dict[str, Any], state: Any) -> None:
        """Handle blank lines (usually just separators)."""
        # Blank lines are just separators in markdown, don't render anything
        return None

    def table(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle table elements."""
        children = token.get("children", [])
        rows = []

        for child in children:
            child_type = child.get("type")
            if child_type == "table_head":
                # Process header row
                row = self.table_head(child, state)
                if row:
                    rows.append(row)
            elif child_type == "table_body":
                # Process body rows
                body_rows = self.table_body(child, state)
                rows.extend(body_rows)

        if rows:
            adf_node = {
                "type": "table",
                "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
                "content": rows
            }
            self.current_content.append(adf_node)
            return adf_node
        return None

    def table_head(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle table header row."""
        children = token.get("children", [])
        cells = []

        for child in children:
            if child.get("type") == "table_cell":
                cell_content = self.render_children(child, state)
                cells.append({
                    "type": "tableHeader",
                    "content": [{"type": "paragraph", "content": cell_content if cell_content else [{"type": "text", "text": ""}]}]
                })

        return {"type": "tableRow", "content": cells}

    def table_body(self, token: Dict[str, Any], state: Any) -> List[Dict[str, Any]]:
        """Handle table body rows."""
        children = token.get("children", [])
        rows = []

        for child in children:
            if child.get("type") == "table_row":
                row = self.table_row(child, state)
                if row:
                    rows.append(row)

        return rows

    def table_row(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle table row."""
        children = token.get("children", [])
        cells = []

        for child in children:
            if child.get("type") == "table_cell":
                cell_content = self.render_children(child, state)
                cells.append({
                    "type": "tableCell",
                    "content": [{"type": "paragraph", "content": cell_content if cell_content else [{"type": "text", "text": ""}]}]
                })

        return {"type": "tableRow", "content": cells}

    def table_cell(self, token: Dict[str, Any], state: Any) -> List[Dict[str, Any]]:
        """Handle table cell - just return rendered children."""
        return self.render_children(token, state)

    def image(self, token: Dict[str, Any], state: Any) -> Dict[str, Any]:
        """Handle image elements."""
        attrs = token.get("attrs", {})
        url = attrs.get("url", "")
        alt_text = attrs.get("alt", "")
        title = attrs.get("title", "")

        # ADF represents images as mediaSingle containing media nodes
        media_attrs = {
            "type": "external",
            "url": url
        }

        if alt_text:
            media_attrs["alt"] = alt_text

        # Return as inline content (will be wrapped in paragraph by parent)
        return {
            "type": "mediaSingle",
            "attrs": {"layout": "center"},
            "content": [
                {
                    "type": "media",
                    "attrs": media_attrs
                }
            ]
        }


def markdown_to_adf(markdown_text: str) -> Dict[str, Any]:
    """Convert markdown text to Atlassian Document Format (ADF).

    Args:
        markdown_text: Markdown formatted text

    Returns:
        ADF document structure

    Examples:
        >>> adf = markdown_to_adf("# Hello\\n\\nThis is **bold** text.")
        >>> print(adf['type'])
        doc
    """
    if not markdown_text or not markdown_text.strip():
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": ""}]}
            ],
        }

    # Create custom renderer
    renderer = ADFRenderer()

    # Create markdown parser with custom renderer and plugins
    # Enable plugins for extended markdown features
    markdown = mistune.create_markdown(
        renderer=renderer,
        plugins=['strikethrough', 'table', 'task_lists']
    )

    # Parse markdown (this will populate the renderer's content)
    markdown(markdown_text)

    # Get final ADF structure
    return renderer.finalize_data()


def text_to_adf(text: str, is_markdown: bool = True) -> Dict[str, Any]:
    """Convert text to ADF, with optional markdown parsing.

    Args:
        text: Input text (plain text or markdown)
        is_markdown: Whether to parse text as markdown

    Returns:
        ADF document structure
    """
    if is_markdown:
        return markdown_to_adf(text)
    else:
        # Plain text fallback
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"text": text, "type": "text"}]}
            ],
        }


# Convenience functions for specific use cases


def create_heading_adf(text: str, level: int = 1) -> Dict[str, Any]:
    """Create ADF heading node."""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "heading",
                "attrs": {"level": min(max(level, 1), 6)},
                "content": [{"type": "text", "text": text}],
            }
        ],
    }


def create_code_block_adf(code: str, language: Optional[str] = None) -> Dict[str, Any]:
    """Create ADF code block node."""
    attrs = {}
    if language:
        attrs["language"] = language

    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "codeBlock",
                "attrs": attrs,
                "content": [{"type": "text", "text": code}],
            }
        ],
    }


def create_list_adf(items: List[str], ordered: bool = False) -> Dict[str, Any]:
    """Create ADF list node."""
    list_items = []
    for item in items:
        list_items.append(
            {
                "type": "listItem",
                "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": item}]}
                ],
            }
        )

    list_type = "orderedList" if ordered else "bulletList"

    return {
        "type": "doc",
        "version": 1,
        "content": [{"type": list_type, "content": list_items}],
    }
