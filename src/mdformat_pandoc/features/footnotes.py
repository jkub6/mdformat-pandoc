"""Pandoc footnote support for mdformat.

Features:
1. Block-level placement: footnote definitions appear directly after their
   respective top-level block in order of usage.
2. Inline footnote conversion: inline footnotes `^[...]` are converted to
   reference footnotes `[^N]` with their definitions placed directly after.
3. Sequential numbering: footnotes are numbered sequentially (`1, 2, 3, ...`)
   in order of first appearance.
4. Multi-usage naming: footnotes used in multiple places are labeled as
   `num_usages` (e.g., `1_2`, `5_3`), while single-use footnotes use `num`.
5. Reused footnotes: definitions only appear once—immediately after their first usage.
"""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, Any

from markdown_it.token import Token
from mdit_py_plugins.footnote.index import _data_from_env

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from markdown_it.rules_core import StateCore
    from mdformat.renderer import RenderContext, RenderTreeNode


def _find_footnote_refs(tokens: Sequence[Token]) -> list[Token]:
    """Recursively find all footnote_ref tokens within a list of inline tokens."""
    refs: list[Token] = []
    for t in tokens:
        if t.type == "footnote_ref":
            refs.append(t)
        if t.children:
            refs.extend(_find_footnote_refs(t.children))
    return refs


class _FootnoteRelocator:
    """Manages renumbering and relocating footnotes directly after blocks."""

    def __init__(self, state: StateCore) -> None:
        self.state = state
        self.footnote_data = _data_from_env(state.env)
        self.fn_list = self.footnote_data.get("list", {})
        self.refs_map = self.footnote_data.get("refs", {})
        self.ref_tokens, self.tokens_without_defs = self._extract_definitions(state.tokens)
        self.seq_counter = 1
        self.key_to_label: dict[tuple[str, Any], str] = {}
        self.emitted_keys: set[tuple[str, Any]] = set()
        self.pending_block_keys: list[tuple[str, Any]] = []

    @staticmethod
    def _extract_definitions(
        tokens: list[Token],
    ) -> tuple[dict[str, list[Token]], list[Token]]:
        ref_tokens: dict[str, list[Token]] = {}
        current_label: str | None = None
        current_tokens: list[Token] = []
        inside_ref = False
        tokens_without_defs: list[Token] = []

        for tok in tokens:
            if tok.type == "footnote_reference_open":
                inside_ref = True
                current_label = tok.meta.get("label")
                current_tokens = []
                continue
            if tok.type == "footnote_reference_close":
                inside_ref = False
                if current_label is not None:
                    ref_tokens[current_label] = current_tokens
                continue
            if inside_ref:
                current_tokens.append(tok)
                continue
            tokens_without_defs.append(tok)

        return ref_tokens, tokens_without_defs

    def _process_inline(self, inline_tok: Token) -> None:
        if not inline_tok.children:
            return
        for child in _find_footnote_refs(inline_tok.children):
            fn_id = child.meta.get("id")
            fn_info = self.fn_list.get(fn_id, {}) if isinstance(fn_id, int) else {}
            orig_label = fn_info.get("label") or child.meta.get("label")
            if orig_label is not None:
                key: tuple[str, Any] = ("ref", orig_label)
                usages = fn_info.get("count", 1)
            else:
                key = ("inline", fn_id)
                usages = 1

            if key not in self.key_to_label:
                self.key_to_label[key] = (
                    f"{self.seq_counter}_{usages}" if usages > 1 else str(self.seq_counter)
                )
                self.seq_counter += 1

            child.meta["label"] = self.key_to_label[key]

            if key not in self.emitted_keys and key not in self.pending_block_keys:
                self.pending_block_keys.append(key)

    def _create_inline_def_tokens(self, fn_info: Mapping[str, Any]) -> list[Token]:
        p_open = Token("paragraph_open", "p", 1)
        p_open.block = True

        inl = Token("inline", "", 0)
        inl.children = fn_info.get("tokens", [])
        inl.content = fn_info.get("content", "")
        self._process_inline(inl)

        p_close = Token("paragraph_close", "p", -1)
        p_close.block = True
        return [p_open, inl, p_close]

    def _emit_pending(self, tokens_dest: list[Token]) -> None:
        if not self.pending_block_keys:
            return

        tokens_dest.append(Token("footnote_block_open", "", 1))
        idx = 0
        while idx < len(self.pending_block_keys):
            key = self.pending_block_keys[idx]
            idx += 1
            self.emitted_keys.add(key)
            assigned = self.key_to_label[key]
            k_type, k_val = key

            fn_open = Token("footnote_open", "", 1)
            fn_id = k_val if k_type == "inline" else self.refs_map.get(":" + k_val, 0)
            fn_open.meta = {"id": fn_id, "label": assigned}
            tokens_dest.append(fn_open)

            if k_type == "inline":
                fn_info = self.fn_list.get(fn_id, {}) if isinstance(fn_id, int) else {}
                tokens_dest.extend(self._create_inline_def_tokens(fn_info))
            else:
                defs = self.ref_tokens.get(k_val, [])
                for def_tok in defs:
                    if def_tok.type == "inline":
                        self._process_inline(def_tok)
                tokens_dest.extend(defs)

            tokens_dest.append(Token("footnote_close", "", -1))

        tokens_dest.append(Token("footnote_block_close", "", -1))
        self.pending_block_keys.clear()

    def run(self) -> None:
        result_tokens: list[Token] = []

        for tok in self.tokens_without_defs:
            result_tokens.append(tok)
            if tok.type == "inline":
                self._process_inline(tok)

            if tok.nesting == -1 and tok.level == 0 and self.pending_block_keys:
                self._emit_pending(result_tokens)

        if self.pending_block_keys:
            self._emit_pending(result_tokens)

        self.state.tokens = result_tokens


def footnote_block_relocate(state: StateCore) -> None:
    """Core rule to renumber and relocate footnote definitions directly after blocks."""
    if "footnotes" not in state.env:
        return

    relocator = _FootnoteRelocator(state)
    if not relocator.fn_list:
        return

    relocator.run()


def render_footnote_ref(node: RenderTreeNode, _context: RenderContext) -> str:
    """Render footnote reference: [^label]"""
    label = node.meta.get("label", "")
    if not label:
        label = str(node.meta.get("id", ""))
    return f"[^{label}]"


def render_footnote_block_open(node: RenderTreeNode, context: RenderContext) -> str:
    """Render start of footnote block."""
    footnotes = [child.render(context) for child in node.children]
    return "\n\n".join(f for f in footnotes if f)


def render_footnote_open(node: RenderTreeNode, context: RenderContext) -> str:
    """Render footnote definition: [^label]: Content"""
    label = node.meta.get("label", "")
    if not label:
        label = str(node.meta.get("id", ""))

    rendered_children = [c for child in node.children if (c := child.render(context))]
    content = "\n\n".join(rendered_children).strip()

    marker = f"[^{label}]: "
    if not content:
        return marker

    indented_content = textwrap.indent(content, "    ")
    return f"{marker}\n{indented_content}"


def render_footnote_anchor(_node: RenderTreeNode, _context: RenderContext) -> str:
    """Render the backlink/anchor at end of footnote."""
    return ""
