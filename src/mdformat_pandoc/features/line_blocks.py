from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from markdown_it import MarkdownIt
    from markdown_it.rules_block import StateBlock
    from mdformat.renderer import RenderContext, RenderTreeNode


def pandoc_line_block_plugin(md: MarkdownIt) -> None:
    md.block.ruler.before("paragraph", "pandoc_line_block", pandoc_line_block_rule)


def pandoc_line_block_rule(
    state: StateBlock,
    start_line: int,
    end_line: int,
    silent: bool,  # noqa: FBT001
) -> bool:
    pos = state.bMarks[start_line] + state.tShift[start_line]
    maximum = state.eMarks[start_line]

    if pos >= maximum or state.src[pos] != "|":
        return False

    # Must be followed by a space or end of line
    if pos + 1 < maximum and state.src[pos + 1] != " ":
        return False

    if silent:
        return True

    next_line = start_line + 1
    while next_line < end_line:
        if state.isEmpty(next_line):
            break

        next_pos = state.bMarks[next_line] + state.tShift[next_line]
        next_max = state.eMarks[next_line]

        # Check if it starts with | (followed by space or EOL)
        if (
            next_pos < next_max
            and state.src[next_pos] == "|"
            and (next_pos + 1 == next_max or state.src[next_pos + 1] == " ")
        ):
            next_line += 1
            continue

        # Check if it's an indented continuation line (no | but indented)
        if state.sCount[next_line] > 0:
            next_line += 1
            continue

        break

    state.line = next_line

    token = state.push("line_block_open", "div", 1)
    token.map = [start_line, next_line]

    token = state.push("inline", "", 0)
    token.content = state.getLines(start_line, next_line, state.blkIndent, False).rstrip()  # noqa: FBT003
    token.map = [start_line, next_line]
    token.children = []

    token = state.push("line_block_close", "div", -1)

    return True


def render_line_block(node: RenderTreeNode, context: RenderContext) -> str:
    # We must preserve multiple spaces in line blocks.
    # The default mdformat text renderer shrinks multiple spaces into one.
    # To bypass this, we temporarily replace spaces with a non-breaking space
    # (or a zero-width space) during rendering, then swap back.
    # But wait, we can just replace spaces in the inline node's text children!
    def protect_spaces(n: RenderTreeNode) -> None:
        if n.type == "text" and n.token is not None:
            n.token.content = re.sub(r"( {2,})", lambda m: "\x01" * len(m.group(1)), n.content)
        for child in getattr(n, "children", []) or []:
            protect_spaces(child)

    protect_spaces(node)
    text = "".join(child.render(context) for child in node.children)
    return text.replace("\x01", " ")
