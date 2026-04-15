"""Pandoc parity tests.

These tests verify that mdformat-pandoc reformats markdown without
changing the HTML output that pandoc produces. This is the gold
standard for formatter correctness.

Tests are organized by pandoc Markdown extension category and are
loaded from fixture files in tests/fixtures/.

Two test dimensions:
  1. Idempotency: format(format(x)) == format(x)
  2. HTML Parity: pandoc_html(x) == pandoc_html(format(x))

Both dimensions are tested with and without wrapping.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pandoc_golden import (
    assert_idempotent,
    assert_pandoc_parity,
    has_pandoc,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Skip the custom_labels directory for pandoc parity tests since
# custom labels are a non-standard extension that pandoc doesn't
# natively understand.
SKIP_PARITY_DIRS = {"custom_labels"}


def _collect_fixtures(
    *categories: str,
    skip_parity: bool = False,
) -> list[tuple[str, str]]:
    """Collect (test_id, markdown_content) from fixture directories.

    Args:
        categories: Subdirectory names under fixtures/ to scan.
            If empty, scan all subdirectories.
        skip_parity: If True, exclude directories in SKIP_PARITY_DIRS.

    """
    fixtures: list[tuple[str, str]] = []

    if not categories:
        categories = tuple(
            d.name
            for d in sorted(FIXTURES_DIR.iterdir())
            if d.is_dir() and not d.name.startswith(".")
        )

    for category in categories:
        if skip_parity and category in SKIP_PARITY_DIRS:
            continue
        cat_dir = FIXTURES_DIR / category
        if not cat_dir.is_dir():
            continue
        for md_file in sorted(cat_dir.glob("*.md")):
            test_id = f"{category}/{md_file.stem}"
            content = md_file.read_text(encoding="utf-8")
            fixtures.append((test_id, content))

    return fixtures


# ─── Fixture collections ────────────────────────────────────────────
ALL_FIXTURES = _collect_fixtures()
PARITY_FIXTURES = _collect_fixtures(skip_parity=True)
CUSTOM_LABEL_FIXTURES = _collect_fixtures("custom_labels")


# ═══════════════════════════════════════════════════════════════════
# Idempotency Tests (no pandoc binary needed)
# ═══════════════════════════════════════════════════════════════════


class TestIdempotency:
    """Verify format(format(x)) == format(x) for all fixtures."""

    @pytest.mark.parametrize(("test_id", "md"), ALL_FIXTURES, ids=[f[0] for f in ALL_FIXTURES])
    def test_idempotent(self, test_id: str, md: str) -> None:
        assert_idempotent(md)

    @pytest.mark.parametrize(("test_id", "md"), ALL_FIXTURES, ids=[f[0] for f in ALL_FIXTURES])
    def test_idempotent_wrap80(self, test_id: str, md: str) -> None:
        assert_idempotent(md, wrap=80)


# ═══════════════════════════════════════════════════════════════════
# Pandoc HTML Parity Tests (require pandoc binary)
# ═══════════════════════════════════════════════════════════════════

PANDOC_SKIP = pytest.mark.skipif(
    not has_pandoc(),
    reason="pandoc binary not found on PATH",
)


@PANDOC_SKIP
class TestPandocParity:
    """Verify pandoc_html(x) == pandoc_html(format(x)) for standard fixtures."""

    @pytest.mark.parametrize(
        ("test_id", "md"), PARITY_FIXTURES, ids=[f[0] for f in PARITY_FIXTURES]
    )
    def test_parity(self, test_id: str, md: str) -> None:
        assert_pandoc_parity(md)

    @pytest.mark.parametrize(
        ("test_id", "md"), PARITY_FIXTURES, ids=[f[0] for f in PARITY_FIXTURES]
    )
    def test_parity_wrap80(self, test_id: str, md: str) -> None:
        assert_pandoc_parity(md, wrap=80)


# ═══════════════════════════════════════════════════════════════════
# Custom Label Tests (extended syntax — idempotency only)
# ═══════════════════════════════════════════════════════════════════


class TestCustomLabels:
    """Custom label lists are a non-standard extension.

    They can't be tested with pandoc parity (pandoc doesn't know them),
    so we only test idempotency.
    """

    @pytest.mark.parametrize(
        ("test_id", "md"), CUSTOM_LABEL_FIXTURES, ids=[f[0] for f in CUSTOM_LABEL_FIXTURES]
    )
    def test_idempotent(self, test_id: str, md: str) -> None:
        assert_idempotent(md)

    @pytest.mark.parametrize(
        ("test_id", "md"), CUSTOM_LABEL_FIXTURES, ids=[f[0] for f in CUSTOM_LABEL_FIXTURES]
    )
    def test_idempotent_wrap80(self, test_id: str, md: str) -> None:
        assert_idempotent(md, wrap=80)
