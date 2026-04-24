from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from mdformat.renderer import RenderContext, RenderTreeNode

    Render = Callable[[RenderTreeNode, RenderContext], str]
else:
    Render = Any

from mdformat_pandoc.features import custom_labels
from mdformat_pandoc.features.divs import render_pandoc_div
from mdformat_pandoc.features.footnotes import (
    render_footnote_anchor,
    render_footnote_block_open,
    render_footnote_open,
    render_footnote_ref,
)
from mdformat_pandoc.features.frontmatter import render_front_matter
from mdformat_pandoc.features.lists import (
    render_dd_open,
    render_dl_open,
    render_dt_open,
    render_list_item,
    render_ordered_list,
)
from mdformat_pandoc.features.math import (
    render_math_block,
    render_math_inline,
)
from mdformat_pandoc.features.obsidian_embeds import render_obsidian_embed
from mdformat_pandoc.features.sub_sup import render_sub, render_sup
from mdformat_pandoc.features.tables import render_cell, render_table
from mdformat_pandoc.features.wikilinks import render_wikilink
from mdformat_pandoc.utils import PANDOC_DIV


def render_strikethrough(node: RenderTreeNode, context: RenderContext) -> str:
    """Render strikethrough: ~~text~~"""
    content = "".join(child.render(context) for child in node.children)
    return f"~~{content}~~"


# Renderer mapping for mdformat - use dict for .update() support
RENDERERS: dict[str, Render] = {
    PANDOC_DIV: render_pandoc_div,
    "front_matter": render_front_matter,
    "footnote_ref": render_footnote_ref,
    "footnote_block": render_footnote_block_open,
    "footnote": render_footnote_open,
    "footnote_anchor": render_footnote_anchor,
    "dl": render_dl_open,
    "dt": render_dt_open,
    "dd": render_dd_open,
    "ordered_list": render_ordered_list,
    "list_item": render_list_item,
    "math_inline": render_math_inline,
    "math_block": render_math_block,
    "table": render_table,
    "th": render_cell,
    "td": render_cell,
    "sub": render_sub,
    "sup": render_sup,
    "s": render_strikethrough,
    "custom_label_list": custom_labels.render_custom_label_list,
    "custom_label_item": custom_labels.render_custom_label_item,
    "wikilink": render_wikilink,
    "obsidian_embed": render_obsidian_embed,
}
