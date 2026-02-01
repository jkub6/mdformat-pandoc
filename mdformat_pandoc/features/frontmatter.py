from mdformat.renderer import RenderContext, RenderTreeNode

def render_front_matter(node: RenderTreeNode, context: RenderContext) -> str:
    """Render YAML front matter.
    
    Front matter token info usually contains the style (yaml, toml).
    Pandoc typically uses YAML with '---' fences.
    """
    content = node.content.strip()
    if not content:
        return ""
    
    # Check if we should use --- or +++
    fence = "---"
    if node.markup == "+++":
        fence = "+++"
    
    return f"{fence}\n{content}\n{fence}"
