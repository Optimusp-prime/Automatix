"""DFA language inclusion via an empty intersection with the complement."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from automata_extensions.fa.dfa import ExtendedDFA


class InclusionMixin:
    """Decide DFA language inclusion using existing extension analyses."""

    def is_included_in(self, other: ExtendedDFA) -> bool:
        """Return whether every word accepted by this DFA is accepted by other.

        The criterion is ``L(self) ∩ complement(L(other)) = ∅``. The method
        composes complement, lazy product and empty-language analysis rather
        than enumerating words or changing either operand.

        Parameters
        ----------
        other : ExtendedDFA
            DFA whose language is proposed to contain this DFA's language.

        Returns
        -------
        bool
            True exactly when ``L(self)`` is a subset of ``L(other)``.

        Raises
        ------
        SymbolMismatchError
            If the two DFA input alphabets differ, as in ``product``.

        Complexity
        ----------
        O((|Q1| + |Q2| + R) × |Sigma| + V) expected time and
        O((|Q2| + R) × |Sigma| + M) auxiliary space. R is the number of
        reachable product pairs (including any implicit trap), while V/M
        cover upstream completion, product construction and validation.
        State hashing and the final-state predicate are assumed O(1).

        References
        ----------
        Professor requirement #24 and the supplied mature InclusionMixin
        example. The source PDFs were not accessed.
        """
        left = cast("ExtendedDFA", self)
        other_complement = other.complement()
        witness_automaton = left.product(
            other_complement,
            is_final=lambda left_state, right_state: (
                left_state in left.final_states
                and right_state in other_complement.final_states
            ),
        )
        return witness_automaton.is_empty()
