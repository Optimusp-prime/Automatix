"""Determinism of symbol-labeled DFA and NFA transition functions."""

from typing import cast

from automata.fa.dfa import DFA
from automata.fa.nfa import NFA


class DeterminismMixin:
    """Expose determinism on DFA/NFA, without assigning GNFA semantics."""

    def is_deterministic(self) -> bool:
        """Return whether transitions are deterministic and epsilon-free.

        A valid DFA is deterministic even when partial. An NFA must have
        at most one destination per symbol and no actual epsilon edge.
        An empty destination set, including under "", defines no edge.
        The source is not modified and no cache is added.

        Returns
        -------
        bool
            Whether this DFA/NFA is deterministic, independently of
            completeness. This mixin is not exposed on ExtendedGNFA.

        Complexity
        ----------
        DFA: O(1) time. NFA: O(T) time, where T counts stored source rows
        and symbol entries (destination-set lengths are O(1)). Auxiliary
        space is O(1); no transition graph is built.

        References
        ----------
        Professor requirement #33 and supplied mature DeterminismMixin
        excerpt; automata-lib 9.2.0 DFA/NFA transition representations.
        """
        automaton = cast(DFA | NFA, self)
        if isinstance(automaton, DFA):
            return True
        for paths in automaton.transitions.values():
            for symbol, destinations in paths.items():
                if (symbol == "" and destinations) or len(destinations) > 1:
                    return False
        return True
