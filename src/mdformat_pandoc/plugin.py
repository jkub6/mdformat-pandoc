from collections.abc import Callable

from markdown_it import MarkdownIt
from markdown_it.rules_block.state_block import StateBlock
from markdown_it.rules_inline import StateInline
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

from mdformat_pandoc.features.custom_labels import custom_label_plugin
from mdformat_pandoc.features.divs import PANDOC_DIV, pandoc_div_plugin
from mdformat_pandoc.features.fancy_lists import fancy_lists_plugin
from mdformat_pandoc.features.line_blocks import pandoc_line_block_plugin
from mdformat_pandoc.features.obsidian_embeds import obsidian_embed_plugin
from mdformat_pandoc.features.sub_sup import subscript_plugin, superscript_plugin
from mdformat_pandoc.features.wikilinks import wikilink_plugin

RuleFunc = Callable[[StateBlock, int, int, bool], bool]


def update_mdit(mdit: MarkdownIt) -> None:
    """Update the markdown-it parser to handle pandoc fenced divs and other extensions."""
    # Enable defaults that match Pandoc
    mdit.enable("table")
    mdit.enable("strikethrough")

    # Custom plugins
    mdit.block.ruler.before("fence", PANDOC_DIV, pandoc_div_plugin)
    mdit.use(fancy_lists_plugin)
    mdit.use(obsidian_embed_plugin)  # Must be before image rule
    mdit.use(wikilink_plugin)  # Must be before link rule
    mdit.use(superscript_plugin)

    # Wrap the standard list rule to track silent mode for monkeypatches
    for _i, rule in enumerate(mdit.block.ruler.__rules__):
        if rule.name == "list":

            def make_wrapper(orig: RuleFunc) -> RuleFunc:
                def wrapped_list(
                    state: StateBlock,
                    start_line: int,
                    end_line: int,
                    silent: bool,  # noqa: FBT001
                ) -> bool:
                    state._is_silent = silent  # type: ignore[attr-defined]
                    try:
                        return orig(state, start_line, end_line, silent)
                    finally:
                        if hasattr(state, "_is_silent"):
                            del state._is_silent

                return wrapped_list

            rule.fn = make_wrapper(rule.fn)

    # External plugins matching Pandoc syntax
    mdit.use(pandoc_line_block_plugin)
    mdit.use(footnote_plugin)
    mdit.use(deflist_plugin)
    mdit.use(front_matter_plugin)
    mdit.use(subscript_plugin)
    mdit.use(custom_label_plugin)
    # mdit-py-plugins.tasklists renders html <input> tags effectively suitable
    # for viewing but not formatting.
    # We prefer keeping them as text '[ ]' which standard mdit parser handles
    # fine as plain content.
    # Pandoc supports both $..$ and $$..$$ (dollarmath) and generic tex math
    # dollarmath usually covers most use cases well
    mdit.use(dollarmath_plugin)

    # Pandoc supports escaped spaces '\ '
    def escaped_space(state: StateInline, silent: bool) -> bool:  # noqa: FBT001
        if (
            state.pos + 1 < state.posMax
            and state.src[state.pos] == "\\"
            and state.src[state.pos + 1] == " "
        ):
            if not silent:
                token = state.push("text", "", 0)
                token.content = " "
            state.pos += 2
            return True
        return False

    mdit.inline.ruler.before("escape", "escaped_space", escaped_space)
