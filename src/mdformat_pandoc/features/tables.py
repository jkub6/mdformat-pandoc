from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from mdformat.renderer import RenderContext, RenderTreeNode

    Render = Callable[[RenderTreeNode, RenderContext], str]


def _get_cell_alignment(node: RenderTreeNode) -> str:
    """Get alignment from style attribute.

    Returns 'left', 'right', 'center', or ''.
    """
    style_attr = node.attrs.get("style", "")
    style = str(style_attr) if style_attr else ""

    if "text-align:center" in style:
        return "center"
    if "text-align:right" in style:
        return "right"
    if "text-align:left" in style:
        return "left"
    return ""


def render_cell(node: RenderTreeNode, context: RenderContext) -> str:
    """Render a table cell (th/td).

    This acts as a transparent container, rendering its children.
    """
    # Simply render children. mdformat's default traversal logic isn't easily accessible
    # as a single function, but usually we iterate children.
    return "".join(child.render(context) for child in node.children)


def _render_cell_content(node: RenderTreeNode, context: RenderContext) -> str:
    """Render the content of a cell (th/td)."""
    # We want to render the inline content of the cell.
    return node.render(context).strip()


def _extract_table_data(
    node: RenderTreeNode, context: RenderContext
) -> tuple[list[str], list[str], list[list[str]]]:
    """Extract headers, alignments, and rows from table node."""
    headers: list[str] = []
    alignments: list[str] = []
    rows: list[list[str]] = []

    thead = next((c for c in node.children if c.type == "thead"), None)
    tbody = next((c for c in node.children if c.type == "tbody"), None)

    # Process Header
    if thead:
        for tr in (c for c in thead.children if c.type == "tr"):
            for th in (c for c in tr.children if c.type in ("th", "td")):
                headers.append(_render_cell_content(th, context))
                alignments.append(_get_cell_alignment(th))

    # Process Body
    if tbody:
        for tr in (c for c in tbody.children if c.type == "tr"):
            row_data = [
                _render_cell_content(td, context) for td in tr.children if td.type in ("td", "th")
            ]
            rows.append(row_data)

    return headers, alignments, rows


def _render_table_row(row: list[str], col_widths: list[int]) -> str:
    """Render a single table row."""
    row_line = "|"
    num_cols = len(col_widths)
    num_row_cells = len(row)

    for i in range(num_cols):
        c_text = row[i] if i < num_row_cells else ""
        c_width = col_widths[i]
        row_line += f" {c_text.ljust(c_width)} |"
    return row_line


def _calculate_col_widths(
    headers: list[str], rows: list[list[str]], alignments: list[str]
) -> list[int]:
    """Calculate and normalize column widths."""
    col_widths = [len(h) for h in headers]

    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(cell))
            else:
                # Row has more cells than header? Extend
                col_widths.append(len(cell))
                # Also extend headers/alignments if needed
                if len(headers) < len(col_widths):
                    headers.append("")
                    alignments.append("")

    # Ensure min width of 3 for delimiter generation
    min_delim_width = 3
    return [max(w, min_delim_width) for w in col_widths]


def _render_delimiter(align: str, width: int) -> str:
    """Render a table delimiter cell."""
    if align == "center":
        # :---:
        return ":" + "-" * (width - 2) + ":"
    if align == "right":
        # ---:
        return "-" * (width - 1) + ":"
    if align == "left":
        # :---
        return ":" + "-" * (width - 1)
    # ---
    return "-" * width


def render_table(node: RenderTreeNode, context: RenderContext) -> str:
    """Render a Pipe Table."""
    # 1. Extract Data
    headers, alignments, rows = _extract_table_data(node, context)

    if not headers and not rows:
        return ""

    # 2. Normalize Data if headerless
    if not headers and rows:
        num_columns = len(rows[0])
        headers = [""] * num_columns
        alignments = [""] * num_columns

    # 3. Calculate Column Widths
    col_widths = _calculate_col_widths(headers, rows, alignments)

    # 4. Generate Output
    lines = []

    # Header Row
    lines.append(_render_table_row(headers, col_widths))

    # Delimiter Row
    delim_cells = [_render_delimiter(align, col_widths[i]) for i, align in enumerate(alignments)]
    lines.append("| " + " | ".join(delim_cells) + " |")

    # Body Rows
    lines.extend(_render_table_row(row, col_widths) for row in rows)

    return "\n".join(lines)
