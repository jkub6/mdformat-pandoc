"""Comprehensive test suite for pandoc footnote features in mdformat-pandoc.

Covers:
1. Block-level placement directly after respective paragraph / container.
2. Inline footnote conversion to block footnotes.
3. Sequential renumbering in order of appearance.
4. Multi-usage naming scheme (num_usages: 1_2, 2_3) for reused footnotes.
5. Emitting definitions only once, after the first usage.
6. Placement after various container blocks (headings, blockquotes, lists, tables, divs).
7. Multiblock footnote definitions.
8. Idempotency and self-healing when usages change.
9. Pandoc HTML parity.
"""

from __future__ import annotations

import mdformat
import pytest
from pandoc_golden import (
    assert_idempotent,
    assert_pandoc_parity,
    has_pandoc,
)

PANDOC_SKIP = pytest.mark.skipif(
    not has_pandoc(),
    reason="pandoc binary not found on PATH",
)


def _fmt(md: str, wrap: int | None = None) -> str:
    kwargs: dict = {"extensions": {"pandoc"}}
    if wrap is not None:
        kwargs["options"] = {"wrap": wrap}
    return mdformat.text(md, **kwargs)


class TestFootnoteSequentialRenumbering:
    def test_out_of_order_labels_renumbered(self) -> None:
        inp = "First para[^zebra] and [^apple].\n\n[^apple]: Apple note.\n[^zebra]: Zebra note.\n"
        expected = (
            "First para[^1] and [^2].\n\n[^1]: \n    Zebra note.\n\n[^2]: \n    Apple note.\n"
        )
        assert _fmt(inp) == expected
        assert_idempotent(inp)

    def test_order_of_usage_across_paragraphs(self) -> None:
        inp = "Paragraph one[^b].\n\nParagraph two[^a].\n\n[^a]: Alpha.\n[^b]: Beta.\n"
        expected = (
            "Paragraph one[^1].\n\n[^1]: \n    Beta.\n\nParagraph two[^2].\n\n[^2]: \n    Alpha.\n"
        )
        assert _fmt(inp) == expected
        assert_idempotent(inp)


class TestInlineFootnoteConversion:
    def test_inline_footnote_converted_to_block(self) -> None:
        inp = "Here is a note^[this is inline].\n"
        expected = "Here is a note[^1].\n\n[^1]: \n    this is inline\n"
        assert _fmt(inp) == expected
        assert_idempotent(inp)

    def test_inline_footnote_with_formatting(self) -> None:
        inp = "Text^[This has *emphasis* and `code`].\n"
        expected = "Text[^1].\n\n[^1]: \n    This has *emphasis* and `code`\n"
        assert _fmt(inp) == expected
        assert_idempotent(inp)

    def test_mixed_inline_and_block_footnotes(self) -> None:
        inp = (
            "Paragraph with block note[^b] and inline note^[inline content].\n\n"
            "[^b]: Block content.\n"
        )
        expected = (
            "Paragraph with block note[^1] and inline note[^2].\n\n"
            "[^1]: \n    Block content.\n\n"
            "[^2]: \n    inline content\n"
        )
        assert _fmt(inp) == expected
        assert_idempotent(inp)

    @PANDOC_SKIP
    def test_inline_footnote_pandoc_parity(self) -> None:
        inp = "Text^[This has *emphasis* and `code`].\n"
        assert_pandoc_parity(inp)


class TestReusedFootnotes:
    def test_reused_footnote_naming_scheme(self) -> None:
        """Footnotes used in multiple places use num_usages (e.g. 1_2), single-use use num."""
        inp = (
            "Para 1 with single[^single] and reused[^shared].\n\n"
            "[^single]: Single note.\n"
            "[^shared]: Shared note.\n\n"
            "Para 2 with reused[^shared] again.\n"
        )
        expected = (
            "Para 1 with single[^1] and reused[^2_2].\n\n"
            "[^1]: \n    Single note.\n\n"
            "[^2_2]: \n    Shared note.\n\n"
            "Para 2 with reused[^2_2] again.\n"
        )
        assert _fmt(inp) == expected
        assert_idempotent(inp)

    def test_reused_footnote_definition_only_after_first_usage(self) -> None:
        """Definition only appears after first usage; subsequent usages omit definition."""
        inp = (
            "Para 1[^shared].\n\n"
            "Para 2[^shared].\n\n"
            "Para 3[^shared].\n\n"
            "[^shared]: Shared definition.\n"
        )
        expected = (
            "Para 1[^1_3].\n\n[^1_3]: \n    Shared definition.\n\nPara 2[^1_3].\n\nPara 3[^1_3].\n"
        )
        assert _fmt(inp) == expected
        assert_idempotent(inp)

    def test_reused_footnote_in_same_paragraph(self) -> None:
        """Reusing the same footnote twice in one paragraph only emits definition once."""
        inp = "First ref[^dup] and second ref[^dup] in same paragraph.\n\n[^dup]: Duplicate note.\n"
        expected = (
            "First ref[^1_2] and second ref[^1_2] in same paragraph.\n\n"
            "[^1_2]: \n    Duplicate note.\n"
        )
        assert _fmt(inp) == expected
        assert_idempotent(inp)

    def test_self_healing_when_usage_removed(self) -> None:
        """If a reused footnote is reduced to 1 usage, it reverts to standard number."""
        inp = "Para 1[^1_2].\n\n[^1_2]: \n    Note content.\n"
        expected = "Para 1[^1].\n\n[^1]: \n    Note content.\n"
        assert _fmt(inp) == expected

    def test_self_healing_when_usage_added(self) -> None:
        """If an additional reference is added to [^1_2], it updates to [^1_3]."""
        inp = "Para 1[^1_2].\n\n[^1_2]: \n    Note content.\n\nPara 2[^1_2].\n\nPara 3[^1_2].\n"
        expected = (
            "Para 1[^1_3].\n\n[^1_3]: \n    Note content.\n\nPara 2[^1_3].\n\nPara 3[^1_3].\n"
        )
        assert _fmt(inp) == expected

    @PANDOC_SKIP
    def test_reused_footnote_pandoc_parity(self) -> None:
        inp = (
            "Para 1 with single[^single] and reused[^shared].\n\n"
            "[^single]: Single note.\n"
            "[^shared]: Shared note.\n\n"
            "Para 2 with reused[^shared] again.\n"
        )
        assert_pandoc_parity(inp)


