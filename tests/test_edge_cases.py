"""Comprehensive edge case tests for mdformat-pandoc.

Tests for boundary conditions, unusual combinations, and known tricky
scenarios that exercise the full range of pandoc markdown syntax.
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


# ═══════════════════════════════════════════════════════════════════
# Image edge cases
# ═══════════════════════════════════════════════════════════════════


class TestImageEdgeCases:
    """Tests for various image formatting edge cases."""

    def test_image_trailing_backslash_with_text(self) -> None:
        """Image with trailing backslash + text on next line (non-figure)."""
        md = "![alt](image.png)\\\nSome text.\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_image_trailing_backslash_with_text_parity(self) -> None:
        md = "![alt](image.png)\\\nSome text.\n"
        assert_pandoc_parity(md)

    @PANDOC_SKIP
    def test_image_trailing_backslash_alone_parity(self) -> None:
        """Image alone with trailing backslash — prevents figure treatment.

        Pandoc manual §4.16: "If you just want a regular inline image,
        just make sure it is not the only thing in the paragraph. One way
        to do this is to insert a nonbreaking space after the image:
        ![This image won't be a figure](image.png)\\"
        """
        md = "![alt](image.png)\\\n"
        assert_pandoc_parity(md)

    def test_image_with_empty_alt(self) -> None:
        md = "![](image.png)\n"
        assert_idempotent(md)

    def test_image_with_title(self) -> None:
        md = '![alt](image.png "My Title")\n'
        assert_idempotent(md)

    def test_multiple_images_one_paragraph(self) -> None:
        md = "![a](a.png) ![b](b.png)\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_multiple_images_parity(self) -> None:
        md = "![a](a.png) ![b](b.png)\n"
        assert_pandoc_parity(md)


# ═══════════════════════════════════════════════════════════════════
# Emphasis edge cases
# ═══════════════════════════════════════════════════════════════════


class TestEmphasisEdgeCases:
    """Tests for emphasis formatting edge cases."""

    def test_bold_italic_combined(self) -> None:
        md = "***bold and italic***\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_bold_italic_parity(self) -> None:
        md = "***bold and italic***\n"
        assert_pandoc_parity(md)

    def test_emphasis_across_words(self) -> None:
        md = "This is *a multi-word emphasis*.\n"
        assert_idempotent(md)

    def test_nested_strong_in_emphasis(self) -> None:
        md = "*emphasized **and strong***\n"
        assert_idempotent(md)

    def test_strong_with_emphasis_inside(self) -> None:
        md = "**strong with *emphasis* inside**\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_strong_emphasis_parity(self) -> None:
        md = "**strong with *emphasis* inside**\n"
        assert_pandoc_parity(md)

    def test_underscore_emphasis(self) -> None:
        md = "This is _emphasized_ text.\n"
        assert_idempotent(md)

    def test_intraword_asterisk(self) -> None:
        md = "feas*ible*, not feas*able*.\n"
        assert_idempotent(md)


# ═══════════════════════════════════════════════════════════════════
# Subscript / Superscript edge cases
# ═══════════════════════════════════════════════════════════════════


class TestSubSupEdgeCases:
    """Tests for sub/superscript edge cases."""

    def test_multiple_subscripts(self) -> None:
        md = "H~2~O and CO~2~ and Fe~2~O~3~.\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_multiple_subscripts_parity(self) -> None:
        md = "H~2~O and CO~2~ and Fe~2~O~3~.\n"
        assert_pandoc_parity(md)

    def test_superscript_exponents(self) -> None:
        md = "This is 2^10^ and 10^3^ and x^n^.\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_superscript_exponents_parity(self) -> None:
        md = "This is 2^10^ and 10^3^ and x^n^.\n"
        assert_pandoc_parity(md)

    def test_sub_with_escaped_space(self) -> None:
        md = "P~a\\ cat~ has spaces.\n"
        assert_idempotent(md)

    def test_sup_with_escaped_space(self) -> None:
        md = "x^a\\ b^ has spaces.\n"
        assert_idempotent(md)

    def test_nested_sub_in_sup(self) -> None:
        md = "test ~sub^sup^~ here\n"
        assert_idempotent(md)

    def test_sub_with_bold(self) -> None:
        md = "test ~*bold\\ sub*~ here\n"
        assert_idempotent(md)


# ═══════════════════════════════════════════════════════════════════
# Strikeout edge cases
# ═══════════════════════════════════════════════════════════════════


class TestStrikeoutEdgeCases:
    def test_strikeout_with_emphasis(self) -> None:
        md = "This is ~~*important* deleted text~~.\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_strikeout_with_emphasis_parity(self) -> None:
        md = "This is ~~*important* deleted text~~.\n"
        assert_pandoc_parity(md)

    def test_strikeout_with_strong(self) -> None:
        md = "This is ~~**strongly** deleted~~.\n"
        assert_idempotent(md)

    def test_strikeout_with_code(self) -> None:
        md = "This is ~~`code` deleted~~.\n"
        assert_idempotent(md)


# ═══════════════════════════════════════════════════════════════════
# Citation edge cases
# ═══════════════════════════════════════════════════════════════════


class TestCitationEdgeCases:
    """Tests for citation formatting edge cases."""

    def test_citation_in_footnote(self) -> None:
        md = "Text[^1]\n\n[^1]: \n    See [@smith04] for details.\n"
        assert_idempotent(md)

    def test_citation_multiple_with_locators(self) -> None:
        md = "Blah blah [see @doe99, pp. 33-35 and *passim*; @smith04, chap. 1].\n"
        assert_idempotent(md)

    def test_citation_with_braces(self) -> None:
        md = "two[@Foo{ii, A, D-Z}, with a suffix]\n"
        assert_idempotent(md)

    def test_citation_empty_braces(self) -> None:
        md = "four[@Foo{}, 99 years later]\n"
        assert_idempotent(md)

    def test_citation_suppressed_author(self) -> None:
        md = "Smith says blah [-@smith04].\n"
        assert_idempotent(md)

    def test_citation_author_in_text(self) -> None:
        md = "@smith04 says blah.\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_citation_author_in_text_parity(self) -> None:
        md = "@smith04 says blah.\n"
        assert_pandoc_parity(md)


# ═══════════════════════════════════════════════════════════════════
# Span edge cases
# ═══════════════════════════════════════════════════════════════════


class TestSpanEdgeCases:
    def test_span_with_empty_attrs(self) -> None:
        md = "[text]{}\n"
        assert_idempotent(md)

    def test_span_empty_content(self) -> None:
        md = "[]{#my-anchor}\n"
        assert_idempotent(md)

    def test_span_with_multiple_classes(self) -> None:
        md = '[styled]{#id .class1 .class2 key="val"}\n'
        assert_idempotent(md)

    def test_span_nested(self) -> None:
        md = "[outer [inner]{.a}]{.b}\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_span_parity(self) -> None:
        md = '[This is *some text*]{.class key="val"}\n'
        assert_pandoc_parity(md)


# ═══════════════════════════════════════════════════════════════════
# Footnote edge cases
# ═══════════════════════════════════════════════════════════════════


class TestFootnoteEdgeCases:
    def test_inline_footnote_with_formatting(self) -> None:
        md = "Text^[This has *emphasis* and `code`].\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_inline_footnote_parity(self) -> None:
        md = "Text^[This has *emphasis* and `code`].\n"
        assert_pandoc_parity(md)

    def test_multiple_footnote_refs(self) -> None:
        md = "First[^1] and second[^2].\n\n[^1]: \n    Note one.\n\n[^2]: \n    Note two.\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_multiple_footnotes_parity(self) -> None:
        md = "First[^1] and second[^2].\n\n[^1]: \n    Note one.\n\n[^2]: \n    Note two.\n"
        assert_pandoc_parity(md)

    def test_footnote_with_code_block(self) -> None:
        md = (
            "Test[^1]\n\n[^1]: \n    First para.\n\n    ```\n    code\n    ```\n\n    After code.\n"
        )
        assert_idempotent(md)

    def test_mixed_inline_and_block_footnotes(self) -> None:
        md = "Regular footnote[^1] and inline^[This is inline].\n\n[^1]: \n    Regular note.\n"
        assert_idempotent(md)


# ═══════════════════════════════════════════════════════════════════
# Math edge cases
# ═══════════════════════════════════════════════════════════════════


class TestMathEdgeCases:
    def test_math_with_escaped_dollars(self) -> None:
        md = "This costs \\$100 but $x = y$ is math.\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_math_with_escaped_dollars_parity(self) -> None:
        md = "This costs \\$100 but $x = y$ is math.\n"
        assert_pandoc_parity(md)

    def test_display_math_multiline(self) -> None:
        md = "$$\n\\begin{aligned}\nx &= y \\\\\\\\\nz &= w\n\\end{aligned}\n$$\n"
        assert_idempotent(md)

    def test_multiple_inline_math(self) -> None:
        md = "We have $x = 1$ and $y = 2$ and $z = x + y$.\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_multiple_inline_math_parity(self) -> None:
        md = "We have $x = 1$ and $y = 2$ and $z = x + y$.\n"
        assert_pandoc_parity(md)

    def test_inline_math_complex(self) -> None:
        md = "The equation $\\sum_{i=1}^{n} x_i = S$ is well known.\n"
        assert_idempotent(md)


# ═══════════════════════════════════════════════════════════════════
# Div edge cases
# ═══════════════════════════════════════════════════════════════════


class TestDivEdgeCases:
    def test_div_with_list(self) -> None:
        md = "::: {.note}\n\n- Item 1\n- Item 2\n\n:::\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_div_with_list_parity(self) -> None:
        md = "::: {.note}\n\n- Item 1\n- Item 2\n\n:::\n"
        assert_pandoc_parity(md)

    def test_div_with_code(self) -> None:
        md = "::: {.note}\n\n```python\nprint('hello')\n```\n\n:::\n"
        assert_idempotent(md)

    def test_deeply_nested_divs(self) -> None:
        md = (
            "::::: {.outer}\n\n:::: {.middle}\n\n::: {.inner}\n\nContent.\n\n:::\n\n::::\n\n:::::\n"
        )
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_deeply_nested_divs_parity(self) -> None:
        md = (
            "::::: {.outer}\n\n:::: {.middle}\n\n::: {.inner}\n\nContent.\n\n:::\n\n::::\n\n:::::\n"
        )
        assert_pandoc_parity(md)


# ═══════════════════════════════════════════════════════════════════
# Table edge cases
# ═══════════════════════════════════════════════════════════════════


class TestTableEdgeCases:
    def test_table_with_empty_cells(self) -> None:
        md = "| A   | B   |\n| --- | --- |\n| 1   |     |\n|     | 2   |\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_table_with_empty_cells_parity(self) -> None:
        md = "| A   | B   |\n| --- | --- |\n| 1   |     |\n|     | 2   |\n"
        assert_pandoc_parity(md)

    def test_table_single_column(self) -> None:
        md = "| A   |\n| --- |\n| 1   |\n"
        assert_idempotent(md)

    def test_table_with_inline_formatting(self) -> None:
        md = "| **Bold** | *Italic* | `Code` |\n| -------- | -------- | ------ |\n| a        | b        | c      |\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_table_with_inline_formatting_parity(self) -> None:
        md = "| **Bold** | *Italic* | `Code` |\n| -------- | -------- | ------ |\n| a        | b        | c      |\n"
        assert_pandoc_parity(md)

    def test_table_all_alignments(self) -> None:
        md = (
            "| Right | Left | Default | Center |\n"
            "| ----: | :--- | ------- | :----: |\n"
            "| 12    | 12   | 12      | 12     |\n"
        )
        assert_idempotent(md)


# ═══════════════════════════════════════════════════════════════════
# List edge cases
# ═══════════════════════════════════════════════════════════════════


class TestListEdgeCases:
    def test_list_with_initials(self) -> None:
        """Ensure N. T. Wright doesn't get parsed as a fancy list."""
        md = "- N. T. Wright\n"
        assert_idempotent(md)

    def test_ordered_list_startnum(self) -> None:
        md = "9)  Ninth\n10)  Tenth\n11)  Eleventh\n"
        assert_idempotent(md)

    def test_alpha_list_ambiguity(self) -> None:
        md = "A.  test\nB.  test2\nC.  test3\n"
        assert_idempotent(md)

    def test_roman_numeral_list(self) -> None:
        md = "(i)  first\n(ii) second\n"
        assert_idempotent(md)

    def test_list_with_continuation_paragraph(self) -> None:
        md = "- First item.\n\n  Second paragraph of first item.\n\n- Second item.\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_list_with_continuation_parity(self) -> None:
        md = "- First item.\n\n  Second paragraph of first item.\n\n- Second item.\n"
        assert_pandoc_parity(md)

    def test_list_with_nested_code(self) -> None:
        md = "1. Item with code:\n\n   ```\n   code block\n   ```\n\n2. Next item.\n"
        assert_idempotent(md)

    def test_nested_mixed_list(self) -> None:
        md = "1. ordered item\n   - nested bullet\n   - another bullet\n2. second ordered\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_nested_mixed_list_parity(self) -> None:
        md = "1. ordered item\n   - nested bullet\n   - another bullet\n2. second ordered\n"
        assert_pandoc_parity(md)

    def test_hash_list(self) -> None:
        md = "#. one\n#. two\n#. three\n"
        assert_idempotent(md)

    def test_task_list(self) -> None:
        md = "- [ ] an unchecked task list item\n- [x] checked item\n"
        assert_idempotent(md)


# ═══════════════════════════════════════════════════════════════════
# Definition list edge cases
# ═══════════════════════════════════════════════════════════════════


class TestDefListEdgeCases:
    def test_deflist_with_code(self) -> None:
        md = (
            "Term 1\n\n:   Definition 1\n\n"
            "Term 2 with *inline markup*\n\n:   Definition 2\n\n"
            "    ```\n      { some code, part of Definition 2 }\n    ```\n\n"
            "    Third paragraph of definition 2.\n"
        )
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_deflist_parity(self) -> None:
        md = (
            "Term 1\n\n:   Definition 1\n\n"
            "Term 2 with *inline markup*\n\n:   Definition 2\n\n"
            "    ```\n      { some code, part of Definition 2 }\n    ```\n\n"
            "    Third paragraph of definition 2.\n"
        )
        assert_pandoc_parity(md)

    def test_deflist_multiple_definitions(self) -> None:
        md = "Term 1\n:   Definition 1a\n:   Definition 1b\n\nTerm 2\n:   Definition 2\n"
        assert_idempotent(md)

    def test_deflist_tight(self) -> None:
        md = "Term 1\n:   Def 1\n\nTerm 2\n:   Def 2\n"
        assert_idempotent(md)


# ═══════════════════════════════════════════════════════════════════
# Line block edge cases
# ═══════════════════════════════════════════════════════════════════


class TestLineBlockEdgeCases:
    def test_line_block_with_formatting(self) -> None:
        md = "| This line has *emphasis* and **bold**.\n| This line has `code` in it.\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_line_block_formatting_parity(self) -> None:
        md = "| This line has *emphasis* and **bold**.\n| This line has `code` in it.\n"
        assert_pandoc_parity(md)

    def test_line_block_no_wrap(self) -> None:
        """Line blocks should never be wrapped even with wrap=80."""
        md = (
            "| This is a very very very very very very very very very very "
            "very very very long line block\n"
            "| And it should not be wrapped at all even if wrap is eighty\n"
        )
        result = _fmt(md, wrap=80)
        assert result == md

    def test_line_block_preserved_spaces(self) -> None:
        md = "|    Indented line\n| Normal line\n|      More indented\n"
        assert_idempotent(md)


# ═══════════════════════════════════════════════════════════════════
# Code block edge cases
# ═══════════════════════════════════════════════════════════════════


class TestCodeBlockEdgeCases:
    def test_code_block_with_attrs(self) -> None:
        md = '```{#mycode .haskell .numberLines startFrom="100"}\nqsort [] = []\n```\n'
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_code_block_attrs_parity(self) -> None:
        md = '```{#mycode .haskell .numberLines startFrom="100"}\nqsort [] = []\n```\n'
        assert_pandoc_parity(md)

    def test_code_with_language_shortcut(self) -> None:
        md = "```haskell\nqsort [] = []\n```\n"
        assert_idempotent(md)

    def test_code_language_plus_attrs(self) -> None:
        md = "```haskell {.numberLines}\nqsort [] = []\n```\n"
        assert_idempotent(md)

    def test_raw_attr_block(self) -> None:
        md = "```{=ms}\n.MYMACRO\nblah blah\n```\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_raw_attr_block_parity(self) -> None:
        md = "```{=ms}\n.MYMACRO\nblah blah\n```\n"
        assert_pandoc_parity(md)

    def test_raw_attr_inline(self) -> None:
        md = "This is `<a>html</a>`{=html}\n"
        assert_idempotent(md)


# ═══════════════════════════════════════════════════════════════════
# Link edge cases
# ═══════════════════════════════════════════════════════════════════


class TestLinkEdgeCases:
    def test_link_with_title(self) -> None:
        md = '[link](https://example.com "My Title")\n'
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_link_with_title_parity(self) -> None:
        md = '[link](https://example.com "My Title")\n'
        assert_pandoc_parity(md)

    def test_automatic_link(self) -> None:
        md = "<https://google.com>\n"
        assert_idempotent(md)

    def test_email_link(self) -> None:
        md = "<sam@green.eggs.ham>\n"
        assert_idempotent(md)

    def test_reference_link(self) -> None:
        md = "See [my website].\n\n[my website]: http://foo.bar.baz\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_reference_link_parity(self) -> None:
        md = "See [my website].\n\n[my website]: http://foo.bar.baz\n"
        assert_pandoc_parity(md)


# ═══════════════════════════════════════════════════════════════════
# Heading edge cases
# ═══════════════════════════════════════════════════════════════════


class TestHeadingEdgeCases:
    def test_heading_with_link(self) -> None:
        md = "# A heading with a [link](/url) and *emphasis*\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_heading_with_link_parity(self) -> None:
        md = "# A heading with a [link](/url) and *emphasis*\n"
        assert_pandoc_parity(md)

    def test_heading_unnumbered(self) -> None:
        md = "# My heading {-}\n"
        assert_idempotent(md)

    def test_heading_multi_attrs(self) -> None:
        md = '### Third heading {#bar .class1 .class2 key="value"}\n'
        assert_idempotent(md)


# ═══════════════════════════════════════════════════════════════════
# Frontmatter edge cases
# ═══════════════════════════════════════════════════════════════════


class TestFrontmatterEdgeCases:
    def test_yaml_with_lists(self) -> None:
        md = (
            "---\n"
            "title: 'Title: with colon'\n"
            "author:\n"
            "- Author One\n"
            "- Author Two\n"
            "keywords: [nothing, nothingness]\n"
            "---\n\n"
            "Content.\n"
        )
        assert_idempotent(md)

    def test_yaml_simple(self) -> None:
        md = "---\ntitle: Test Document\nauthor: Jane Doe\ndate: 2024-01-01\n---\n\nContent.\n"
        assert_idempotent(md)


# ═══════════════════════════════════════════════════════════════════
# Backslash escape edge cases
# ═══════════════════════════════════════════════════════════════════


class TestEscapeEdgeCases:
    def test_escaped_asterisks(self) -> None:
        md = "\\*not emphasis\\*\n"
        assert_idempotent(md)

    def test_escaped_backtick_in_code(self) -> None:
        md = "This is a backslash followed by an asterisk: `\\*`.\n"
        assert_idempotent(md)

    def test_escaped_dollar(self) -> None:
        md = "This costs \\$100.\n"
        assert_idempotent(md)

    def test_escaped_dollar_pair(self) -> None:
        md = "This costs \\$100 and that costs \\$200 in total.\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_escaped_dollar_parity(self) -> None:
        md = "This costs \\$100 and that costs \\$200 in total.\n"
        assert_pandoc_parity(md)

    def test_escaped_newline_hard_break(self) -> None:
        md = "A line with a backslash\\\nhard line break.\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_escaped_newline_parity(self) -> None:
        md = "A line with a backslash\\\nhard line break.\n"
        assert_pandoc_parity(md)


# ═══════════════════════════════════════════════════════════════════
# Obsidian/Wikilink edge cases
# ═══════════════════════════════════════════════════════════════════


class TestObsidianEdgeCases:
    def test_wikilink_in_blockquote(self) -> None:
        md = "> See [[page]] for details.\n"
        assert_idempotent(md)

    def test_embed_in_list_item(self) -> None:
        md = "- Item with ![[embed]]\n"
        assert_idempotent(md)

    def test_wikilink_with_alias(self) -> None:
        md = "[[page|display text]]\n"
        assert_idempotent(md)

    def test_embed_with_params(self) -> None:
        md = "![[image.png|400]]\n"
        assert_idempotent(md)

    def test_callout_with_embed(self) -> None:
        md = "> [!info]+\n> Inbox Items ![[inbox.base]]\n"
        assert_idempotent(md)


# ═══════════════════════════════════════════════════════════════════
# Cross-feature combination tests
# ═══════════════════════════════════════════════════════════════════


class TestCrossFeatureCombinations:
    """Tests combining multiple pandoc features together."""

    def test_div_with_footnote(self) -> None:
        md = "::: {.note}\n\nText with footnote[^1].\n\n:::\n\n[^1]: \n    Note content.\n"
        assert_idempotent(md)

    def test_list_with_math(self) -> None:
        md = "1. The equation $E = mc^2$\n2. And also $F = ma$\n"
        assert_idempotent(md)

    def test_table_with_emphasis(self) -> None:
        md = "| **Bold** | *Italic* |\n| -------- | -------- |\n| a        | b        |\n"
        assert_idempotent(md)

    def test_blockquote_with_citation(self) -> None:
        md = "> As stated in [@smith04].\n"
        assert_idempotent(md)

    def test_heading_with_sub_sup(self) -> None:
        md = "# H~2~O and 2^10^\n"
        assert_idempotent(md)

    def test_list_with_span(self) -> None:
        md = "- [highlight]{.mark}\n- [small]{.smallcaps}\n"
        assert_idempotent(md)

    def test_div_with_table(self) -> None:
        md = "::: {.data}\n\n| A   | B   |\n| --- | --- |\n| 1   | 2   |\n\n:::\n"
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_div_with_table_parity(self) -> None:
        md = "::: {.data}\n\n| A   | B   |\n| --- | --- |\n| 1   | 2   |\n\n:::\n"
        assert_pandoc_parity(md)

    def test_footnote_with_emphasis_and_code(self) -> None:
        md = "Text[^1]\n\n[^1]: \n    This has *emphasis* and `code` and **bold**.\n"
        assert_idempotent(md)

    def test_complex_paragraph(self) -> None:
        """A paragraph using many inline features at once."""
        md = (
            "This has *emphasis*, **strong**, ~~strikeout~~, "
            "H~2~O, 2^10^, `code`, [span]{.mark}, "
            "and a [link](/url).\n"
        )
        assert_idempotent(md)

    @PANDOC_SKIP
    def test_complex_paragraph_parity(self) -> None:
        md = (
            "This has *emphasis*, **strong**, ~~strikeout~~, "
            "H~2~O, 2^10^, `code`, [span]{.mark}, "
            "and a [link](/url).\n"
        )
        assert_pandoc_parity(md)


# ═══════════════════════════════════════════════════════════════════
# Wrap mode edge cases
# ═══════════════════════════════════════════════════════════════════


class TestWrapEdgeCases:
    """Tests that verify wrapping doesn't break formatting."""

    def test_wrap_preserves_math(self) -> None:
        md = "This is a long paragraph with inline math $x = y + z$ that should not break the math delimiters.\n"
        result = _fmt(md, wrap=40)
        assert "$x = y + z$" in result
        assert_idempotent(md, wrap=40)

    def test_wrap_preserves_citation(self) -> None:
        md = "This is a long paragraph with a citation [@smith04] that should not break.\n"
        result = _fmt(md, wrap=40)
        assert "[@smith04]" in result
        assert_idempotent(md, wrap=40)

    def test_wrap_preserves_span(self) -> None:
        md = "This is a long paragraph with a [span]{.mark} that should not break.\n"
        result = _fmt(md, wrap=40)
        assert "[span]{.mark}" in result
        assert_idempotent(md, wrap=40)

    def test_wrap_preserves_wikilink(self) -> None:
        md = "This is a long paragraph with a [[wikilink]] that should not break.\n"
        result = _fmt(md, wrap=40)
        assert "[[wikilink]]" in result
        assert_idempotent(md, wrap=40)

    def test_wrap_preserves_sub_sup(self) -> None:
        md = "This is a long paragraph with H~2~O subscript and 2^10^ superscript in it.\n"
        result = _fmt(md, wrap=40)
        assert "H~2~O" in result
        assert "2^10^" in result
        assert_idempotent(md, wrap=40)

    def test_wrap_preserves_strikeout(self) -> None:
        md = "This is a long paragraph with ~~strikeout text~~ that should not break.\n"
        result = _fmt(md, wrap=40)
        assert "~~strikeout text~~" in result
        assert_idempotent(md, wrap=40)

    def test_wrap_preserves_footnote_ref(self) -> None:
        md = "This is a long paragraph with a footnote[^1] reference.\n\n[^1]: \n    Note.\n"
        result = _fmt(md, wrap=40)
        assert "[^1]" in result
        assert_idempotent(md, wrap=40)

    def test_wrap_preserves_embed(self) -> None:
        md = "This is a long paragraph with an embed ![[file]] that should not break.\n"
        result = _fmt(md, wrap=40)
        assert "![[file]]" in result
        assert_idempotent(md, wrap=40)
