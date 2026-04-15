from __future__ import annotations

import re
from typing import TYPE_CHECKING

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline

if TYPE_CHECKING:
    from mdformat.renderer import RenderContext, RenderTreeNode


def superscript_plugin(md: MarkdownIt) -> None:
    """Markdown-it-py plugin to handle ^superscript^."""

    def tokenize(state: StateInline, silent: bool) -> bool:
        start = state.pos
        if state.src[start] != "^":
            return False

        if silent:
            return False

        # Look for closing ^
        maximum = state.posMax
        state.pos = start + 1

        found = False
        while state.pos < maximum:
            if state.src[state.pos] == "^":
                found = True
                break
            state.md.inline.skipToken(state)

        if not found or start + 1 == state.pos:
            state.pos = start
            return False

        # Found closing ^
        res_pos = state.pos
        token = state.push("sup_open", "sup", 1)
        token.markup = "^"

        state.posMax = res_pos
        state.pos = start + 1
        state.md.inline.tokenize(state)
        state.pos = res_pos + 1
        state.posMax = maximum

        token = state.push("sup_close", "sup", -1)
        token.markup = "^"

        return True

    md.inline.ruler.after("emphasis", "sup", tokenize)


def subscript_plugin(md: MarkdownIt) -> None:
    """Markdown-it-py plugin to handle ~subscript~."""

    def tokenize(state: StateInline, silent: bool) -> bool:
        start = state.pos
        if state.src[start] != "~":
            return False

        if silent:
            return False

        # Look for closing ~
        maximum = state.posMax
        state.pos = start + 1

        found = False
        while state.pos < maximum:
            if state.src[state.pos] == "~":
                found = True
                break
            state.md.inline.skipToken(state)

        if not found or start + 1 == state.pos:
            state.pos = start
            return False

        # Found closing ~
        res_pos = state.pos
        token = state.push("sub_open", "sub", 1)
        token.markup = "~"

        state.posMax = res_pos
        state.pos = start + 1
        state.md.inline.tokenize(state)
        state.pos = res_pos + 1
        state.posMax = maximum

        token = state.push("sub_close", "sub", -1)
        token.markup = "~"

        return True

    md.inline.ruler.after("emphasis", "sub", tokenize)


def _escape_spaces_for_pandoc(content: str) -> str:
    """Escape spaces (and WRAP_POINT markers) with backslash for Pandoc sub/superscripts.

    When mdformat wraps text, spaces in text tokens are replaced with
    WRAP_POINT (\\x00) before sub/sup renderers see them. We need to
    replace both regular spaces and WRAP_POINT characters with the
    Pandoc escaped-space sequence ``\\ ``.
    """
    # Replace WRAP_POINT (\x00) and regular spaces with escaped space
    return re.sub(r"[\x00 ]", "\\ ", content)


def render_sub(node: RenderTreeNode, context: RenderContext) -> str:
    """Render subscript: ~text~"""
    content = "".join(child.render(context) for child in node.children)
    # Pandoc requires spaces in subscripts to be escaped with a backslash
    content = _escape_spaces_for_pandoc(content)
    return f"~{content}~"


def render_sup(node: RenderTreeNode, context: RenderContext) -> str:
    """Render superscript: ^text^"""
    content = "".join(child.render(context) for child in node.children)
    # Pandoc requires spaces in superscripts to be escaped with a backslash
    content = _escape_spaces_for_pandoc(content)
    return f"^{content}^"
