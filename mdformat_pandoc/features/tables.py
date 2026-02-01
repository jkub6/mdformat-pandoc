from typing import List, Optional, Tuple
from mdformat.renderer import RenderContext, RenderTreeNode

def _get_cell_alignment(node: RenderTreeNode) -> str:
    """Get alignment from style attribute.
    
    Returns 'left', 'right', 'center', or ''.
    """
    style = node.attrs.get("style", "")
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
    # We use empty string as separator for inline content?
    # Or usually mdformat handles spacing.
    # For inline content, usually we just join.
    return "".join(child.render(context) for child in node.children)

def _render_cell_content(node: RenderTreeNode, context: RenderContext) -> str:
    """Render the content of a cell (th/td)."""
    # We want to render the inline content of the cell.
    # We rely on mdformat's default behavior for children of th/td
    # which effectively renders the inline nodes.
    # Note: If th/td has block children, pipe tables might break.
    # Pandoc pipe tables usually expect inline content.
    return node.render(context).strip()

def render_table(node: RenderTreeNode, context: RenderContext) -> str:
    """Render a Pipe Table."""
    
    # 1. Extract Data
    headers: List[str] = []
    alignments: List[str] = []
    rows: List[List[str]] = []
    
    thead = None
    tbody = None
    
    for child in node.children:
        if child.type == "thead":
            thead = child
        elif child.type == "tbody":
            tbody = child
            
    # Process Header
    if thead:
        for tr in thead.children:
            if tr.type == "tr":
                for th in tr.children:
                    if th.type in ("th", "td"):
                        headers.append(_render_cell_content(th, context))
                        alignments.append(_get_cell_alignment(th))
    
    # Process Body
    if tbody:
        for tr in tbody.children:
            if tr.type == "tr":
                row_data = []
                for td in tr.children:
                    if td.type in ("td", "th"):
                        row_data.append(_render_cell_content(td, context))
                rows.append(row_data)

    if not headers and not rows:
        return ""

    # 2. Normalize Data
    num_columns = len(headers)
    if not num_columns and rows:
        num_columns = len(rows[0])
        # If no header, make empty headers? Pandoc pipe tables usually require headers or start with |
        # But valid pipe table must have a header line in most specs (including GFM).
        # Pandoc extensions might allow headerless, but let's assume we need one or at least the separator.
        headers = [""] * num_columns
        alignments = [""] * num_columns

    # 3. Calculate Column Widths
    # Minimum width is 3 (for '---') or length of content
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
    # Actually markdown-it-py alignment is ':-:', '---', '-:' (3 chars min)
    col_widths = [max(w, 3) for w in col_widths]

    # 4. Generate Output
    lines = []
    
    # Header Row
    header_line = "|"
    for i, h in enumerate(headers):
        header_line += f" {h.ljust(col_widths[i])} |"
    lines.append(header_line)
    
    # Delimiter Row
    delim_line = "|"
    for i, align in enumerate(alignments):
        width = col_widths[i]
        if align == "center":
            # :---:
            delim = ":" + "-" * (width - 2) + ":"
        elif align == "right":
            # ---:
            delim = "-" * (width - 1) + ":"
        elif align == "left":
            # :---
            delim = ":" + "-" * (width - 1)
        else:
            # ---
            delim = "-" * width
        
        delim_line += f" {delim} |"
    lines.append(delim_line)
    
    # Body Rows
    for row in rows:
        row_line = "|"
        for i, cell in enumerate(row):
            # Handle cells missing at end of row
            c_text = cell if i < len(row) else ""
            c_width = col_widths[i]
            row_line += f" {c_text.ljust(c_width)} |"
            
        # Fill missing columns in the row string
        remaining_cols = len(col_widths) - len(row)
        for i in range(remaining_cols):
             idx = len(row) + i
             c_width = col_widths[idx]
             row_line += f" {''.ljust(c_width)} |"

        lines.append(row_line)
        
    return "\n".join(lines)
