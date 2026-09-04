"""Postprocessors for mdformat-pandoc.

Postprocessors run after the default renderer and can modify the
rendered text.  They are collaborative: multiple plugins can each
define a postprocessor for the same node type and all will execute.
"""

from __future__ import annotations


def _postprocess_escape_dollar(text: str, _node: object, _context: object) -> str:
    """Escape literal dollar signs so the dollarmath plugin won't
    misinterpret them as inline math delimiters on re-parse.

    Without this, an input like ``\\$100 ... \\$200`` is rendered as
    ``$100 ... $200``, and the dollarmath plugin matches the region
    between the two bare ``$`` as inline math, causing mdformat's
    HTML-equivalence check to fail.
    """
    return text.replace("$", "\\$")


POSTPROCESSORS = {
    "text": _postprocess_escape_dollar,
}
