"""Exact-state induced subautomata built from concrete FA restrictions."""

from collections.abc import Iterable, Set
from typing import FrozenSet, Protocol, Self, TypeVar

from automata.base.exceptions import InvalidStateError
from automata.fa.fa import FAStateT


class _Restrictable(Protocol):
    """Read-only state interface and same-type private reconstruction."""

    @property
    def states(self) -> Set[FAStateT]:
        """Return the source state set."""
        ...

    @property
    def initial_state(self) -> FAStateT:
        """Return the mandatory initial state."""
        ...

    def _restrict_to_states(self, kept: FrozenSet[FAStateT]) -> Self:
        """Construct a fresh concrete automaton over kept states."""
        ...


_RestrictableT = TypeVar("_RestrictableT", bound=_Restrictable)


class SubautomatonMixin:
    """Expose exact-state restrictions without changing the source."""

    def induced_subautomaton(
        self: _RestrictableT, states: Iterable[FAStateT]
    ) -> _RestrictableT:
        """Return a new same-type automaton induced by exactly the given states.

        Every retained transition has both endpoints in the requested set.
        The alphabet is preserved; DFA/NFA final states are restricted to
        that set. GNFA also requires its structural final state. Unlike
        ``trim()``, this operation never adds mandatory states to an empty
        or otherwise invalid request.

        Parameters
        ----------
        states : Iterable[FAStateT]
            States to retain. The iterable is consumed once. It must contain
            the source initial state; GNFA additionally requires final_state.

        Returns
        -------
        Self
            A fresh Extended automaton of the same concrete type, whose
            states equal exactly the requested set.

        Raises
        ------
        InvalidStateError
            If a requested state is unknown or unhashable, or the set is
            empty or omits a required structural state. The GNFA-specific
            final-state check is performed by its reconstruction helper.
        AutomatonException
            If the upstream constructor rejects another representation
            invariant after filtering; such validation is not suppressed.

        Complexity
        ----------
        O(|Q| + T + V) time, including materialization, validation,
        transition filtering and construction. Q is the source state set,
        T bounds the transition entries examined, and V is upstream
        constructor validation (including GNFA regex checks). Auxiliary
        and result storage are proportional to the requested states and
        retained transition table, plus upstream validation memory.
        Hashing and equality are assumed constant-time on average.

        References
        ----------
        Professor requirement #19 and the supplied reference-extension
        SubautomatonMixin excerpt; the source PDFs were not accessed.
        ADR-0007: concrete private restriction helpers and trim's distinct
        empty-language convention.
        """
        try:
            requested = frozenset(states)
        except TypeError as exc:
            raise InvalidStateError(
                "requested states must be an iterable of hashable states"
            ) from exc

        unknown = requested - self.states
        if unknown:
            raise InvalidStateError(f"unknown states requested: {unknown!r}")
        if self.initial_state not in requested:
            raise InvalidStateError("the initial state must be retained")

        return self._restrict_to_states(requested)
