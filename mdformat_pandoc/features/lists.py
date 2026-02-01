import textwrap
from mdformat.renderer import RenderContext, RenderTreeNode

def render_dl_open(node: RenderTreeNode, context: RenderContext) -> str:
    """Render definition list.
    
    Join children with newlines.
    """
    return "\n\n".join(child.render(context) for child in node.children)

def render_dt_open(node: RenderTreeNode, context: RenderContext) -> str:
    """Render generic definition term."""
    return "".join(child.render(context) for child in node.children)

def render_dd_open(node: RenderTreeNode, context: RenderContext) -> str:
    """Render definition description.
    
    Needs to start with : and indentation.
    Pandoc syntax:
    Term
    :   Definition
    """
    content = "\n\n".join(child.render(context) for child in node.children)
    # Indent content by 4 spaces
    indented = textwrap.indent(content, "    ")
    # Replace first 4 spaces with ":   "
    # But wait, textwrap.indent indents EVERY line.
    # The first line should be prefixed with ":   ".
    # And we don't want to indent empty lines usually?
    # Simple approach:
    # 1. Indent everything.
    # 2. Replace first 4 chars of result (if they are spaces) with ":   "
    if not indented:
        return ":   "
    return ":   " + indented[4:] if indented.startswith("    ") else ":   " + indented
