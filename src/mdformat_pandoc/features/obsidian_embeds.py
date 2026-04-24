"""Obsidian embed syntax support: ![[target]].

Obsidian uses ``![[filename]]`` to embed notes, images, and other files.
This module adds a markdown-it inline rule to tokenize them,
preventing mdformat's default bracket escaping from mangling them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from markdown_it import MarkdownIt
    from markdown_it.rules_inline import StateInline
    from mdformat.renderer import RenderContext, RenderTreeNode


def obsidian_embed_plugin(md: MarkdownIt) -> None:
    """Register the obsidian embed inline rule.

    Must be registered before the wikilink and image rules so that
    ``![[`` is matched as an embed rather than ``!`` + wikilink.
    """
    md.inline.ruler.before("image", "obsidian_embed", _obsidian_embed_tokenize)


def _obsidian_embed_tokenize(state: StateInline, silent: bool) -> bool:  # noqa: FBT001
    """Tokenize ``![[target]]``."""
    start = state.pos
    maximum = state.posMax

    # Need at least ![[x]]
    min_embed_len = 6
    if start + min_embed_len > maximum + 1 or state.src[start : start + 3] != "![[":
        return False

    # Scan forward for closing ]], disallowing newlines
    pos = start + 3
    while pos < maximum and state.src[pos : pos + 2] != "]]":
        if state.src[pos] == "\n":
            return False
        pos += 1

    inner = state.src[start + 3 : pos]

    # Must have found ]] and non-empty content
    if state.src[pos : pos + 2] != "]]" or not inner:
        return False

    if silent:
        return True

    token = state.push("obsidian_embed", "", 0)
    token.markup = "![["
    token.meta = {"target": inner}

    state.pos = pos + 2
    return True


def render_obsidian_embed(node: RenderTreeNode, _context: RenderContext) -> str:
    """Render an obsidian embed token back to ``![[target]]``."""
    target = str(node.meta.get("target", ""))
    return f"![[{target}]]"
