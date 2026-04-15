"""Pandoc golden test utilities.

Converts markdown to HTML via the pandoc binary, then compares
HTML(pandoc, original) with HTML(pandoc, mdformat(original))
to ensure formatting preserves semantics.
"""

from __future__ import annotations

import html.parser
import re
import shutil
import subprocess
from typing import Any


def has_pandoc() -> bool:
    """Check if the pandoc binary is available on PATH."""
    return shutil.which("pandoc") is not None


def pandoc_to_html(md_text: str) -> str:
    """Convert markdown to HTML using the pandoc binary.

    Uses pandoc's default markdown format (which includes all extensions
    enabled by default in pandoc's Markdown).
    """
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "html", "--wrap=none"],
        input=md_text,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return result.stdout


class _HTMLNormalizer(html.parser.HTMLParser):
    """Parse HTML and produce a normalized string for comparison.

    Strips insignificant whitespace differences so that semantically
    identical HTML compares equal.
    """

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        sorted_attrs = sorted(attrs, key=lambda a: a[0])
        attr_str = ""
        for k, v in sorted_attrs:
            if v is None:
                attr_str += f" {k}"
            else:
                attr_str += f' {k}="{v}"'
        self._parts.append(f"<{tag}{attr_str}>")

    def handle_endtag(self, tag: str) -> None:
        self._parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        # Normalize whitespace in text nodes
        normalized = re.sub(r"\s+", " ", data).strip()
        if normalized:
            self._parts.append(normalized)

    def handle_entityref(self, name: str) -> None:
        self._parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self._parts.append(f"&#{name};")

    def get_result(self) -> str:
        return "".join(self._parts)


def normalize_html(html_str: str) -> str:
    """Normalize HTML for comparison.

    Strips whitespace differences and sorts attributes so that
    semantically identical HTML compares equal.
    """
    parser = _HTMLNormalizer()
    parser.feed(html_str)
    return parser.get_result()


def assert_pandoc_parity(
    md_input: str,
    *,
    wrap: int | None = None,
    extensions: set[str] | None = None,
) -> None:
    """Assert that formatting markdown does not change pandoc's HTML output.

    This is the core parity assertion:
        pandoc_html(input) == pandoc_html(mdformat(input))

    Args:
        md_input: The raw markdown input.
        wrap: If set, pass --wrap=<N> to mdformat.
        extensions: mdformat extensions to enable (defaults to {"pandoc"}).
    """
    import mdformat

    if extensions is None:
        extensions = {"pandoc"}

    # Format with mdformat
    kwargs: dict[str, Any] = {"extensions": extensions}
    if wrap is not None:
        kwargs["options"] = {"wrap": wrap}

    formatted = mdformat.text(md_input, **kwargs)

    # Convert both to HTML via pandoc
    html_original = pandoc_to_html(md_input)
    html_formatted = pandoc_to_html(formatted)

    # Normalize and compare
    norm_original = normalize_html(html_original)
    norm_formatted = normalize_html(html_formatted)

    if norm_original != norm_formatted:
        # Build a helpful error message
        msg_parts = [
            "Pandoc HTML parity violation!",
            "",
            "=== Original markdown ===",
            md_input,
            "=== Formatted markdown ===",
            formatted,
            "=== Original HTML (normalized) ===",
            norm_original,
            "=== Formatted HTML (normalized) ===",
            norm_formatted,
            "=== Original HTML (raw) ===",
            html_original,
            "=== Formatted HTML (raw) ===",
            html_formatted,
        ]
        raise AssertionError("\n".join(msg_parts))


def assert_idempotent(
    md_input: str,
    *,
    wrap: int | None = None,
    extensions: set[str] | None = None,
) -> str:
    """Assert that formatting is idempotent: format(format(x)) == format(x).

    Returns the formatted output.
    """
    import mdformat

    if extensions is None:
        extensions = {"pandoc"}

    kwargs: dict[str, Any] = {"extensions": extensions}
    if wrap is not None:
        kwargs["options"] = {"wrap": wrap}

    first = mdformat.text(md_input, **kwargs)
    second = mdformat.text(first, **kwargs)

    if first != second:
        msg_parts = [
            "Idempotency violation!",
            "",
            "=== Input ===",
            md_input,
            "=== First format ===",
            first,
            "=== Second format ===",
            second,
        ]
        raise AssertionError("\n".join(msg_parts))

    return first
