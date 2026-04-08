from __future__ import annotations

from typing import TYPE_CHECKING

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline

if TYPE_CHECKING:
    from mdformat.renderer import RenderContext, RenderTreeNode


def superscript_plugin(md: MarkdownIt) -> None:
    """Markdown-it-py plugin to handle ^superscript^."""

    def superscript_rule(state: StateInline, silent: bool) -> bool:
        start = state.pos
        if state.src[start] != "^":
            return False

        if silent:
            return False

        # Look for closing ^
        maximum = state.posMax
        # Skip the opening ^
        state.pos += 1

        found = False
        while state.pos < maximum:
            if state.src[state.pos] == "^":
                # Check for escaped ^
                if state.src[state.pos - 1] == "\\":
                    state.pos += 1
                    continue
                found = True
                break
            state.pos += 1

        if not found:
            state.pos = start
            return False

        # Found closing ^
        # Create tokens
        token = state.push("sup_open", "sup", 1)
        token.markup = "^"

        maximum_old = state.posMax
        state.posMax = state.pos
        state.pos = start + 1
        state.md.inline.tokenize(state)
        state.pos = state.posMax + 1
        state.posMax = maximum_old

        token = state.push("sup_close", "sup", -1)
        token.markup = "^"

        return True

    md.inline.ruler.after("emphasis", "sup", superscript_rule)


def render_sub(node: RenderTreeNode, context: RenderContext) -> str:
    """Render subscript: ~text~"""
    # mdit-py-plugins subscript uses 'sub' as token type
    content = "".join(child.render(context) for child in node.children)
    return f"~{content}~"


def render_sup(node: RenderTreeNode, context: RenderContext) -> str:
    """Render superscript: ^text^"""
    # Our custom superscript uses 'sup' as token type
    content = "".join(child.render(context) for child in node.children)
    return f"^{content}^"
