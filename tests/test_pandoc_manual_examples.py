"""Pandoc manual examples test suite.

Tests extracted directly from pandoc-manual.txt to ensure mdformat-pandoc
handles every documented pandoc markdown syntax correctly.

Each test verifies:
  1. Idempotency: format(format(x)) == format(x)
  2. HTML parity (where applicable): pandoc_html(x) == pandoc_html(format(x))
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
# Pandoc Manual §4.1 — Paragraphs
# ═══════════════════════════════════════════════════════════════════

PARAGRAPH_EXAMPLES = [
    pytest.param(
        "A simple paragraph of text.\n",
        id="para-simple",
    ),
    pytest.param(
        "First paragraph.\n\nSecond paragraph.\n",
        id="para-two-paragraphs",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.1.1 — Escaped Line Breaks
# ═══════════════════════════════════════════════════════════════════

ESCAPED_LINE_BREAK_EXAMPLES = [
    pytest.param(
        "A backslash\\\nhard line break.\n",
        id="escaped-line-break",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.2 — Headings (ATX-style)
# ═══════════════════════════════════════════════════════════════════

HEADING_EXAMPLES = [
    pytest.param(
        "## A level-two heading\n",
        id="heading-atx-level2",
    ),
    pytest.param(
        "### A level-three heading\n",
        id="heading-atx-level3",
    ),
    pytest.param(
        "# A level-one heading with a [link](/url) and *emphasis*\n",
        id="heading-with-inline-formatting",
    ),
    pytest.param(
        "# My heading {#foo}\n",
        id="heading-with-id",
    ),
    pytest.param(
        "# My heading {-}\n",
        id="heading-unnumbered",
    ),
    pytest.param(
        "# My heading {.unnumbered}\n",
        id="heading-unnumbered-class",
    ),
    pytest.param(
        "# My heading {.unnumbered .unlisted}\n",
        id="heading-unlisted",
    ),
    pytest.param(
        '### Third heading {#bar .class1 .class2 key="value"}\n',
        id="heading-multi-attrs",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.3 — Block Quotations
# ═══════════════════════════════════════════════════════════════════

BLOCKQUOTE_EXAMPLES = [
    pytest.param(
        "> This is a block quote. This\n> paragraph has two lines.\n>\n"
        "> 1. This is a list inside a block quote.\n> 2. Second item.\n",
        id="blockquote-with-list",
    ),
    pytest.param(
        "> This is a block quote.\n>\n> > A block quote within a block quote.\n",
        id="blockquote-nested",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.4 — Verbatim (Code) Blocks
# ═══════════════════════════════════════════════════════════════════

CODE_EXAMPLES = [
    pytest.param(
        "```\nif (a > 3) {\n  moveShip(5 * gravity, DOWN);\n}\n```\n",
        id="code-fenced-backtick",
    ),
    pytest.param(
        "~~~\nif (a > 3) {\n  moveShip(5 * gravity, DOWN);\n}\n~~~\n",
        id="code-fenced-tilde",
    ),
    pytest.param(
        '```{#mycode .haskell .numberLines startFrom="100"}\nqsort [] = []\n```\n',
        id="code-fenced-attrs",
    ),
    pytest.param(
        "```haskell\nqsort [] = []\n```\n",
        id="code-language-shortcut",
    ),
    pytest.param(
        "```haskell {.numberLines}\nqsort [] = []\n```\n",
        id="code-language-plus-attrs",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.5 — Line Blocks
# ═══════════════════════════════════════════════════════════════════

LINE_BLOCK_EXAMPLES = [
    pytest.param(
        "| The limerick packs laughs anatomical\n"
        "| In space that is quite economical.\n"
        "|    But the good ones I've seen\n"
        "|    So seldom are clean\n"
        "| And the clean ones so seldom are comical\n",
        id="line-block-verse",
    ),
    pytest.param(
        "| 200 Main St.\n| Berkeley, CA 94718\n",
        id="line-block-address",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.6 — Lists
# ═══════════════════════════════════════════════════════════════════

LIST_EXAMPLES = [
    pytest.param(
        "- one\n- two\n- three\n",
        id="bullet-list-compact",
    ),
    pytest.param(
        "- one\n\n- two\n\n- three\n",
        id="bullet-list-loose",
    ),
    pytest.param(
        "- fruits\n  - apples\n    - macintosh\n    - red delicious\n"
        "  - pears\n  - peaches\n- vegetables\n  - broccoli\n  - chard\n",
        id="bullet-list-nested",
    ),
    pytest.param(
        "1. one\n2. two\n3. three\n",
        id="ordered-list-basic",
    ),
    pytest.param(
        "9)  Ninth\n10)  Tenth\n11)  Eleventh\n",
        id="ordered-list-startnum",
    ),
    pytest.param(
        "#. one\n#. two\n#. three\n",
        id="fancy-list-hash",
    ),
    pytest.param(
        "- [ ] an unchecked task list item\n- [x] checked item\n",
        id="task-list",
    ),
    pytest.param(
        "(@good) This is a good example.\n(@bad) This is a bad example.\n",
        id="example-list-labeled",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.6.4 — Definition Lists
# ═══════════════════════════════════════════════════════════════════

DEFLIST_EXAMPLES = [
    pytest.param(
        "Term 1\n\n:   Definition 1\n\n"
        "Term 2 with *inline markup*\n\n:   Definition 2\n\n"
        "    ```\n      { some code, part of Definition 2 }\n    ```\n\n"
        "    Third paragraph of definition 2.\n",
        id="deflist-basic",
    ),
    pytest.param(
        "Term 1\n:   Definition 1\n\nTerm 2\n:   Definition 2\n",
        id="deflist-compact",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.7 — Horizontal Rules
# ═══════════════════════════════════════════════════════════════════

HRULE_EXAMPLES = [
    pytest.param(
        "______________________________________________________________________\n",
        id="hrule-normalized",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.8 — Tables
# ═══════════════════════════════════════════════════════════════════

TABLE_EXAMPLES = [
    pytest.param(
        "| Right | Left | Default | Center |\n"
        "| ----: | :--- | ------- | :----: |\n"
        "| 12    | 12   | 12      | 12     |\n"
        "| 123   | 123  | 123     | 123    |\n"
        "| 1     | 1    | 1       | 1      |\n",
        id="pipe-table-aligned",
    ),
    pytest.param(
        "| A   | B   |\n| --- | --- |\n| 1   | 2   |\n| 3   | 4   |\n",
        id="pipe-table-basic",
    ),
    pytest.param(
        "| A   |\n| --- |\n| 1   |\n",
        id="pipe-table-single-col",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.11 — Backslash Escapes
# ═══════════════════════════════════════════════════════════════════

ESCAPE_EXAMPLES = [
    pytest.param(
        "\\*not emphasis\\*\n",
        id="escape-asterisks",
    ),
    pytest.param(
        "This is a backslash followed by an asterisk: `\\*`.\n",
        id="escape-in-code",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.12 — Inline Formatting
# ═══════════════════════════════════════════════════════════════════

EMPHASIS_EXAMPLES = [
    pytest.param(
        "This text is _emphasized with underscores_, and this\nis *emphasized with asterisks*.\n",
        id="emphasis-basic",
    ),
    pytest.param(
        "This is **strong emphasis** and __with underscores__.\n",
        id="emphasis-strong",
    ),
    pytest.param(
        "feas*ible*, not feas*able*.\n",
        id="emphasis-intraword",
    ),
]


STRIKEOUT_EXAMPLES = [
    pytest.param(
        "This ~~is deleted text.~~\n",
        id="strikeout-basic",
    ),
]


SUB_SUP_EXAMPLES = [
    pytest.param(
        "H~2~O is a liquid. 2^10^ is 1024.\n",
        id="sub-sup-basic",
    ),
    pytest.param(
        "P~a\\ cat~ has an escaped space in subscript.\n",
        id="sub-escaped-space",
    ),
]


VERBATIM_EXAMPLES = [
    pytest.param(
        "What is the difference between `>>=` and `>>`?\n",
        id="verbatim-basic",
    ),
    pytest.param(
        "Here is a literal backtick `` ` ``.\n",
        id="verbatim-double-backtick",
    ),
    pytest.param(
        "`<$>`{.haskell}\n",
        id="verbatim-inline-code-attrs",
    ),
]


SMALL_CAPS_EXAMPLES = [
    pytest.param(
        "[Small caps]{.smallcaps}\n",
        id="small-caps",
    ),
    pytest.param(
        "[Underline]{.underline}\n",
        id="underline",
    ),
    pytest.param(
        "[Mark]{.mark}\n",
        id="highlight-mark",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.13 — Math
# ═══════════════════════════════════════════════════════════════════

MATH_EXAMPLES = [
    pytest.param(
        "Inline math: $E = mc^2$ is famous.\n",
        id="math-inline",
    ),
    pytest.param(
        "$$\n\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}\n$$\n",
        id="math-display",
    ),
    pytest.param(
        "We have $x = 1$ and $y = 2$ and $z = x + y$.\n",
        id="math-multiple-inline",
    ),
    pytest.param(
        "This costs \\$100 and that costs \\$200 in total.\n",
        id="math-escaped-dollar",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.14 — Raw HTML/TeX
# ═══════════════════════════════════════════════════════════════════

RAW_EXAMPLES = [
    pytest.param(
        "```{=ms}\n.MYMACRO\nblah blah\n```\n",
        id="raw-attribute-block",
    ),
    pytest.param(
        "This is `<a>html</a>`{=html}\n",
        id="raw-attribute-inline",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.15 — Links
# ═══════════════════════════════════════════════════════════════════

LINK_EXAMPLES = [
    pytest.param(
        "<https://google.com>\n",
        id="link-automatic",
    ),
    pytest.param(
        "<sam@green.eggs.ham>\n",
        id="link-email",
    ),
    pytest.param(
        "This is an [inline link](/url), and here's\n"
        '[one with a title](https://fsf.org "click here for a good time!").\n',
        id="link-inline",
    ),
    pytest.param(
        "See [my website].\n\n[my website]: http://foo.bar.baz\n",
        id="link-reference-shortcut",
    ),
    pytest.param(
        "See the [Introduction](#introduction).\n",
        id="link-internal",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.16 — Images
# ═══════════════════════════════════════════════════════════════════

IMAGE_EXAMPLES = [
    pytest.param(
        '![la lune](lalune.jpg "Voyage to the moon")\n',
        id="image-basic",
    ),
    pytest.param(
        "![This is the caption.](image.png)\n",
        id="image-figure",
    ),
    pytest.param(
        "![alt](foo.jpg){#id .class width=30 height=20px}\n",
        id="image-with-attrs",
    ),
    pytest.param(
        "![a](a.png) ![b](b.png)\n",
        id="image-multiple-inline",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.17 — Divs and Spans
# ═══════════════════════════════════════════════════════════════════

DIVS_SPANS_EXAMPLES = [
    pytest.param(
        "::: {#special .sidebar}\n\nHere is a paragraph.\n\nAnd another.\n\n:::\n",
        id="div-basic",
    ),
    pytest.param(
        ":::: {.Warning}\n\nThis is a warning.\n\n"
        "::: {.Danger}\n\nThis is a warning within a warning.\n\n:::\n\n::::\n",
        id="div-nested",
    ),
    pytest.param(
        '[This is *some text*]{.class key="val"}\n',
        id="span-basic",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.18 — Footnotes
# ═══════════════════════════════════════════════════════════════════

FOOTNOTE_EXAMPLES = [
    pytest.param(
        "Here is a footnote reference,[^1] and another.[^longnote]\n\n"
        "[^1]: \n    Here is the footnote.\n\n"
        "[^longnote]: \n    Here's one with multiple blocks.\n\n"
        "    Subsequent paragraphs are indented to show that they belong "
        "to the previous footnote.\n\n"
        "    ```\n    { some.code }\n    ```\n\n"
        "    The whole paragraph can be indented, or just the first line.\n",
        id="footnote-block",
    ),
    pytest.param(
        "Here is an inline\nnote.^[Inline notes are easier to write, since "
        "you don't have to pick an identifier and move down to type\nthe note.]\n",
        id="footnote-inline",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.19 — Citation Syntax
# ═══════════════════════════════════════════════════════════════════

CITATION_EXAMPLES = [
    pytest.param(
        "Blah blah [@doe99; @smith2000; @smith2004].\n",
        id="citation-multiple",
    ),
    pytest.param(
        "Blah blah [see @doe99, pp. 33-35 and *passim*; @smith04, chap. 1].\n",
        id="citation-with-locator",
    ),
    pytest.param(
        "Smith says blah [-@smith04].\n",
        id="citation-suppressed-author",
    ),
    pytest.param(
        "@smith04 says blah.\n",
        id="citation-author-in-text",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Pandoc Manual §4.10 — YAML Metadata
# ═══════════════════════════════════════════════════════════════════

META_EXAMPLES = [
    pytest.param(
        "---\ntitle: Test Document\nauthor: Jane Doe\ndate: 2024-01-01\n---\n\n"
        "Content after front matter.\n",
        id="yaml-simple",
    ),
    pytest.param(
        "---\ntitle: 'Title: with colon'\nauthor:\n- Author One\n- Author Two\n"
        "keywords: [nothing, nothingness]\n---\n\nContent.\n",
        id="yaml-complex",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Collect ALL examples
# ═══════════════════════════════════════════════════════════════════

ALL_EXAMPLES = (
    PARAGRAPH_EXAMPLES
    + ESCAPED_LINE_BREAK_EXAMPLES
    + HEADING_EXAMPLES
    + BLOCKQUOTE_EXAMPLES
    + CODE_EXAMPLES
    + LINE_BLOCK_EXAMPLES
    + LIST_EXAMPLES
    + DEFLIST_EXAMPLES
    + HRULE_EXAMPLES
    + TABLE_EXAMPLES
    + ESCAPE_EXAMPLES
    + EMPHASIS_EXAMPLES
    + STRIKEOUT_EXAMPLES
    + SUB_SUP_EXAMPLES
    + VERBATIM_EXAMPLES
    + SMALL_CAPS_EXAMPLES
    + MATH_EXAMPLES
    + RAW_EXAMPLES
    + LINK_EXAMPLES
    + IMAGE_EXAMPLES
    + DIVS_SPANS_EXAMPLES
    + FOOTNOTE_EXAMPLES
    + CITATION_EXAMPLES
    + META_EXAMPLES
)


class TestPandocManualIdempotency:
    """Verify format(format(x)) == format(x) for all pandoc manual examples."""

    @pytest.mark.parametrize("md", ALL_EXAMPLES)
    def test_idempotent(self, md: str) -> None:
        assert_idempotent(md)

    @pytest.mark.parametrize("md", ALL_EXAMPLES)
    def test_idempotent_wrap80(self, md: str) -> None:
        assert_idempotent(md, wrap=80)


@PANDOC_SKIP
class TestPandocManualParity:
    """Verify pandoc_html(x) == pandoc_html(format(x)) for pandoc manual examples."""

    @pytest.mark.parametrize("md", ALL_EXAMPLES)
    def test_parity(self, md: str) -> None:
        assert_pandoc_parity(md)

    @pytest.mark.parametrize("md", ALL_EXAMPLES)
    def test_parity_wrap80(self, md: str) -> None:
        assert_pandoc_parity(md, wrap=80)
