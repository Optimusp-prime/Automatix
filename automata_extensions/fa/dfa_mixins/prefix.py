"""Prefix-closed DFA language analysis."""

from typing import Protocol, cast

from automata.fa.dfa import DFA
from automata.fa.fa import FAStateT


class _UsefulDFA(Protocol):
    """Only the existing useful-state query needed by the predicate."""

    def useful_states(self) -> frozenset[FAStateT]:
        """Return states on an accepting path."""
        ...


class PrefixMixin:
    """Analyze prefix closure of deterministic finite automata."""

    def is_prefix_closed(self) -> bool:
        """Return whether every useful state is final.

        Equivalently, every prefix of an accepted word is accepted.
        The empty language satisfies the criterion vacuously. This query
        does not modify the automaton or cache any result.

        Returns
        -------
        bool
            True exactly when the DFA language is prefix-closed.

        Complexity
        ----------
        O(|Q| + T) expected time and O(|Q| + |E|) auxiliary space.
        ``useful_states`` computes accessibility and coaccessibility over
        all states and emitted transitions; the final subset check adds
        at most O(|Q|) expected time. No adjacency is cached.

        References
        ----------
        Professor requirement #27: all useful states are final.
        """
        dfa = cast(DFA, self)
        useful = cast(_UsefulDFA, self)
        return useful.useful_states().issubset(dfa.final_states)
