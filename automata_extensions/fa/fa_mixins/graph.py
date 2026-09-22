"""Private graph primitives shared by finite-automaton mixins."""

from collections.abc import Iterator, Mapping, Set
from typing import Protocol, TypeAlias

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
