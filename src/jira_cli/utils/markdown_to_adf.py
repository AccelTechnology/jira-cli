"""Markdown to Atlassian Document Format (ADF) converter."""

import re
from typing import Dict, List, Any, Optional, Union
import mistune
from mistune import HTMLRenderer


class ADFRenderer(HTMLRenderer):
    """Custom mistune renderer that outputs ADF format instead of HTML."""

    def __init__(self):
        super().__init__()
        self.content_stack = []
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

    def paragraph(self, text: str) -> str:
        """Handle paragraph elements."""
        content = self._parse_inline_content(text)
        if content:  # Only add non-empty paragraphs
            self.current_content.append({"type": "paragraph", "content": content})
        return ""

    def heading(self, text: str, level: int) -> str:
        """Handle heading elements (h1-h6)."""
        content = self._parse_inline_content(text)
        self.current_content.append(
            {
                "type": "heading",
                "attrs": {"level": min(level, 6)},  # ADF supports levels 1-6
                "content": content,
            }
        )
        return ""

    def list(self, text: str, ordered: bool = False, **attrs) -> str:
        """Handle list elements (ul/ol)."""
        # Parse list items from text
        items = self._parse_list_items(text)
        if items:
            list_type = "orderedList" if ordered else "bulletList"
            self.current_content.append({"type": list_type, "content": items})
        return ""

    def list_item(self, text: str) -> str:
        """Handle list item elements."""
        content = self._parse_inline_content(text)
        return {
            "type": "listItem",
            "content": [{"type": "paragraph", "content": content}],
        }

    def blockquote(self, text: str) -> str:
        """Handle blockquote elements."""
        # Parse content inside blockquote
        content = []
        paragraphs = text.strip().split("\n\n")
        for para in paragraphs:
            if para.strip():
                inline_content = self._parse_inline_content(para.strip())
                content.append({"type": "paragraph", "content": inline_content})

        self.current_content.append({"type": "blockquote", "content": content})
        return ""

    def block_code(self, code: str, lang: Optional[str] = None) -> str:
        """Handle code block elements."""
        attrs = {}
        if lang:
            attrs["language"] = lang

        self.current_content.append(
            {
                "type": "codeBlock",
                "attrs": attrs,
                "content": [{"type": "text", "text": code}],
            }
        )
        return ""

    def block_html(self, html: str) -> str:
        """Handle raw HTML blocks (convert to text)."""
        # Strip HTML tags and treat as plain text
        text = re.sub(r"<[^>]+>", "", html)
        if text.strip():
            self.current_content.append(
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text.strip()}],
                }
            )
        return ""

    def thematic_break(self) -> str:
        """Handle horizontal rules."""
        self.current_content.append({"type": "rule"})
        return ""

    def table(self, text: str) -> str:
        """Handle table elements."""
        # Parse table structure from text
        rows = self._parse_table_rows(text)
        if rows:
            self.current_content.append(
                {
                    "type": "table",
                    "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
                    "content": rows,
                }
            )
        return ""

    def _parse_inline_content(self, text: str) -> List[Dict[str, Any]]:
        """Parse inline markdown content (bold, italic, code, links)."""
        if not text:
            return []

        content = []
        current_pos = 0

        # Patterns for inline markdown
        patterns = [
            (r"\*\*(.*?)\*\*", "strong"),  # Bold
            (r"\*(.*?)\*", "em"),  # Italic
            (r"`([^`]+)`", "code"),  # Inline code
            (r"\[([^\]]+)\]\(([^)]+)\)", "link"),  # Links
        ]

        # Find all matches
        matches = []
        for pattern, mark_type in patterns:
            for match in re.finditer(pattern, text):
                matches.append((match.start(), match.end(), match, mark_type))

        # Sort matches by position
        matches.sort(key=lambda x: x[0])

        # Process text with matches
        for start, end, match, mark_type in matches:
            # Add text before match
            if start > current_pos:
                content.append({"type": "text", "text": text[current_pos:start]})

            # Add formatted text
            if mark_type == "link":
                content.append(
                    {
                        "type": "text",
                        "text": match.group(1),
                        "marks": [{"type": "link", "attrs": {"href": match.group(2)}}],
                    }
                )
            elif mark_type == "code":
                content.append(
                    {
                        "type": "text",
                        "text": match.group(1),
                        "marks": [{"type": "code"}],
                    }
                )
            else:  # strong, em
                content.append(
                    {
                        "type": "text",
                        "text": match.group(1),
                        "marks": [{"type": mark_type}],
                    }
                )

            current_pos = end

        # Add remaining text
        if current_pos < len(text):
            content.append({"type": "text", "text": text[current_pos:]})

        # If no formatting found, return simple text
        if not content:
            content.append({"type": "text", "text": text})

        return content

    def _parse_list_items(self, text: str) -> List[Dict[str, Any]]:
        """Parse list items from HTML-like text."""
        items = []
        # This is a simplified parser - in practice, mistune would call list_item for each item
        lines = text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line:
                content = self._parse_inline_content(line)
                items.append(
                    {
                        "type": "listItem",
                        "content": [{"type": "paragraph", "content": content}],
                    }
                )
        return items

    def _parse_table_rows(self, text: str) -> List[Dict[str, Any]]:
        """Parse table rows from text."""
        # This is a simplified implementation
        # In practice, you'd need a more sophisticated table parser
        rows = []
        lines = text.strip().split("\n")

        for line in lines:
            if "|" in line:
                cells = [cell.strip() for cell in line.split("|") if cell.strip()]
                if cells:
                    row_content = []
                    for cell in cells:
                        cell_content = self._parse_inline_content(cell)
                        row_content.append(
                            {
                                "type": "tableCell",
                                "content": [
                                    {"type": "paragraph", "content": cell_content}
                                ],
                            }
                        )

                    rows.append({"type": "tableRow", "content": row_content})

        return rows


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

    # Create markdown parser with custom renderer
    markdown = mistune.create_markdown(renderer=renderer)

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
