"""Accessibility analyses built on the common finite-automaton traversal."""

from typing import FrozenSet, Protocol

from automata.fa.fa import FAStateT


class _InitialTraversal(Protocol):
    """Minimal traversal interface required by accessibility queries."""

    def dfs(self) -> list[FAStateT]:
        """Return states discovered from the initial state."""
        ...


class _AccessibleStatesQuery(Protocol):
    """Read-only set query required by the accessibility predicate."""

    def accessible_states(self) -> FrozenSet[FAStateT]:
        """Return the states accessible from the initial state."""
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

    def is_accessible(
        self: _AccessibleStatesQuery, state: FAStateT
    ) -> bool:
        """Return whether the given state is reachable from the initial state.

        Parameters
        ----------
        state : FAStateT
            State value to query using native frozenset membership semantics.
            None is treated as an ordinary value, with no default meaning.

        Returns
        -------
        bool
            True exactly when state belongs to accessible_states(). An
            unreachable state or a hashable value absent from the automaton
            returns False. No source data or cached state is modified.

        Raises
        ------
        TypeError
            If state cannot be used as a frozenset membership key, for
            example a list. Native membership behavior is not overridden.

        Complexity
        ----------
        Recomputing accessible_states costs O(|Q| + T) time and
        O(|Q| + |E|) space, including adjacency construction, traversal and
        result creation. Q contains all states, E all emitted transitions,
        and T is the cost of exhausting iter_transitions, including empty
        NFA target-set entries and stored GNFA None labels. The final
        membership test is expected O(1), but the complete query remains
        O(|Q| + T) time and O(|Q| + |E|) space without caching, assuming
        constant-time state hashing and equality.

        References
        ----------
        Professor requirement #4: membership in the accessible state set,
        as supplied in the task prompt; the source PDFs were not accessed.
        ADR-0005: common accessibility analysis layer.
        The absent-state policy is a project choice based on membership
        semantics, not an additional contract attributed to the professor.
        """
        return state in self.accessible_states()
