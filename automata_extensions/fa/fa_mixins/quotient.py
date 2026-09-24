"""Shared reversal-based construction for right word quotients."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from automata_extensions.fa.dfa import ExtendedDFA
    from automata_extensions.fa.nfa import ExtendedNFA


def _right_quotient_via_reversal(
    source: ExtendedDFA | ExtendedNFA, word: str
) -> ExtendedNFA:
    """Apply reverse, left quotient by the reversed word, then reverse."""
    reversed_source = source.reverse()
    return reversed_source.left_quotient_word(word[::-1]).reverse()
