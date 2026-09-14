"""Postprocessors for mdformat-pandoc."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mdformat_pandoc.utils import ATTR_PATTERN, format_attributes

if TYPE_CHECKING:
    from mdformat.renderer import RenderContext, RenderTreeNode


def _postprocess_text(text: str, node: RenderTreeNode, _context: RenderContext) -> str:
    res = text.replace("$", "\\$")

    # Fix trailing backslash bug: mdformat escapes backslashes, but at the end of a paragraph
    # we want to output exactly one backslash (Pandoc hard break).
    if (
        node.content == "\\"
        and not node.next_sibling
        and node.parent
        and node.parent.type == "inline"
        and node.parent.parent
        and node.parent.parent.type == "paragraph"
        and res == "\\\\"
    ):
        res = "\\"

    # Format attributes that follow images or links
    if node.previous_sibling and node.previous_sibling.type in ("image", "link"):
        m = ATTR_PATTERN.match(res)
        if m:
            formatted = format_attributes(m.group(0))
            res = formatted + res[m.end() :]

    return res


def _postprocess_heading(text: str, _node: RenderTreeNode, _context: RenderContext) -> str:
    # Headings have their attributes at the very end
    m = list(ATTR_PATTERN.finditer(text))
    if m:
        last_match = m[-1]
        if last_match.end() == len(text) or text[last_match.end() :].isspace():
            formatted = format_attributes(last_match.group(0))
            text = text[: last_match.start()] + formatted + text[last_match.end() :]

    return text


def _postprocess_fence(text: str, _node: RenderTreeNode, _context: RenderContext) -> str:
    # `fence` text typically looks like ```{#id .class}\ncode\n```
    # If there's an info string, it's immediately after the opening backticks/tildes
    m = ATTR_PATTERN.search(text)
    if m:
        # Only replace if it's on the first line (the info string)
        first_newline = text.find("\n")
        if first_newline == -1 or m.start() < first_newline:
            formatted = format_attributes(m.group(0))
            text = text[: m.start()] + formatted + text[m.end() :]

    return text


POSTPROCESSORS = {
    "text": _postprocess_text,
    "heading": _postprocess_heading,
    "fence": _postprocess_fence,
}
