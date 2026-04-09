from __future__ import annotations

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


def render_sub(node: RenderTreeNode, context: RenderContext) -> str:
    """Render subscript: ~text~"""
    # mdit-py-plugins subscript uses 'sub' as token type
    content = "".join(child.render(context) for child in node.children)
    # Pandoc requires spaces in subscripts to be escaped with a backslash
    content = content.replace(" ", "\\ ")
    return f"~{content}~"


def render_sup(node: RenderTreeNode, context: RenderContext) -> str:
    """Render superscript: ^text^"""
    # Our custom superscript uses 'sup' as token type
    content = "".join(child.render(context) for child in node.children)
    # Pandoc requires spaces in superscripts to be escaped with a backslash
    content = content.replace(" ", "\\ ")
    return f"^{content}^"