class TestContainerBlocks:
    def test_footnote_after_heading(self) -> None:
        inp = "# Heading[^1]\n\n[^1]: Heading footnote.\n\nParagraph.\n"
        expected = "# Heading[^1]\n\n[^1]: \n    Heading footnote.\n\nParagraph.\n"
        assert _fmt(inp) == expected
        assert_idempotent(inp)

    def test_footnote_after_blockquote(self) -> None:
        inp = "> Quote with note[^1].\n\n[^1]: Quote footnote.\n\nParagraph.\n"
        expected = "> Quote with note[^1].\n\n[^1]: \n    Quote footnote.\n\nParagraph.\n"
        assert _fmt(inp) == expected
        assert_idempotent(inp)

    def test_footnote_after_bullet_list(self) -> None:
        inp = "- Item 1 with note[^a]\n- Item 2 with note[^b]\n\n[^a]: Note A.\n[^b]: Note B.\n"
        expected = (
            "- Item 1 with note[^1]\n"
            "- Item 2 with note[^2]\n\n"
            "[^1]: \n    Note A.\n\n"
            "[^2]: \n    Note B.\n"
        )
        assert _fmt(inp) == expected
        assert_idempotent(inp)

    def test_footnote_after_ordered_list(self) -> None:
        inp = "1. Item 1[^a]\n2. Item 2[^b]\n\n[^a]: Note A.\n[^b]: Note B.\n"
        expected = "1. Item 1[^1]\n2. Item 2[^2]\n\n[^1]: \n    Note A.\n\n[^2]: \n    Note B.\n"
        assert _fmt(inp) == expected
        assert_idempotent(inp)

    def test_footnote_after_table(self) -> None:
        inp = (
            "| Header 1 | Header 2 |\n| --- | --- |\n| Cell 1[^1] | Cell 2 |\n\n[^1]: Table note.\n"
        )
        expected = (
            "| Header 1   | Header 2 |\n"
            "| ---------- | -------- |\n"
            "| Cell 1[^1] | Cell 2   |\n\n"
            "[^1]: \n    Table note.\n"
        )
        assert _fmt(inp) == expected
        assert_idempotent(inp)

    def test_footnote_after_fenced_div(self) -> None:
        inp = "::: {.note}\nDiv content[^1].\n:::\n\n[^1]: Div note.\n"
        expected = "::: {.note}\n\nDiv content[^1].\n\n:::\n\n[^1]: \n    Div note.\n"
        assert _fmt(inp) == expected
        assert_idempotent(inp)

    @PANDOC_SKIP
    def test_container_footnotes_pandoc_parity(self) -> None:
        inp = (
            "> Quote with note[^1].\n\n"
            "- Item with note[^2]\n\n"
            "| Col |\n| --- |\n| Cell[^3] |\n\n"
            "[^1]: Note 1.\n"
            "[^2]: Note 2.\n"
            "[^3]: Note 3.\n"
        )
        assert_pandoc_parity(inp)


class TestMultiblockFootnotes:
    def test_multiblock_footnote_placement(self) -> None:
        inp = (
            "Here is a note[^multi].\n\n"
            "[^multi]: \n"
            "    First paragraph of note.\n\n"
            "    Second paragraph of note.\n\n"
            "    ```\n"
            "    code block\n"
            "    ```\n\n"
            "Following paragraph.\n"
        )
        expected = (
            "Here is a note[^1].\n\n"
            "[^1]: \n"
            "    First paragraph of note.\n\n"
            "    Second paragraph of note.\n\n"
            "    ```\n"
            "    code block\n"
            "    ```\n\n"
            "Following paragraph.\n"
        )
        assert _fmt(inp) == expected
        assert_idempotent(inp)

    @PANDOC_SKIP
    def test_multiblock_footnote_pandoc_parity(self) -> None:
        inp = (
            "Here is a note[^multi].\n\n"
            "[^multi]: \n"
            "    First paragraph of note.\n\n"
            "    Second paragraph of note.\n\n"
            "Following paragraph.\n"
        )
        assert_pandoc_parity(inp)
