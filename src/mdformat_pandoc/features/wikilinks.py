"""Wikilink syntax support: [[target]] and [[target|alias]].

Obsidian and other wiki-style editors use double-bracket links.
This module adds a markdown-it inline rule to tokenize them,
preventing mdformat's default bracket escaping from mangling them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from markdown_it import MarkdownIt
    from markdown_it.rules_inline import StateInline
    from mdformat.renderer import RenderContext, RenderTreeNode


def wikilink_plugin(md: MarkdownIt) -> None:
    """Register the wikilink inline rule."""
    md.inline.ruler.before("link", "wikilink", _wikilink_tokenize)


def _wikilink_tokenize(state: StateInline, silent: bool) -> bool:  # noqa: FBT001
    """Tokenize ``[[target]]`` and ``[[target|alias]]``."""
    start = state.pos
    maximum = state.posMax

    # Need at least [[ + one char + ]]
    min_wikilink_len = 5
    if start + min_wikilink_len > maximum + 1 or state.src[start : start + 2] != "[[":
        return False

    # Scan forward for closing ]], disallowing newlines
    pos = start + 2
    while pos < maximum and state.src[pos : pos + 2] != "]]":
        if state.src[pos] == "\n":
            return False
        pos += 1

    inner = state.src[start + 2 : pos]

    # Must have found ]] and non-empty content
    if state.src[pos : pos + 2] != "]]" or not inner:
        return False

    if silent:
        return True

    token = state.push("wikilink", "", 0)
    token.markup = "[["

    # Split on first | for alias syntax
    if "|" in inner:
        pipe_idx = inner.index("|")
        token.meta = {
            "target": inner[:pipe_idx],
            "alias": inner[pipe_idx + 1 :],
        }
    else:
        token.meta = {"target": inner}

    state.pos = pos + 2
    return True


def render_wikilink(node: RenderTreeNode, _context: RenderContext) -> str:
    """Render a wikilink token back to ``[[target]]`` or ``[[target|alias]]``."""
    target = str(node.meta.get("target", ""))
    alias = node.meta.get("alias")
    if alias is not None:
        return f"[[{target}|{alias}]]"
    return f"[[{target}]]"
