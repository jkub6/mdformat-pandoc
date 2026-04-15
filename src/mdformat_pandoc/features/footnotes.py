import textwrap

from mdformat.renderer import RenderContext, RenderTreeNode


def render_footnote_ref(node: RenderTreeNode, context: RenderContext) -> str:
    """Render footnote reference: [^label] or inline ^[content]"""
    # Detect inline footnote (it will have label=None)
    if node.meta.get("label") is None:
        # Find the root node to search for the footnote block
        root = node
        while root.parent:
            root = root.parent

        # Find the footnote block at the end of the root's children
        footnote_block = next((c for c in root.children if c.type == "footnote_block"), None)
        if footnote_block:
            # Find the footnote definition with the matching ID
            footnote_id = node.meta.get("id")
            fn_node = next(
                (c for c in footnote_block.children if c.meta.get("id") == footnote_id), None
            )
            if fn_node:
                # Render content of the footnote node
                # Pandoc inline footnotes usually contain inline content.
                # mdit-py-plugins parses them into a block (paragraph).
                # We strip the surrounding whitespace to make it an inline string.
                content = "\n\n".join(child.render(context) for child in fn_node.children)
                content = content.strip()
                return f"^[{content}]"

    label = node.meta.get("label", "")
    if not label:
        label = str(node.meta.get("id", ""))

    return f"[^{label}]"


def render_footnote_block_open(node: RenderTreeNode, context: RenderContext) -> str:
    """Render start of footnote block (bottom of doc)."""
    # Render children (the footnotes) separated by newlines
    # Filter out footnotes that were originally inline (label=None)
    footnotes = [c for c in node.children if c.meta.get("label") is not None]

    if not footnotes:
        return ""

    # Typically footnotes are separated by blank lines
    return "\n\n".join(child.render(context) for child in footnotes)


def render_footnote_open(node: RenderTreeNode, context: RenderContext) -> str:
    """Render footnote definition: [^label]: Content"""
    label = node.meta.get("label", "")
    if not label:
        # This case should be rare now since we handle label=None as inline
        label = str(node.meta.get("id", ""))

    # Render content
    # Note: Children are usually blocks (p, blockquote, etc.)
    # Mdformat renders them with their own spacing.
    content = "\n\n".join(child.render(context) for child in node.children)

    # Construct marker: `[^label]: `
    marker = f"[^{label}]: "

    # Indent entire content by 4 spaces (standard markdown block indent)
    # We assume 4 spaces is enough.
    indented_content = textwrap.indent(content, "    ")

    if not content:
        return marker

    return f"{marker}\n{indented_content}"


def render_footnote_anchor(_node: RenderTreeNode, _context: RenderContext) -> str:
    """Render the backlink/anchor at end of footnote.

    In Markdown source, we do NOT write the backlink character manually.
    So this should be an empty string.
    """
    return ""
