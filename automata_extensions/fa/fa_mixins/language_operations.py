"""Rational language constructions shared by DFA and NFA extensions."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from automata.fa.dfa import DFA
from automata.fa.nfa import NFA

if TYPE_CHECKING:
    from automata_extensions.fa.nfa import ExtendedNFA


def _as_nfa(automaton: DFA | NFA) -> NFA:
    """Convert a DFA to an extended NFA, leaving an NFA unchanged."""
    if isinstance(automaton, DFA):
        from automata_extensions.fa.nfa import ExtendedNFA

        return ExtendedNFA.from_dfa(automaton)
    return automaton


class LanguageOperationsMixin:
    """Build concatenation and Kleene star as epsilon-NFA operations."""

    def concatenation(self, other: DFA | NFA) -> ExtendedNFA:
        """Return a fresh NFA accepting ``L(self) · L(other)``.

        Upstream renames both state sets disjointly and connects each former
        left final state to the right initial state with an epsilon edge.
        Neither operand is modified or determinized.

        Parameters
        ----------
        other : DFA | NFA
            Right operand. Its alphabet may differ from the left alphabet.

        Returns
        -------
        ExtendedNFA
            New epsilon-NFA for the concatenated language.

        Complexity
        ----------
        O(|Q1| + |Q2| + T1 + T2 + V) time and
        O(|Q1| + |Q2| + T1 + T2 + M) space. T1/T2 count transition
        entries and destinations; V/M include upstream construction and
        validation. A DFA operand is converted once before concatenation.

        References
        ----------
        Professor requirement #45 and the supplied mature
        LanguageOperationsMixin example. automata-lib 9.2.0 NFA.from_dfa
        and NFA.concatenate.
        """
        left = _as_nfa(cast(DFA | NFA, self))
        right = _as_nfa(other)
        # The left operand is always ExtendedNFA: DFA is converted above,
        # while this mixin is installed only on ExtendedDFA/ExtendedNFA.
        return cast("ExtendedNFA", NFA.concatenate(left, right))

    def kleene_star(self) -> ExtendedNFA:
        """Return a fresh NFA accepting zero or more repetitions.

        Upstream adds a collision-free initial/final state, an epsilon edge
        into the old initial state, and epsilon repetition edges from each
        old final state. The empty word is therefore always accepted.
        The source is neither modified nor determinized.

        Returns
        -------
        ExtendedNFA
            New epsilon-NFA for ``L(self)*``.

        Complexity
        ----------
        O(|Q| + T + |F| + V) time and O(|Q| + T + |F| + M) space,
        including optional DFA-to-NFA conversion, upstream construction
        and validation V/M. T counts stored transition entries and edges.

        References
        ----------
        Professor requirement #46 and the supplied mature
        LanguageOperationsMixin example. automata-lib 9.2.0 NFA.from_dfa,
        NFA.kleene_star and FA._add_new_state.
        """
        source = _as_nfa(cast(DFA | NFA, self))
        return cast("ExtendedNFA", NFA.kleene_star(source))
