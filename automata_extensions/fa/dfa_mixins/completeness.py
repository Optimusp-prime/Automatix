"""Total-transition predicate for deterministic finite automata."""

from collections.abc import Mapping, Set
from typing import Protocol

from automata.fa.fa import FAStateT


class _DfaTransitionView(Protocol):
    """Read-only DFA attributes needed to test transition totality."""

    @property
    def states(self) -> Set[FAStateT]: ...

    @property
    def input_symbols(self) -> Set[str]: ...

    @property
    def transitions(self) -> Mapping[FAStateT, Mapping[str, FAStateT]]: ...


class CompletenessMixin:
    """Analyze DFA transition totality without modifying the automaton."""

    def is_complete(self: _DfaTransitionView) -> bool:
        """Return whether every state has a transition for every symbol.

        A DFA is complete when its transition function is total on
        ``states × input_symbols``. This inspects actual transition entries:
        ``allow_partial=True`` merely permits missing entries and does not
        imply that any entry is missing. An empty alphabet is complete
        vacuously. The source automaton is not modified.

        Returns
        -------
        bool
            True exactly when every state-symbol pair has a transition.

        Complexity
        ----------
        O(|Q| × |Σ|) worst-case time and O(1) auxiliary space, assuming
        expected O(1) mapping membership. Q is the state set and Σ is
        the input alphabet. An early missing transition may return sooner.

        References
        ----------
        Professor requirement #20 and the supplied reference-extension
        CompletenessMixin excerpt; the source PDFs were not accessed.
        automata-lib 9.2.0 DFA transition validation and allow_partial.
        """
        for state in self.states:
            for symbol in self.input_symbols:
                if symbol not in self.transitions[state]:
                    return False
        return True
