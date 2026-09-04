from __future__ import annotations

from typing import TYPE_CHECKING

from mdformat_pandoc.utils import PANDOC_DIV, format_attributes, parse_attributes

if TYPE_CHECKING:
    from markdown_it.rules_block import StateBlock
    from mdformat.renderer import RenderContext, RenderTreeNode

__all__ = ["PANDOC_DIV", "pandoc_div_plugin", "render_pandoc_div"]

# Standard markdown block indent limit
INDENT_LIMIT = 4


def _is_code_block(state: StateBlock, line: int) -> bool:
    """Check if line is inside a code block."""
    return int(state.sCount[line]) - state.blkIndent >= INDENT_LIMIT


def _is_fence_start(state: StateBlock, start_line: int) -> tuple[int, int] | None:
    """Check if a line starts a fenced div.

    Returns (colon_count, pos_after_colons) if it does, else None.
    """
    if _is_code_block(state, start_line):
        return None

    start = state.bMarks[start_line] + state.tShift[start_line]
    maximum = state.eMarks[start_line]

    # Must start with :
    if state.src[start] != ":":
        return None

    # Count colons
    pos = start
    while pos < maximum and state.src[pos] == ":":
        pos += 1

    colon_count = pos - start
    min_fence_colons = 3
    if colon_count < min_fence_colons:
        return None

    return colon_count, pos


def _find_closing_fence(state: StateBlock, start_line: int, end_line: int, min_colons: int) -> int:
    """Find the line containing the closing fence."""
    next_line = start_line + 1
    nesting = 1

    while next_line < end_line:
        if _is_code_block(state, next_line):
            next_line += 1
            continue

        line_start = state.bMarks[next_line] + state.tShift[next_line]
        line_end = state.eMarks[next_line]

        if line_start >= line_end or state.src[line_start] != ":":
            next_line += 1
            continue

        # Count colons on this line
        line_pos = line_start
        while line_pos < line_end and state.src[line_pos] == ":":
            line_pos += 1

        line_colon_count = line_pos - line_start
        if line_colon_count < min_colons:
            next_line += 1
            continue

        line_rest = state.src[line_pos:line_end].strip()

        # If has attributes, it's a nested opening
        if line_rest:
            nested_attrs = parse_attributes(line_rest)
            max_div_attrs = 2
            if (
                nested_attrs.get("id")
                or nested_attrs.get("classes")
                or len(nested_attrs) > max_div_attrs
            ):
                nesting += 1
        else:
            # Closing fence (no attributes)
            nesting -= 1
            if nesting == 0:
                return next_line

        next_line += 1

    return next_line


def pandoc_div_plugin(state: StateBlock, start_line: int, end_line: int, silent: bool) -> bool:  # noqa: FBT001
    """Parse pandoc fenced divs."""
    fence_info = _is_fence_start(state, start_line)
    if not fence_info:
        return False

    colon_count, pos = fence_info
    maximum = state.eMarks[start_line]
    rest = state.src[pos:maximum].strip()

    # Opening fence must have attributes
    if not rest:
        return False

    # Parse and validate attributes
    attrs = parse_attributes(rest)
    if not attrs.get("id") and not attrs.get("classes"):
        other_keys = [k for k in attrs if k not in ("id", "classes")]
        if not other_keys:
            return False

    # In silent mode, just validate
    if silent:
        return True

    # Find closing fence
    min_div_colons = 3
    next_line = _find_closing_fence(state, start_line, end_line, min_div_colons)

    # Store old state
    old_parent = state.parentType
    old_line_max = state.lineMax

    state.parentType = "container"
    state.lineMax = next_line

    # Create opening token
    token = state.push(f"{PANDOC_DIV}_open", "div", 1)
    token.markup = ":" * colon_count
    token.block = True
    token.info = rest
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
    """Count maximum nesting depth within this node's subtree."""
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
    """Render a pandoc div fence with content."""
    attrs = parse_attributes(node.info) if node.info else {"id": "", "classes": []}
    attr_str = format_attributes(attrs)  # type: ignore[arg-type]

    inner_depth = _count_nested_divs(node)
    min_fixed_colons = 3
    colon_count = min_fixed_colons + inner_depth

    child_outputs = [child.render(context) for child in node.children]
    child_outputs = [c for c in child_outputs if c]
    children_text = "\n\n".join(child_outputs)

    opening = ":" * colon_count + " " + attr_str
    closing = ":" * colon_count

    if children_text:
        return f"{opening}\n\n{children_text}\n\n{closing}"
    return f"{opening}\n{closing}"
