"""Total-transition predicate for deterministic finite automata."""

from collections.abc import Mapping, Set
from typing import Protocol, Self, cast

from automata.fa.fa import FAStateT


class _DfaTransitionView(Protocol):
    """Read-only DFA attributes needed to test transition totality."""

    @property
    def states(self) -> Set[FAStateT]: ...

    @property
    def input_symbols(self) -> Set[str]: ...

    @property
    def transitions(self) -> Mapping[FAStateT, Mapping[str, FAStateT]]: ...


class _CompletableDFA(Protocol):
    """Upstream completion operation used by the pedagogical API."""

    def to_complete(self, trap_state: FAStateT | None = None) -> Self: ...


class CompletenessMixin:
    """Test and restore DFA transition totality without mutating the source."""

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

    def complete(self, trap_state: FAStateT | None = None) -> Self:
        """Return a new equivalent DFA with a total transition function.

        Missing transitions lead to one nonaccepting trap state, which loops
        on every input symbol. Existing transitions are preserved. An already
        complete DFA is copied without adding a trap state. The source
        automaton is not modified.

        Parameters
        ----------
        trap_state : FAStateT | None, default: None
            Name for a new trap state. None requests automata-lib's
            collision-free negative-integer name. The name is unused when
            no trap state is needed.

        Returns
        -------
        Self
            Fresh ExtendedDFA with the same language and alphabet.

        Raises
        ------
        InvalidStateError
            If a needed trap state has a requested name already in states.

        Complexity
        ----------
        O(|Q| × |Sigma| + V) time and O(|Q| × |Sigma| + M) auxiliary space
        in the worst case. V and M denote upstream construction/validation
        cost and temporary memory. Already-complete DFAs are copied.

        References
        ----------
        Professor requirement #21; automata-lib 9.2.0 DFA.to_complete.
        The source PDFs were not accessed.
        """
        return cast(Self, cast(_CompletableDFA, self).to_complete(trap_state))
