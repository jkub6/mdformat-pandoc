"""Obsidian callout blockquote support.

Obsidian callouts use a special blockquote syntax::

    > [!type]+ Optional Title
    > Body content here.

The first line (``[!type]`` with optional fold indicator and title) is
semantically a **header** that must remain on its own line. Without
special handling, mdformat's word-wrapping joins the header with the
body content, breaking the callout syntax.

This module provides a custom blockquote renderer that detects callout
headers and preserves the line break between the header and body.
"""

from __future__ import annotations

import re
import textwrap
from typing import TYPE_CHECKING

from mdformat.renderer._context import make_render_children

if TYPE_CHECKING:
    from mdformat.renderer import RenderContext, RenderTreeNode

# Matches the callout header pattern at the start of inline content.
# Examples: [!info], [!warning]+, [!danger]- Title Text
_CALLOUT_RE = re.compile(r"^\[![\w-]+\][+-]?(?:\s.*)?$")


def _is_callout_blockquote(node: RenderTreeNode) -> bool:
    """Check if a blockquote node contains an Obsidian callout."""
    if not node.children:
        return False
    first_child = node.children[0]
    if first_child.type != "paragraph" or not first_child.children:
        return False
    inline_node = first_child.children[0]
    if inline_node.type != "inline":
        return False

    # Check if the first text child matches a callout pattern
    for child in inline_node.children:
        if child.type == "text":
            return bool(_CALLOUT_RE.match(child.content))
        break  # First child must be the callout text
    return False


def _get_callout_header(inline_node: RenderTreeNode) -> str:
    """Extract the callout header text from the first text child."""
    for child in inline_node.children:
        if child.type == "text":
            return child.content
        break
    return ""


def _quote_lines(lines: list[str], marker: str) -> list[str]:
    """Prefix each line with the blockquote marker."""
    return [f"{marker}{line}" if line else ">" for line in lines]


def render_blockquote(node: RenderTreeNode, context: RenderContext) -> str:
    """Render a blockquote, with special handling for Obsidian callouts.

    For standard blockquotes, delegates to the default rendering.
    For callout blockquotes, ensures the ``[!type]`` header stays on
    its own line by rendering header and body separately.
    """
    if _is_callout_blockquote(node):
        return _render_callout(node, context)
    return _render_standard_blockquote(node, context)


def _render_standard_blockquote(node: RenderTreeNode, context: RenderContext) -> str:
    """Render a standard blockquote (identical to mdformat default)."""
    marker = "> "
    with context.indented(len(marker)):
        text = make_render_children(separator="\n\n")(node, context)
        lines = text.splitlines()
        if not lines:
            return ">"
        return "\n".join(_quote_lines(lines, marker))


def _render_callout_body(
    body_children: list[RenderTreeNode],
    context: RenderContext,
    marker: str,
) -> list[str]:
    """Render callout body children into quoted lines."""
    body_text = "".join(child.render(context) for child in body_children).strip()
    if not body_text:
        return []

    # Replace WRAP_POINT chars (\x00) that the text renderer injects
    body_text = body_text.replace("\x00", " ")

    if context.do_wrap:
        wrap_width = context.options["mdformat"]["wrap"]
        if isinstance(wrap_width, int):
            wrap_width -= len(marker) + context.env["indent_width"]
            wrap_width = max(1, wrap_width)
            body_text = textwrap.fill(
                body_text,
                width=wrap_width,
                break_long_words=False,
                break_on_hyphens=False,
            )

    return [f"{marker}{line}" for line in body_text.splitlines()]


def _render_callout(node: RenderTreeNode, context: RenderContext) -> str:
    """Render an Obsidian callout blockquote.

    The callout header line is rendered verbatim (no wrapping), and
    the body content goes through wrapping independently.
    """
    marker = "> "
    first_para = node.children[0]
    inline_node = first_para.children[0]
    header = _get_callout_header(inline_node)

    # Split inline children at the first softbreak
    body_children: list[RenderTreeNode] = []
    found_break = False
    for child in inline_node.children:
        if not found_break:
            if child.type == "softbreak":
                found_break = True
            continue
        body_children.append(child)

    result_lines = [f"{marker}{header}"]
    result_lines.extend(_render_callout_body(body_children, context, marker))

    # Render remaining children (paragraphs after the first)
    remaining = node.children[1:]
    if remaining:
        with context.indented(len(marker)):
            for child in remaining:
                rendered = child.render(context)
                if rendered:
                    result_lines.append(">")  # blank line separator
                    result_lines.extend(_quote_lines(rendered.splitlines(), marker))

    return "\n".join(result_lines)
