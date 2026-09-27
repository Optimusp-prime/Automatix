"""Strongly connected components of a finite automaton's transition graph."""

from typing import FrozenSet, Protocol

from automata.fa.fa import FAStateT

from automata_extensions.fa.fa_mixins.graph import _build_successors, _GraphSource


class _SCCQuery(Protocol):
    """Existing partition operation needed by the connectivity predicate."""

    def strongly_connected_components(self) -> list[FrozenSet[FAStateT]]: ...


class SCCMixin:
    """Analyze strongly connected components using the common graph layer."""

    def is_strongly_connected(self: _SCCQuery) -> bool:
        """Test whether every state can reach every other state.

        The test uses the existing complete Tarjan partition. A valid
        upstream finite automaton has at least one state, so a singleton
        without a loop is strongly connected by the zero-length path.
        The source is unchanged.

        Returns
        -------
        bool
            True exactly when all states form one component.

        Complexity
        ----------
        O(|Q| + T) expected time and O(|Q| + |E|) space, inherited from
        ``strongly_connected_components``. Q is the number of states,
        E the emitted edges and T the upstream transition scan cost.

        References
        ----------
        Mature SCCMixin example; professor requirement #10; ADR-0008.
        """
        return len(self.strongly_connected_components()) == 1

    def strongly_connected_components(
        self: _GraphSource,
    ) -> list[FrozenSet[FAStateT]]:
        """Partition all states into maximal mutually reachable components.

        Every state is included, even when inaccessible from the initial
        state. A singleton is a component with or without a self-loop.
        Component and member order have no mathematical significance.
        This query neither mutates the automaton nor stores a cache.

        Returns
        -------
        list[FrozenSet[FAStateT]]
            A list of disjoint, nonempty components whose union is all states.
            Each component is an immutable state set.

        Complexity
        ----------
        Building adjacency takes O(|Q| + T) time and O(|Q| + |E|) space,
        where Q is all states, E the emitted transitions including parallel
        edges, and T the cost of exhausting iter_transitions. Tarjan then
        takes O(|Q| + |E|) time and space. Overall: O(|Q| + T) time and
        O(|Q| + |E|) space, assuming constant-time state hashing and equality.
        T includes NFA empty target entries and GNFA stored None labels.
        Recursion depth can reach |Q| and is limited by Python's recursion
        limit on sufficiently deep graphs.

        References
        ----------
        Tarjan's strongly connected components algorithm; professor
        requirement #10 and the reference excerpts supplied in the task
        prompt (the source PDFs were not accessed). ADR-0004 supplies the
        common graph abstraction; ADR-0008 records this analysis layer.
        """
        successors = _build_successors(self)
        next_index = 0
        indices: dict[FAStateT, int] = {}
        lowlinks: dict[FAStateT, int] = {}
        stack: list[FAStateT] = []
        on_stack: set[FAStateT] = set()
        components: list[FrozenSet[FAStateT]] = []

        def strongconnect(state: FAStateT) -> None:
            nonlocal next_index

            indices[state] = next_index
            lowlinks[state] = next_index
            next_index += 1
            stack.append(state)
            on_stack.add(state)

            for neighbor in successors[state]:
                if neighbor not in indices:
                    strongconnect(neighbor)
                    lowlinks[state] = min(lowlinks[state], lowlinks[neighbor])
                elif neighbor in on_stack:
                    lowlinks[state] = min(lowlinks[state], indices[neighbor])

            if lowlinks[state] == indices[state]:
                component: set[FAStateT] = set()
                while True:
                    member = stack.pop()
                    on_stack.remove(member)
                    component.add(member)
                    if member == state:
                        break
                components.append(frozenset(component))

        for state in successors:
            if state not in indices:
                strongconnect(state)

        return components
