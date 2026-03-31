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


import textwrap


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

    # We want:
    # [^label]: First block...
    #
    #           Second block...

    # Construct marker: `[^label]: `
    marker = f"[^{label}]: "

    # Indent entire content by 4 spaces (standard markdown block indent)
    # We assume 4 spaces is enough.
    indented_content = textwrap.indent(content, "    ")

    # Now we want `marker` to replace the first indentation.
    # But `marker` might be longer than 4 spaces if label is long.
    # If marker is long (e.g. `[^100]: ` is 8 chars), we might want:
    # [^100]: Content...
    #         Content... (indent 8 spaces?)
    #
    # Pandoc usually accepts 4-space indent for blocks regardless of marker length,
    # AS LONG AS the content starts on the same line or next line indented.
    # Standard:
    # [^1]:
    #     Content...
    #
    # Or:
    # [^1]: Content...
    #     Content...
    #
    # If we replace first 4 chars of `indented_content` with `marker`:
    # If `marker` is `[^1]: ` (6 chars), and text starts at col 4...
    # It pushes text?

    # Robust approach:
    # Return marker + "\n" + indented_content
    # [^1]:
    #     Content...
    #
    # This is valid and safe for all marker lengths.

    # However, for single paragraph footnotes, it looks nicer on same line.

    # Let's try:
    # Indent everything by 4 spaces.
    # If using same line:
    # `marker` + content.lstrip()
    # But subsequent lines of first paragraph need indentation?
    # textwrap.indent indents ALL lines.

    # Let's go with the safe block style:
    # [^id]:
    #     Content
    #
    # It ensures no alignment issues.

    if not content:
        return marker

    return f"{marker}\n{indented_content}"


def render_footnote_anchor(node: RenderTreeNode, context: RenderContext) -> str:
    """Render the backlink/anchor at end of footnote.

    In Markdown source, we do NOT write the backlink character manually.
    So this should be an empty string.
    """
    return ""
