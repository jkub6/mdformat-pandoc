from __future__ import annotations

import sys
import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mdformat.renderer import RenderContext, RenderTreeNode


def to_alpha(n: int, lower: bool = True) -> str:
    """Convert integer to alphabetic (a, b, c... or A, B, C...)."""
    if n <= 0:
        return str(n)
    res = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        res = chr((ord("a") if lower else ord("A")) + rem) + res
    return res


def to_roman(n: int, lower: bool = True) -> str:
    """Convert integer to roman numerals."""
    if n <= 0:
        return str(n)
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syb = ["m", "cm", "d", "cd", "c", "xc", "l", "xl", "x", "ix", "v", "iv", "i"]
    if not lower:
        syb = [s.upper() for s in syb]
    res = ""
    for i in range(len(val)):
        count = n // val[i]
        res += syb[i] * count
        n -= val[i] * count
    return res


def get_attr(node: RenderTreeNode, name: str) -> str | None:
    """Helper to get an attribute from a node, supporting both dict and list-of-lists."""
    # Try meta first (always a dict if present)
    if meta := getattr(node, "meta", {}):
        if val := meta.get(name):
            return str(val)
            
    # Then try attrs
    attrs = getattr(node, "attrs", {})
    if isinstance(attrs, dict):
        if val := attrs.get(name):
            return str(val)
    elif isinstance(attrs, (list, tuple)):
        for k, v in attrs:
            if k == name:
                return str(v)
    return None


def render_ordered_list(node: RenderTreeNode, context: RenderContext) -> str:
    """Render ordered list. Join items with newlines (double if loose)."""
    # Determine if list is loose
    is_loose = False
    for item in node.children:
        for child in item.children:
            if child.type == "paragraph":
                token = getattr(child, "token", None)
                if token and not getattr(token, "hidden", False):
                    is_loose = True
                    break
        if is_loose:
            break
            
    sep = "\n\n" if is_loose else "\n"
    return sep.join(child.render(context) for child in node.children)


def render_list_item(node: RenderTreeNode, context: RenderContext) -> str:
    """Render list item, preserving Pandoc fancy markers and spacing."""
    # 1. Render content first to handle loose lists and scoping
    is_loose = False
    for child in node.children:
        if child.type == "paragraph":
            token = getattr(child, "token", None)
            if token and not getattr(token, "hidden", False):
                is_loose = True
                break

    content = "".join(child.render(context) for child in node.children)
    if not is_loose:
        content = content.strip()

    # 2. Determine the marker string
    parent = node.parent
    
    # Handle bullet lists (standard markdown)
    # The default mdformat bullet_list renderer adds the marker, 
    # so we only return the content.
    if parent and parent.type == "bullet_list":
        return content

    # Handle ordered lists (including fancy Pandoc ones)
    style = get_attr(node, "pandoc_style") or "arabic"
    delim = get_attr(node, "pandoc_delim") or "period"
    pandoc_spaces = get_attr(node, "pandoc_spaces")
    actual_spaces_count = int(pandoc_spaces) if pandoc_spaces else 2
    pandoc_markup = get_attr(node, "pandoc_markup")

    index = 0
    if parent:
        list_items = [c for c in parent.children if c.type == "list_item"]
        if node in list_items:
            index = list_items.index(node)

        # Opening attributes of parent list
        start_attr = get_attr(parent, "start")
        start = int(start_attr) if start_attr else 1
        current_val = start + index
    else:
        current_val = 1

    # Format the value based on style
    if style == "example":
        prefix = (pandoc_markup or node.markup) + (" " * actual_spaces_count)
        if not content:
            return prefix
        lines = content.splitlines(keepends=True)
        first_line = lines[0]
        rest = "".join(lines[1:])
        return prefix + first_line + textwrap.indent(rest, " " * len(prefix))

    if style == "roman":
        markup = pandoc_markup or node.markup
        is_lower = not any(c.isupper() for c in markup) if markup else True
        marker_val = to_roman(current_val, lower=is_lower)
    elif style == "alpha":
        markup = pandoc_markup or node.markup
        is_lower = not any(c.isupper() for c in markup) if markup else True
        marker_val = to_alpha(current_val, lower=is_lower)
    else:
        marker_val = str(current_val)

    # Wrap with delimiters
    if delim == "parens":
        marker = f"({marker_val})"
    elif delim == "paren":
        marker = f"{marker_val})"
    else:  # period
        marker = f"{marker_val}."

    actual_spaces = " " * actual_spaces_count
    prefix = marker + actual_spaces

    if not content:
        return prefix

    lines = content.splitlines(keepends=True)
    if not lines:
        return prefix
        
    first_line = lines[0]
    rest = "".join(lines[1:])
    return prefix + first_line + textwrap.indent(rest, " " * len(prefix))


def render_dl_open(node: RenderTreeNode, context: RenderContext) -> str:
    """Render definition list. Join children with newlines."""
    return "\n\n".join(child.render(context) for child in node.children)


def render_dt_open(node: RenderTreeNode, context: RenderContext) -> str:
    """Render generic definition term."""
    return "".join(child.render(context) for child in node.children)


def render_dd_open(node: RenderTreeNode, context: RenderContext) -> str:
    """Render definition description. Pandoc syntax: Term : Definition"""
    content = "\n\n".join(child.render(context) for child in node.children)
    indented = textwrap.indent(content, "    ")
    if not indented:
        return ":   "
    return ":   " + indented[4:] if indented.startswith("    ") else ":   " + indented
