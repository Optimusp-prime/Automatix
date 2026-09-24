"""Uncached epsilon reachability for nondeterministic automata."""

from collections.abc import Iterable
from typing import FrozenSet, cast

from automata.base.exceptions import InvalidStateError
from automata.fa.fa import FAStateT
from automata.fa.nfa import NFA


class EpsilonMixin:
    """Compute single-source and multi-source epsilon closures."""

    def epsilon_closure(self, state: FAStateT) -> FrozenSet[FAStateT]:
        """Return states reachable from state using only epsilon edges.

        Parameters
        ----------
        state : FAStateT
            Starting state, including None when it is an actual state.

        Returns
        -------
        FrozenSet[FAStateT]
            Epsilon closure, including state itself. No source mutation or
            cache is introduced.

        Raises
        ------
        InvalidStateError
            If state is absent or unhashable, as for dfs(start_state).

        Complexity
        ----------
        O(|Q_e| + |E_e|) time and O(|Q_e|) space, where Q_e and E_e are
        the states and epsilon edges reached. Hashing is expected O(1).

        References
        ----------
        Professor requirement #34; supplied mature EpsilonMixin excerpt.
        automata-lib 9.2.0 NFA represents epsilon by the empty string.
        """
        return self.epsilon_closure_of_set((state,))

    def epsilon_closure_of_set(
        self, states: Iterable[FAStateT]
    ) -> FrozenSet[FAStateT]:
        """Return the union of epsilon closures of the supplied states.

        Parameters
        ----------
        states : Iterable[FAStateT]
            Seeds, consumed once and validated before traversal. Duplicates
            are harmless and an empty iterable is permitted.

        Returns
        -------
        FrozenSet[FAStateT]
            All seeds and states reachable through zero or more epsilon
            transitions. Consuming transitions are ignored. Empty input
            returns frozenset(). The source remains unchanged, without caching.

        Raises
        ------
        InvalidStateError
            If any seed is absent or unhashable.

        Complexity
        ----------
        O(k + |Q_e| + |E_e|) time and O(|Q_e|) auxiliary/result space,
        for k input items and the reached epsilon subgraph Q_e, E_e.
        Assumes expected constant-time state hashing and mapping lookups.

        References
        ----------
        Professor requirement #34: epsilon-transition traversal.
        ADR-0004 start-state validation policy; mature EpsilonMixin excerpt.
        """
        nfa = cast(NFA, self)
        visited: set[FAStateT] = set()
        for state in states:
            try:
                hash(state)
                valid = state in nfa.states
            except TypeError:
                valid = False
            if not valid:
                raise InvalidStateError(f"{state!r} is not a valid state")
            visited.add(state)

        pending = list(visited)
        while pending:
            current = pending.pop()
            for target in nfa.transitions.get(current, {}).get("", ()):
                if target not in visited:
                    visited.add(target)
                    pending.append(target)
        return frozenset(visited)
