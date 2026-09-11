"""Pandoc bracketed span support: [content]{.class #id key="val"}.

Pandoc uses ``[inline content]{attributes}`` to apply attributes to
arbitrary inline content.  Without a dedicated parser rule, markdown-it
treats the square brackets as plain text.  When the bracketed content
contains inline formatting (emphasis, etc.), the ``[`` and ``]`` end up
in different text tokens and mdformat's escaper adds backslash escapes
that break the Pandoc syntax.

This module adds an inline rule that recognises the full
``[...]{...}`` construct and emits ``pandoc_span_open`` /
``pandoc_span_close`` tokens that wrap the inner inline content, plus
a renderer that reassembles the original syntax.

The same mechanism is extended to handle **Pandoc citations** of the
form ``[see @ref, pp. 33-35; @ref2]`` where the square brackets
contain ``@``-prefixed citation keys.  Without a parser rule these
brackets are also split by inline formatting and escaped.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from markdown_it import MarkdownIt
    from markdown_it.rules_inline import StateInline
    from mdformat.renderer import RenderContext, RenderTreeNode


# ── Attribute block regex ────────────────────────────────────────────
# Matches a ``{…}`` block immediately after a closing ``]``.
# Allows: #id, .class, key="value", key='value', key=value
# Also allows bare ``{}`` (empty attributes).
_RE_ATTR_BLOCK = re.compile(
    r"\{"
    r"(?:"
    r"[#.][A-Za-z0-9_-]+"  # #id or .class
    r"|[A-Za-z0-9_-]+=(?:\"[^\"]*\"|'[^']*'|[A-Za-z0-9_%-]+)"  # key=val
    r"|[ \t]"  # whitespace separators
    r")*"
    r"\}"
)

# ── Citation key regex ───────────────────────────────────────────────
# A citation key starts with ``@`` followed by an identifier made up
# of alphanumerics, ``_``, internal hyphens, slashes, dots, or colons
# (matching Pandoc's citation key syntax).
_RE_CITATION_KEY = re.compile(r"@[A-Za-z0-9_][A-Za-z0-9_:.#$%&\-+?<>~/]*")


# ═══════════════════════════════════════════════════════════════════
# Parser plugin
# ═══════════════════════════════════════════════════════════════════


def pandoc_span_plugin(md: MarkdownIt) -> None:
    """Register the Pandoc span/citation inline rule.

    Must be registered **before** the standard ``link`` rule so that
    ``[…]{…}`` is recognised before the link parser attempts (and
    fails) to match these brackets.
    """
    md.inline.ruler.before("link", "pandoc_span", _pandoc_span_tokenize)


def _try_match_attr_block(src: str, pos: int) -> str | None:
    """If *src* starting at *pos* is a ``{…}`` attribute block, return it.

    Returns ``None`` if no valid attribute block is found.
    """
    if pos >= len(src) or src[pos] != "{":
        return None
    m = _RE_ATTR_BLOCK.match(src, pos)
    if m is None:
        return None
    return m.group()


def _has_citation_key(text: str) -> bool:
    """Return True if *text* contains at least one ``@citationKey``."""
    return _RE_CITATION_KEY.search(text) is not None


def _find_closing_bracket(state: StateInline, open_pos: int) -> int | None:
    """Find the position of the ``]`` that closes a ``[`` at *open_pos*.

    Handles nested brackets but not escaped ones.  Returns ``None``
    if no matching close is found before ``posMax``.
    """
    depth = 1
    pos = open_pos + 1
    maximum = state.posMax
    while pos <= maximum:
        ch = state.src[pos]
        if ch == "\\":
            pos += 2  # skip escaped character
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return pos
        pos += 1
    return None


def _parse_inner(state: StateInline, start: int, close_pos: int) -> None:
    """Parse bracket-enclosed content as inline markdown."""
    old_max = state.posMax
    state.pos = start + 1
    state.posMax = close_pos
    state.md.inline.tokenize(state)
    state.posMax = old_max


def _try_span(
    state: StateInline,
    start: int,
    close_pos: int,
    *,
    silent: bool,
) -> bool:
    """Try to match ``[content]{attrs}``."""
    after_close = close_pos + 1
    attr_block = _try_match_attr_block(state.src, after_close)
    if attr_block is None:
        return False
    if not silent:
        token_open = state.push("pandoc_span_open", "span", 1)
        token_open.markup = "["
        token_open.meta = {"attrs": attr_block}
        _parse_inner(state, start, close_pos)
        token_close = state.push("pandoc_span_close", "span", -1)
        token_close.markup = "]"
    state.pos = after_close + len(attr_block)
    return True


def _try_citation(
    state: StateInline,
    start: int,
    close_pos: int,
    *,
    silent: bool,
) -> bool:
    """Try to match ``[…@key…]``."""
    inner_text = state.src[start + 1 : close_pos]
    if not _has_citation_key(inner_text):
        return False
    # Don't consume brackets that belong to a regular or ref link.
    after_close = close_pos + 1
    next_char = state.src[after_close] if after_close < len(state.src) else ""
    if next_char in ("(", "["):
        return False
    if not silent:
        token_open = state.push("pandoc_citation_open", "", 1)
        token_open.markup = "["
        _parse_inner(state, start, close_pos)
        token_close = state.push("pandoc_citation_close", "", -1)
        token_close.markup = "]"
    state.pos = after_close
    return True


def _pandoc_span_tokenize(state: StateInline, silent: bool) -> bool:  # noqa: FBT001
    """Tokenize ``[content]{attrs}`` spans and ``[@citekey …]`` citations."""
    start = state.pos

    if state.src[start] != "[":
        return False

    close_pos = _find_closing_bracket(state, start)
    if close_pos is None:
        return False

    if _try_span(state, start, close_pos, silent=silent):
        return True

    return _try_citation(state, start, close_pos, silent=silent)


# ═══════════════════════════════════════════════════════════════════
# Renderers
# ═══════════════════════════════════════════════════════════════════


def render_pandoc_span(node: RenderTreeNode, context: RenderContext) -> str:
    """Render ``[inline content]{attrs}``."""
    inner = "".join(child.render(context) for child in node.children)
    attrs = str(node.meta.get("attrs", "{}"))
    return f"[{inner}]{attrs}"


def render_pandoc_citation(node: RenderTreeNode, context: RenderContext) -> str:
    """Render ``[…@citekey…]``."""
    inner = "".join(child.render(context) for child in node.children)
    return f"[{inner}]"
