"""Cycle analysis of finite-automaton transition graphs."""

from collections.abc import Iterable
from typing import FrozenSet, Protocol

from automata.base.exceptions import InvalidStateError
from automata.fa.fa import FAStateT

from automata_extensions.fa.fa_mixins.graph import (
    _build_successors,
    _GraphSource,
    _Successors,
)


def _has_back_edge(
    starts: Iterable[FAStateT], successors: _Successors
) -> bool:
    """Detect a back edge by DFS from only the supplied root states."""
    gray = 1
    black = 2
    colors: dict[FAStateT, int] = {}

    def visit(state: FAStateT) -> bool:
        colors[state] = gray
        for neighbor in successors[state]:
            if colors.get(neighbor) == gray:
                return True
            if neighbor not in colors and visit(neighbor):
                return True
        colors[state] = black
        return False

    for state in starts:
        if state not in colors and visit(state):
            return True
    return False


class _UsefulSCCSource(_GraphSource, Protocol):
    """Graph, useful states and SCC partition needed for finiteness."""

    def useful_states(self) -> FrozenSet[FAStateT]:
        """Return states on accepting paths."""
        ...

    def strongly_connected_components(self) -> list[FrozenSet[FAStateT]]:
        """Partition the transition graph into SCCs."""
        ...


class CycleMixin:
    """Detect directed cycles through DFS back edges."""

    def has_cycle(self: _GraphSource) -> bool:
        """Return whether any state belongs to a directed cycle.

        Search the entire graph, including components inaccessible from the
        initial state. A self-loop is a cycle. No automaton data is changed or
        cached.

        Returns
        -------
        bool
            True if a DFS edge reaches a state still on its active path;
            False if every DFS finishes without such an edge.

        Complexity
        ----------
        Adjacency construction takes O(|Q| + T) time and O(|Q| + |E|)
        space, where Q is all states, E the emitted transitions (including
        parallel edges), and T exhausts iter_transitions. DFS takes
        O(|Q| + |E|) time and O(|Q|) additional space, including the
        recursion stack. Overall: O(|Q| + T) time and O(|Q| + |E|) space,
        assuming constant-time state hashing and equality. T includes
        NFA empty target entries and GNFA stored None labels. A sufficiently
        deep graph may exceed Python's recursion limit.

        References
        ----------
        Professor requirement #11: DFS back-edge cycle detection, as
        supplied in the task prompt; the source PDFs were not accessed.
        ADR-0004: common graph foundation. ADR-0009: global cycle analysis.
        """
        successors = _build_successors(self)
        return _has_back_edge(successors, successors)

    def has_cycle_from(self: _GraphSource, state: FAStateT) -> bool:
        """Return whether a directed cycle is reachable from the given state.

        The cycle need not contain the starting state. Only its reachable
        subgraph is explored, even when other components contain cycles.
        A self-loop is a cycle. The automaton is neither changed nor cached.

        Parameters
        ----------
        state : FAStateT
            Starting state. None is an ordinary state value when present.

        Returns
        -------
        bool
            True exactly when a DFS from state finds an edge to a state
            still on its active path.

        Raises
        ------
        InvalidStateError
            If state is absent from the automaton or cannot be hashed,
            matching the traversal start-state contract.
        RecursionError
            If the reachable graph exceeds Python's recursion limit.

        Complexity
        ----------
        Building global adjacency takes O(|Q| + T) time and
        O(|Q| + |E|) space, where Q is all states, E all emitted
        transitions, and T exhausts iter_transitions. The DFS restricted
        to reachable states takes O(|Q_reached| + |E_reached|) time and
        O(|Q_reached|) additional space, including recursion. Overall:
        O(|Q| + T) time and O(|Q| + |E|) space, assuming constant-time
        state hashing and equality. T includes NFA empty target entries
        and GNFA stored None labels.

        References
        ----------
        Professor requirement #12: DFS over the graph reachable from one
        state, as supplied in the task prompt; the PDFs were not accessed.
        ADR-0009: DFS back-edge detection in CycleMixin.
        ADR-0004: common graph and start-state conventions.
        """
        try:
            hash(state)
            valid_start = state in self.states
        except TypeError:
            valid_start = False
        if not valid_start:
            raise InvalidStateError(f"{state!r} is not a valid start state")

        successors = _build_successors(self)
        return _has_back_edge((state,), successors)

    def is_finite(self: _UsefulSCCSource) -> bool:
        """Return whether the recognized DFA/NFA language is finite.

        A language is infinite only if an accepting path can traverse a
        cycle that consumes at least one input symbol. A useful cycle made
        solely of NFA epsilon transitions does not satisfy that condition.
        GNFA regex labels require separate semantic analysis; the concrete
        GNFA extension explicitly declines this query for now.

        Returns
        -------
        bool
            False if a consuming transition joins states of the same
            useful strongly connected component; True otherwise.

        Complexity
        ----------
        useful_states() builds forward and reverse adjacency, then the SCC
        query builds adjacency again and one final transition scan checks
        labels. Each is O(|Q| + T) time and O(|Q| + |E|) peak space, so the
        total has those bounds at constant factors, assuming constant-time
        state hashing and equality. Q is all states, E all emitted edges,
        and T exhausts iter_transitions, including empty NFA target entries.
        Recursive Tarjan may exceed Python's recursion limit on deep graphs.

        References
        ----------
        Professor requirement #14: accessible and coaccessible cycle, as
        supplied in the prompt; the source PDFs were not accessed. A cycle
        must consume input to make the language genuinely infinite, as
        explicitly clarified by the user. ADR-0005: useful states.
        ADR-0009: cycle-analysis layer. ADR-0010: productive-cycle policy.
        """
        useful = self.useful_states()
        if not useful:
            return True

        component_ids: dict[FAStateT, int] = {}
        for component_id, component in enumerate(
            self.strongly_connected_components()
        ):
            for state in component:
                if state in useful:
                    component_ids[state] = component_id

        for source, target, label in self.iter_transitions():
            if (
                label != ""
                and source in component_ids
                and component_ids.get(source) == component_ids.get(target)
            ):
                return False
        return True
