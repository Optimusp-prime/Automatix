"""Accessibility analyses built on the common finite-automaton traversal."""

from collections.abc import Set
from typing import FrozenSet, Protocol

from automata.fa.fa import FAStateT

from automata_extensions.fa.fa_mixins.graph import (
    _build_predecessors,
    _GraphSource,
)


class _FinalGraphSource(_GraphSource, Protocol):
    """Read-only graph and accepting states for reverse exploration."""

    @property
    def final_states(self) -> Set[FAStateT]:
        """Return the accepting states, including GNFA's unique final."""
        ...


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


class _CoaccessibleStatesQuery(Protocol):
    """Read-only set query required by the coaccessibility predicate."""

    def coaccessible_states(self) -> FrozenSet[FAStateT]:
        """Return states from which a final state can be reached."""
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

    def coaccessible_states(self: _FinalGraphSource) -> FrozenSet[FAStateT]:
        """Return all states from which a final state is reachable.

        A coaccessible state is a state from which at least one final state
        is reachable through zero or more transitions. Every final state
        is included, even if unreachable from the initial state. Epsilon
        transitions are edges; GNFA None labels represent absent edges.

        Returns
        -------
        FrozenSet[FAStateT]
            An immutable, unordered set without duplicates. With no final
            states, the result is empty. No source data or cache is modified.

        Complexity
        ----------
        Build inverse adjacency once in O(|Q| + T) time and O(|Q| + |E|)
        space. Q contains all states, E the emitted transitions including
        parallel edges, and T is the cost of exhausting iter_transitions.
        T includes empty NFA target-set entries and stored GNFA None labels.
        The multi-source traversal costs O(|Q_co| + |E_co|), where Q_co is
        the coaccessible set and E_co the reverse edges examined from it.
        Freezing the result adds O(|Q_co|) time and space. Overall:
        O(|Q| + T) time and O(|Q| + |E|) space, assuming constant-time state
        hashing and equality. Adjacency is built even with no final states.

        References
        ----------
        Professor requirement #5 and AccessibilityMixin excerpts supplied
        in the task prompt; the source PDFs were not accessed.
        ADR-0005: common accessibility analysis layer.
        ADR-0006: private reverse graph foundation.
        """
        predecessors = _build_predecessors(self)
        visited = set(self.final_states)
        pending = list(visited)
        while pending:
            state = pending.pop()
            for predecessor in predecessors[state]:
                if predecessor not in visited:
                    visited.add(predecessor)
                    pending.append(predecessor)
        return frozenset(visited)

    def is_coaccessible(
        self: _CoaccessibleStatesQuery, state: FAStateT
    ) -> bool:
        """Return whether state can reach a final state in zero or more steps.

        Parameters
        ----------
        state : FAStateT
            State value to test. None is treated as an ordinary state.

        Returns
        -------
        bool
            True exactly when state belongs to coaccessible_states(). An
            unreachable state or a hashable value absent from the automaton
            returns False.

        Raises
        ------
        TypeError
            If state cannot be used as a frozenset membership key, such as
            a list. Native membership behavior is preserved.

        Complexity
        ----------
        Recomputing coaccessible_states costs O(|Q| + T) time and
        O(|Q| + |E|) space, including inverse adjacency construction,
        multi-source traversal and result creation. Q contains all states,
        E all emitted transitions including parallel edges, and T is the
        cost of exhausting iter_transitions, including empty NFA target-set
        entries and stored GNFA None labels. The final membership test is
        expected O(1), but the complete query has the stated bounds without
        caching, assuming constant-time state hashing and equality.

        References
        ----------
        Professor requirement #6: membership in the coaccessible state set,
        as supplied in the task prompt; the source PDFs were not accessed.
        ADR-0005: common accessibility analysis layer.
        ADR-0006: private reverse graph foundation.
        """
        return state in self.coaccessible_states()
