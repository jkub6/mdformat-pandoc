import math
import re
from typing import Any, cast

from markdown_it import MarkdownIt
from markdown_it.rules_block import list as std_list_mod
from markdown_it.rules_block.state_block import StateBlock
from markdown_it.token import Token
from mdit_py_plugins.utils import is_code_block


def parse_fancy_marker(state: StateBlock, start_line: int) -> dict[str, Any] | None:
    """Parse a Pandoc-style fancy list marker."""
    if start_line >= len(state.bMarks):
        return None
    pos = state.bMarks[start_line] + state.tShift[start_line]
    max_pos = state.eMarks[start_line]
    
    line_text = state.src[pos:max_pos]
    
    # Regex for various styles: (1), 1., 1), (#), #., (@label)
    match = re.match(r"^(\((?P<val1>[#a-zA-Z0-9]+|@[a-zA-Z0-9_\-]*)\)|(?P<val2>[#a-zA-Z0-9]+)(?P<delim>[.)]))(?P<spaces>[ \t]+)", line_text)
    if not match:
        return None
        
    val = match.group("val1") or match.group("val2")
    delim_char = match.group("delim")
    
    if match.group("val1"):
        delim = "parens"
    elif delim_char == ".":
        delim = "period"
    else:
        delim = "paren"
        
    spaces = len(match.group("spaces"))
    markup = match.group(1)
    
    style = "arabic"
    numeric_val = 1
    
    if val.startswith("@"):
        style = "example"
        numeric_val = 1
    elif val == "#":
        style = "arabic"
        numeric_val = 1
    elif val.isdigit():
        style = "arabic"
        numeric_val = int(val)
    elif len(val) == 1 and val.isalpha():
        # To avoid ambiguity, Pandoc treats single letters as alpha 
        # unless it is 'i' or 'I'.
        if val.lower() == "i":
            style = "roman"
            numeric_val = 1
        else:
            style = "alpha"
            numeric_val = ord(val.lower()) - ord("a") + 1
    else:
        # Multi-letter: must be Roman to be a valid Pandoc marker
        roman_re = r"^[ivxlcmIVXLCM]+$"
        if re.match(roman_re, val):
            style = "roman"
            numeric_val = 1 # Placeholder for multi-letter roman
        else:
            # Not a valid Pandoc fancy marker (e.g. "mortal")
            return None
            
    return {
        "style": style,
        "delim": delim,
        "value": numeric_val,
        "spaces": spaces,
        "markup": markup,
        "pos_after": pos + match.end(),
    }


def skip_fancy_ordered_list_marker(state: StateBlock, start_line: int) -> int:
    """Helper for the monkeypatch to skip our fancy marker."""
    info = parse_fancy_marker(state, start_line)
    if info:
        # Cache the info for the current item so patched_push can find it
        state._last_fancy = info
        return info["pos_after"]
    return -1


import sys


def patched_int(val: Any, base: int = 10) -> int:
    """A patched version of int() that handles non-numeric list items."""
    try:
        if isinstance(val, str) and not val.isdigit():
            return 1
        return int(val, base)
    except (ValueError, TypeError):
        return 1

# Global patch state to avoid multiple patches
_PATCHED = False

def apply_global_patches():
    """Apply global monkeypatches to markdown-it-py list rule."""
    global _PATCHED
    if _PATCHED:
        return
    
    # We patch the module-level functions that std_list_block calls
    std_list_mod.skipOrderedListMarker = skip_fancy_ordered_list_marker
    setattr(std_list_mod, "int", patched_int)
    
    _PATCHED = True


def fancy_lists_rule(state: StateBlock, start_line: int, end_line: int, silent: bool) -> bool:
    """A block rule that intercepts lists to support Pandoc fancy markers."""
    if is_code_block(state, start_line):
        return False
        
    info = parse_fancy_marker(state, start_line)
    if not info:
        return False
        
    if silent:
        return True
        
    # Ensure patches are applied
    apply_global_patches()

    original_push = state.push
    
    def patched_push(ttype: str, tag: str, level: int) -> Token:
        token = original_push(ttype, tag, level)
        if ttype in ("ordered_list_open", "list_item_open"):
            # Use info from the rule start for the list open,
            # but for items use the most recent info from skip_fancy_ordered_list_marker
            fancy = getattr(state, "_last_fancy", info)
            if fancy:
                token.meta.update({
                    "pandoc_style": str(fancy["style"]),
                    "pandoc_delim": str(fancy["delim"]),
                    "pandoc_spaces": str(fancy["spaces"]),
                    "pandoc_markup": str(fancy["markup"]),
                })
        return token

    state.push = patched_push
    try:
        state._last_fancy = info
        from markdown_it.rules_block.list import list_block as std_list_block
        return bool(std_list_block(state, start_line, end_line, silent))
    finally:
        state.push = original_push
        if hasattr(state, "_last_fancy"):
            del state._last_fancy


def fancy_lists_plugin(md: MarkdownIt) -> None:
    """A markdown-it-py plugin that adds support for Pandoc fancy lists."""
    # Register our rule before the standard list rule
    md.block.ruler.before("list", "fancy_list", fancy_lists_rule)
