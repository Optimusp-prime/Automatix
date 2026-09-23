"""Private graph primitives shared by finite-automaton mixins."""

from collections.abc import Iterator, Mapping, Set
from typing import FrozenSet, Protocol, TypeAlias

from automata.base.exceptions import InvalidStateError

from automata.fa.fa import FAStateT


class _GraphSource(Protocol):
    """Read-only upstream interface required by graph traversal."""

    @property
    def states(self) -> Set[FAStateT]:
        """Return the automaton's states."""
        ...

    @property
    def initial_state(self) -> FAStateT:
        """Return the automaton's initial state."""
        ...

    def iter_transitions(self) -> Iterator[tuple[FAStateT, FAStateT, str]]:
        """Yield source, destination and label for each actual transition."""
        ...


_Successors: TypeAlias = Mapping[FAStateT, tuple[FAStateT, ...]]


def _build_successors(automaton: _GraphSource) -> _Successors:
    """Build fresh adjacency once, ignoring labels without sorting states.

    NFA epsilon edges are included; upstream GNFA.iter_transitions omits
    None labels. Parallel edges are retained in upstream iteration order.
    No data is attached to the automaton. Time is O(|Q| + T), where T is
    the cost of exhausting iter_transitions; space is O(|Q| + |E|), with
    E the emitted transitions, including parallel edges.
    """
    successors: dict[FAStateT, list[FAStateT]] = {
        state: [] for state in automaton.states
    }
    for source, target, _label in automaton.iter_transitions():
        successors[source].append(target)
    return {state: tuple(targets) for state, targets in successors.items()}


def _build_predecessors(
    automaton: _GraphSource,
) -> Mapping[FAStateT, tuple[FAStateT, ...]]:
    """Build fresh inverse adjacency from the common transition iterator.

    Labels are ignored, with the same edge semantics as _build_successors.
    Parallel edges and upstream iteration order are retained. Time is
    O(|Q| + T), where T exhausts iter_transitions; space is O(|Q| + |E|).
    No forward adjacency, source mutation or cache is needed.
    """
    predecessors: dict[FAStateT, list[FAStateT]] = {
        state: [] for state in automaton.states
    }
    for source, target, _label in automaton.iter_transitions():
        predecessors[target].append(source)
    return {state: tuple(sources) for state, sources in predecessors.items()}


class GraphMixin:
    """Expose direct graph-neighbor queries shared by finite automata."""

    def predecessors_graph(
        self: _GraphSource, state: FAStateT
    ) -> FrozenSet[FAStateT]:
        """Return the direct predecessors of a state in the transition graph.

        An incoming transition contributes its source regardless of label.
        A self-loop includes state itself; parallel transitions contribute
        their source only once. This method does not explore indirect
        ancestors. NFA epsilon transitions are edges, whereas GNFA None
        labels represent absent edges.

        Parameters
        ----------
        state : FAStateT
            State whose incoming neighbors are requested. None is treated
            as an ordinary state when present in the automaton.

        Returns
        -------
        FrozenSet[FAStateT]
            Immutable set of immediate predecessor states, possibly empty.

        Raises
        ------
        InvalidStateError
            If state is absent from states or is unhashable, following the
            start-state policy of the common graph traversal methods.

        Complexity
        ----------
        The inverse adjacency is rebuilt on each call in O(|Q| + T) time
        and O(|Q| + |E|) space, where Q is all states, E all emitted edges
        and T the cost of exhausting ``iter_transitions``. Freezing the
        direct neighbors adds O(deg_in(state)) time and space; the overall
        bounds remain O(|Q| + T) time and O(|Q| + |E|) space with expected
        constant-time hashing and equality. T includes NFA empty target
        entries and GNFA stored None labels.

        References
        ----------
        Professor requirement #18 and the supplied reference-extension
        GraphMixin excerpt; the source PDFs were not accessed.
        ADR-0004: common graph traversal foundation.
        ADR-0006: private inverse-adjacency foundation.
        """
        try:
            valid_state = state in self.states
        except TypeError:
            valid_state = False
        if not valid_state:
            raise InvalidStateError(f"{state!r} is not a valid state")

        predecessors = _build_predecessors(self)
        return frozenset(predecessors[state])
