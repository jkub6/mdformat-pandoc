from mdformat.renderer import RenderContext, RenderTreeNode


def render_math_inline(node: RenderTreeNode, context: RenderContext) -> str:
    """Render inline math: $...$"""
    return f"${node.content}$"


def render_math_block(node: RenderTreeNode, context: RenderContext) -> str:
    """Render display math: $$...$$"""
    return f"$$\n{node.content.strip()}\n$$"
