from __future__ import annotations

import re
import textwrap
from typing import TYPE_CHECKING

from markdown_it import MarkdownIt
from markdown_it.rules_block import StateBlock

if TYPE_CHECKING:
    from mdformat.renderer import RenderContext, RenderTreeNode

# Match {::LABEL} spaces
LABEL_RE = re.compile(r"^\{::(?P<label>[^}]+)\}(?P<spaces>[ \t]+)")


def custom_label_rule(state: StateBlock, start_line: int, end_line: int, silent: bool) -> bool:
    """Block rule for custom label lists {::LABEL} content."""
    pos = state.bMarks[start_line] + state.tShift[start_line]
    max_pos = state.eMarks[start_line]
    line_text = state.src[pos:max_pos]

    match = LABEL_RE.match(line_text)
    if not match:
        return False

    if silent:
        return True

    # Start a list
    state.push("custom_label_list_open", "div", 1)

    current_line = start_line
    while current_line < end_line:
        pos = state.bMarks[current_line] + state.tShift[current_line]
        max_pos = state.eMarks[current_line]
        line_text = state.src[pos:max_pos]

        match = LABEL_RE.match(line_text)
        if not match:
            break

        label = match.group("label")
        spaces_len = len(match.group("spaces"))
        content_start = match.end()

        item_token = state.push("custom_label_item_open", "div", 1)
        item_token.meta = {
            "label": label,
            "spaces": spaces_len,
        }

        # Collect content lines for this item
        content_lines = [line_text[content_start:].strip()]
        # The indentation level is roughly the start of the content
        indent_needed = content_start

        next_line = current_line + 1
        while next_line < end_line:
            # We must be careful not to consume a line that belongs to another block
            n_pos = state.bMarks[next_line]
            n_indent = state.tShift[next_line]
            n_max = state.eMarks[next_line]
            n_text = state.src[n_pos + n_indent : n_max]

            if not n_text.strip():
                break

            # If the line is not indented enough, it might be a new block
            # (unless it's a paragraph continuation, but we are a block rule)
            if n_indent < indent_needed and not LABEL_RE.match(n_text):
                # Standard markdown allows 'lazy' continuation for some blocks,
                # but for custom labels we'll require indentation or at least
                # check if it looks like a new block.
                # If it's not indented and not another label, it might be a
                # normal paragraph starting.
                pass

            # If it's a new label, stop
            if LABEL_RE.match(n_text):
                break

            content_lines.append(n_text.strip())
            next_line += 1

        state.push("paragraph_open", "p", 1)
        inline_token = state.push("inline", "", 0)
        inline_token.content = " ".join(content_lines)
        inline_token.map = [current_line, next_line]
        inline_token.children = []
        state.push("paragraph_close", "p", -1)

        state.push("custom_label_item_close", "div", -1)
        current_line = next_line

    state.push("custom_label_list_close", "div", -1)
    state.line = current_line
    return True


def custom_label_plugin(md: MarkdownIt) -> None:
    """Plugin for custom label lists."""
    md.block.ruler.before("paragraph", "custom_label", custom_label_rule)


def render_custom_label_list(node: RenderTreeNode, context: RenderContext) -> str:
    """Render a custom label list."""
    return "\n".join(child.render(context) for child in node.children)


def render_custom_label_item(node: RenderTreeNode, context: RenderContext) -> str:
    """Render a custom label item."""
    label = node.meta.get("label")
    spaces_count = node.meta.get("spaces", 1)
    marker = f"{{::{label}}}"
    prefix = marker + (" " * spaces_count)

    # Render children (usually just inline)
    content = "".join(child.render(context) for child in node.children)

    # Paragraphs often have trailing newlines. Strip them so we can handle
    # the lines correctly and avoid blank lines in the output.
    content = content.rstrip("\n")
    if not content:
        return prefix

    lines = content.splitlines(keepends=True)
    first_line = lines[0]
    rest = "".join(lines[1:])

    # If there's rest, indent it to match the marker width
    if rest:
        return prefix + first_line + textwrap.indent(rest, " " * len(prefix))
    return prefix + first_line
