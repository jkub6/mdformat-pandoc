import re
from typing import TypedDict

from markdown_it import MarkdownIt
from markdown_it.rules_block import list as std_list_mod
from markdown_it.rules_block.list import list_block as std_list_block
from markdown_it.rules_block.state_block import StateBlock
from markdown_it.token import Token
from mdit_py_plugins.utils import is_code_block


def _determine_style_and_value(val: str, delim: str, spaces: int) -> tuple[str, int] | None:
    style: str | None = None
    numeric_val: int = 1

    if val.startswith("@"):
        style = "example"
    elif val == "#":
        style = "arabic"
    elif val.isdigit():
        style, numeric_val = "arabic", int(val)
    elif len(val) == 1 and val.isalpha():
        min_spaces_single_cap = 2
        # Single uppercase letter followed by a period requires at least two spaces
        if val.isupper() and delim == "period" and spaces < min_spaces_single_cap:
            pass  # Invalid: leave style as None
        elif val.lower() == "i":
            style = "roman"
        else:
            style, numeric_val = "alpha", ord(val.lower()) - ord("a") + 1
    # Multi-letter: must be Roman to be a valid Pandoc marker
    elif re.match(r"^[ivxlcmIVXLCM]+$", val):
        style = "roman"  # Placeholder for multi-letter roman

    return (style, numeric_val) if style else None


class FancyMarkerInfo(TypedDict):
    style: str
    delim: str
    value: int
    spaces: int
    markup: str
    pos_after: int


def parse_fancy_marker(state: StateBlock, start_line: int) -> FancyMarkerInfo | None:
    if start_line >= len(state.bMarks):
        return None
    pos = state.bMarks[start_line] + state.tShift[start_line]
    max_pos = state.eMarks[start_line]

    line_text = state.src[pos:max_pos]

    # Regex for various styles: (1), 1., 1), (#), #., (@label)
    match = re.match(
        r"^(\((?P<val1>[#a-zA-Z0-9]+|@[a-zA-Z0-9_\-]*)\)|(?P<val2>[#a-zA-Z0-9]+)(?P<delim>[.)]))(?P<spaces>[ \t]+)",
        line_text,
    )
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

    result = _determine_style_and_value(val, delim, spaces)
    if result is None:
        return None

    style, numeric_val = result

    return {
        "style": style,
        "delim": delim,
        "value": numeric_val,
        "spaces": spaces,
        "markup": markup,
        "pos_after": pos + match.start("spaces"),
    }


def skip_fancy_ordered_list_marker(state: StateBlock, start_line: int) -> int:
    """Helper for the monkeypatch to skip our fancy marker."""
    info = parse_fancy_marker(state, start_line)
    if info:
        # If we are interrupting a paragraph (silent mode and sCount >= blkIndent),
        # only standard lists (1., 1)) are allowed.
        # Fancy lists like (1), a., etc. should not interrupt paragraphs.
        if getattr(state, "_is_silent", False) and state.sCount[start_line] >= state.blkIndent:
            if info["delim"] == "parens" or info["style"] not in ("arabic", "example"):
                return -1

        # Cache the info for the current item so patched_push can find it
        state._last_fancy = info  # type: ignore[attr-defined]
        return int(info["pos_after"])
    return -1


def patched_int(val: object, base: int = 10) -> int:
    """A patched version of int() that handles non-numeric list items."""
    try:
        if isinstance(val, int):
            return val
        if isinstance(val, str):
            val_str = val.strip("()@.")
            if val_str.isdigit():
                return int(val_str)
            elif len(val_str) == 1 and val_str.isalpha():
                if val_str.lower() == "i":
                    return 1
                return ord(val_str.lower()) - ord("a") + 1
            elif val_str == "#":
                return 1
            elif re.match(r"^[ivxlcmIVXLCM]+$", val_str):
                return 1 if val_str.lower() == "i" else 2
        return int(str(val), base)
    except (ValueError, TypeError):
        return 1


# Global patch state to avoid multiple patches
_PATCH_STATE = {"applied": False}


def apply_global_patches() -> None:
    """Apply global monkeypatches to markdown-it-py list rule."""
    if _PATCH_STATE["applied"]:
        return

    # We patch the module-level functions that std_list_block calls
    std_list_mod.skipOrderedListMarker = skip_fancy_ordered_list_marker  # type: ignore[assignment]
    std_list_mod.int = patched_int  # type: ignore[attr-defined]

    _PATCH_STATE["applied"] = True


def fancy_lists_rule(state: StateBlock, start_line: int, end_line: int, silent: bool) -> bool:  # noqa: FBT001
    """A block rule that intercepts lists to support Pandoc fancy markers."""
    if is_code_block(state, start_line):
        return False

    info = parse_fancy_marker(state, start_line)
    if not info:
        return False

    if silent:
        return True

    original_push = state.push

    def patched_push(ttype: str, tag: str, level: int) -> Token:
        token = original_push(ttype, tag, level)  # type: ignore[arg-type]
        if ttype in ("ordered_list_open", "list_item_open"):
            # Use info from the rule start for the list open,
            # but for items use the most recent info from skip_fancy_ordered_list_marker
            fancy = getattr(state, "_last_fancy", info)
            if fancy:
                token.meta.update(
                    {
                        "pandoc_style": str(fancy["style"]),
                        "pandoc_delim": str(fancy["delim"]),
                        "pandoc_spaces": str(fancy["spaces"]),
                        "pandoc_markup": str(fancy["markup"]),
                    }
                )
        return token

    state.push = patched_push  # type: ignore[method-assign, assignment]
    try:
        state._last_fancy = info  # type: ignore[attr-defined]

        return bool(std_list_block(state, start_line, end_line, silent))
    finally:
        state.push = original_push  # type: ignore[method-assign]
        if hasattr(state, "_last_fancy"):
            del state._last_fancy


def fancy_lists_plugin(md: MarkdownIt) -> None:
    """A markdown-it-py plugin that adds support for Pandoc fancy lists."""
    apply_global_patches()
    # Register our rule before the standard list rule
    md.block.ruler.before("list", "fancy_list", fancy_lists_rule)
