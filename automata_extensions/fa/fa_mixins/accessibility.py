"""Accessibility analyses built on the common finite-automaton traversal."""

from typing import FrozenSet, Protocol

from automata.fa.fa import FAStateT


class _InitialTraversal(Protocol):
    """Minimal traversal interface required by accessibility queries."""

    def dfs(self) -> list[FAStateT]:
        """Return states discovered from the initial state."""
        ...


class AccessibilityMixin:
    """Express accessibility properties without duplicating graph traversal."""

    def accessible_states(self: _InitialTraversal) -> FrozenSet[FAStateT]:
        """Return the states accessible from the initial state.

        An accessible state is a state reachable from the initial state
        through zero or more transitions. The initial state is therefore
        always included, even without outgoing transitions. Accessibility
        does not depend on whether a final state can be reached.
        Epsilon transitions are edges, as in the common traversal layer.

        Returns
        -------
        FrozenSet[FAStateT]
            An immutable set of accessible states, without traversal order
            or duplicates. Unreachable states are absent. The query does
            not modify the automaton or populate any cache.

        Complexity
        ----------
        Delegates once to the existing iterative DFS. Adjacency construction
        takes O(|Q| + T) time and O(|Q| + |E|) space: Q contains all states,
        E the emitted transitions (including parallel edges), and T is the
        cost of exhausting iter_transitions. DFS then takes
        O(|Q_reached| + |E_reached|) time and O(|Q_reached|) additional space.
        Building the result adds O(|Q_reached|) time and space.
        Overall: O(|Q| + T) time and O(|Q| + |E|) space, assuming constant-time
        state hashing and equality. T includes NFA empty target-set entries
        and GNFA stored None labels, even though these emit no edges.

        References
        ----------
        Professor requirement #3 and reference AccessibilityMixin excerpts
        supplied in the task prompt; the source PDFs were not accessed.
        ADR-0004: common graph traversal foundation.
        ADR-0005: accessibility analysis layer and immutable result contract.
        """
        return frozenset(self.dfs())
