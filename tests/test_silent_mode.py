import markdown_it

from mdformat_pandoc.plugin import update_mdit


def test_silent_mode_infinite_loop():
    """Test that spans and citations properly advance state.pos in silent mode.

    If they do not, this test will hang infinitely.
    Wrapping them in a link triggers silent mode parsing.
    """
    md = markdown_it.MarkdownIt()
    update_mdit(md)

    # This will hang if the bug is present
    md.parseInline("[[span]{.class}](http://example.com)")
    md.parseInline("[[@citation]](http://example.com)")
