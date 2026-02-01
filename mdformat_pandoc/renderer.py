
from __future__ import annotations
from typing import TYPE_CHECKING
from collections.abc import Mapping
from mdformat.renderer.typing import Render

from mdformat_pandoc.utils import PANDOC_DIV
from mdformat_pandoc.features.divs import render_pandoc_div
from mdformat_pandoc.features.frontmatter import render_front_matter
from mdformat_pandoc.features.footnotes import (
    render_footnote_ref,
    render_footnote_block_open,
    render_footnote_open,
    render_footnote_anchor,
)
from mdformat_pandoc.features.lists import (
    render_dl_open,
    render_dt_open,
    render_dd_open,
)
from mdformat_pandoc.features.math import (
    render_math_inline,
    render_math_block,
)
from mdformat_pandoc.features.tables import render_table, render_cell

if TYPE_CHECKING:
    from collections.abc import Mapping
    from mdformat.renderer.typing import Render

# Renderer mapping for mdformat
RENDERERS: Mapping[str, Render] = {
    PANDOC_DIV: render_pandoc_div,
    "front_matter": render_front_matter,
    "footnote_ref": render_footnote_ref,
    "footnote_block": render_footnote_block_open,
    "footnote": render_footnote_open,
    "footnote_anchor": render_footnote_anchor,
    "dl": render_dl_open,
    "dt": render_dt_open,
    "dd": render_dd_open,
    "math_inline": render_math_inline,
    "math_block": render_math_block,
    "table": render_table,
    "th": render_cell,
    "td": render_cell,
    # Note: Header attributes and generic attributes are currently handled 
    # as plain text by the default renderer, which preserves them perfectly 
    # for Pandoc compatibility without risking data loss during parsing.
}
