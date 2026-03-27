from __future__ import annotations

from typing import TYPE_CHECKING

from markdown_it.rules_block import StateBlock
from mdformat.renderer import RenderContext, RenderTreeNode

from mdformat_pandoc.utils import PANDOC_DIV, format_attributes, parse_attributes

if TYPE_CHECKING:
    from mdformat.renderer import RenderContext, RenderTreeNode


def _is_code_block(state: StateBlock, line: int) -> bool:
    """Check if line is inside a code block."""
    return state.sCount[line] - state.blkIndent >= 4


def pandoc_div_plugin(
    state: StateBlock, start_line: int, end_line: int, silent: bool
) -> bool:
    """Parse pandoc fenced divs.

    A fenced div starts with 3+ colons followed by attributes.
    It ends with 3+ colons (no attributes).
    """
    if _is_code_block(state, start_line):
        return False

    start = state.bMarks[start_line] + state.tShift[start_line]
    maximum = state.eMarks[start_line]

    # Must start with :
    if state.src[start] != ":":
        return False

    # Count colons
    pos = start
    while pos < maximum and state.src[pos] == ":":
        pos += 1

    colon_count = pos - start
    if colon_count < 3:
        return False

    # Get the rest of the line (attributes)
    rest = state.src[pos:maximum].strip()

    # Opening fence must have attributes
    if not rest:
        return False

    # Parse attributes
    attrs = parse_attributes(rest)

    # Must have at least an id or class or other attribute
    if not attrs.get("id") and not attrs.get("classes"):
        # Check if there are any other keys
        other_keys = [k for k in attrs if k not in ("id", "classes")]
        if not other_keys:
            return False

    # In silent mode, just validate
    if silent:
        return True

    # Find closing fence
    next_line = start_line + 1
    nesting = 1

    while next_line < end_line:
        if state.sCount[next_line] - state.blkIndent >= 4:
            next_line += 1
            continue

        line_start = state.bMarks[next_line] + state.tShift[next_line]
        line_end = state.eMarks[next_line]

        if line_start >= line_end:
            next_line += 1
            continue

        if state.src[line_start] != ":":
            next_line += 1
            continue

        # Count colons on this line
        line_pos = line_start
        while line_pos < line_end and state.src[line_pos] == ":":
            line_pos += 1

        line_colon_count = line_pos - line_start
        if line_colon_count < 3:
            next_line += 1
            continue

        line_rest = state.src[line_pos:line_end].strip()

        # If has attributes, it's a nested opening
        if line_rest:
            nested_attrs = parse_attributes(line_rest)
            if (
                nested_attrs.get("id")
                or nested_attrs.get("classes")
                or len(nested_attrs) > 2
            ):
                nesting += 1
        else:
            # Closing fence (no attributes)
            nesting -= 1
            if nesting == 0:
                break

        next_line += 1

    # Store old state
    old_parent = state.parentType
    old_line_max = state.lineMax

    state.parentType = "container"
    state.lineMax = next_line

    # Create opening token
    token = state.push(f"{PANDOC_DIV}_open", "div", 1)
    token.markup = ":" * colon_count
    token.block = True
    token.info = rest  # Store original attribute string
    token.meta = {"attrs": attrs, "colon_count": colon_count}
    token.map = [start_line, next_line + 1]

    # Tokenize content
    state.md.block.tokenize(state, start_line + 1, next_line)

    # Create closing token
    token = state.push(f"{PANDOC_DIV}_close", "div", -1)
    token.markup = ":" * colon_count
    token.block = True

    state.parentType = old_parent
    state.lineMax = old_line_max
    state.line = next_line + 1

    return True


def _count_nested_divs(node: RenderTreeNode) -> int:
    """Count maximum nesting depth within this node's subtree.

    For outer-longer convention: outer divs need more colons than inner divs.
    Returns the max depth of nested pandoc_div children.
    """
    max_depth = 0
    for child in node.children:
        if child.type == PANDOC_DIV:
            child_depth = 1 + _count_nested_divs(child)
            max_depth = max(max_depth, child_depth)
        else:
            child_depth = _count_nested_divs(child)
            max_depth = max(max_depth, child_depth)
    return max_depth


def render_pandoc_div(node: RenderTreeNode, context: RenderContext) -> str:
    """Render a pandoc div fence with content.

    Uses professional format with single blank lines for visual separation:
    - Blank line after opening fence (separates attributes from content)
    - Blank line before closing fence (provides visual closure)
    - Children separated by blank lines (required for block elements like lists)
    """
    # Get attributes from the opening token's info field
    attrs = parse_attributes(node.info) if node.info else {"id": "", "classes": []}

    # Format attributes
    attr_str = format_attributes(attrs)

    # Calculate colon count based on nesting (outer-longer convention)
    # Outer divs get more colons than inner divs
    inner_depth = _count_nested_divs(node)
    colon_count = 3 + inner_depth

    # Render children with proper block-level spacing
    # Double newlines between children preserves mdformat's block element handling
    child_outputs = []
    for child in node.children:
        rendered = child.render(context)
        if rendered:
            child_outputs.append(rendered)

    children_text = "\n\n".join(child_outputs)

    # Build the div with professional formatting
    opening = ":" * colon_count + " " + attr_str
    closing = ":" * colon_count

    if children_text:
        return f"{opening}\n\n{children_text}\n\n{closing}"
    return f"{opening}\n{closing}"
