"""Graph traversal shared by DFA, NFA and GNFA extensions."""

from collections import deque
from collections.abc import Iterator
from typing import Final

from automata.base.exceptions import InvalidStateError
from automata.fa.fa import FAStateT

from automata_extensions.fa.fa_mixins.graph import (
    _GraphSource,
    _Successors,
    _build_successors,
)

_DEFAULT_START: Final = object()


def _dfs_iterative(
    start: FAStateT, successors: _Successors
) -> list[FAStateT]:
    """Explore one branch at a time using a stack of neighbor iterators."""
    visited: set[FAStateT] = {start}
    order: list[FAStateT] = [start]
    stack: list[Iterator[FAStateT]] = [iter(successors[start])]

    while stack:
        try:
            neighbor = next(stack[-1])
        except StopIteration:
            stack.pop()
            continue

        if neighbor not in visited:
            visited.add(neighbor)
            order.append(neighbor)
            stack.append(iter(successors[neighbor]))

    return order


def _dfs_recursive(
    start: FAStateT, successors: _Successors
) -> list[FAStateT]:
    """Explore descendants recursively before returning to sibling edges."""
    visited: set[FAStateT] = set()
    order: list[FAStateT] = []

    def visit(state: FAStateT) -> None:
        visited.add(state)
        order.append(state)
        for neighbor in successors[state]:
            if neighbor not in visited:
                visit(neighbor)

    visit(start)
    return order


class TraversalMixin:
    """Provide traversal without storing state or changing the automaton."""

    def dfs(
        self: _GraphSource,
        start_state: FAStateT = _DEFAULT_START,
        *,
        recursive: bool = False,
    ) -> list[FAStateT]:
        """Return states in depth-first discovery order from one start state.

        Parameters
        ----------
        start_state : FAStateT, optional
            A state of this automaton. If omitted, use initial_state.
            Explicit None selects the actual state None, not the default.
            States must be hashable, as required by upstream containers.
        recursive : bool, default: False
            Use an explicit stack by default; True uses recursive calls.

        Returns
        -------
        list[FAStateT]
            A fresh list containing every reachable state exactly once,
            with the start state first. Labels are ignored, including
            epsilon labels. Sibling order follows iter_transitions without
            sorting; it is not necessarily lexical or stable across runs.
            Both variants use the same order for the same transition stream.
            The source automaton is unchanged and no cache is populated.

        Raises
        ------
        InvalidStateError
            If the supplied start state is not in states, including an
            unhashable argument. None is invalid unless it is a state.
        RecursionError
            If recursive=True exceeds Python's recursion limit. Use the
            default iterative variant for deep graphs; no limit is changed.

        Complexity
        ----------
        Adjacency construction: O(|Q| + T) time and O(|Q| + |E|) space.
        Q contains all states, E all transitions emitted by iter_transitions,
        and T is the time to exhaust that iterator. For DFA, T is O(|Q|+|E|).
        NFA also scans symbol entries with empty target sets; GNFA scans
        stored None-labelled entries even though they emit no edge.
        Traversal after construction: O(|Q_reached| + |E_reached|) time
        and O(|Q_reached|) additional space, including the stack and result.
        Overall time: O(|Q| + T); overall space: O(|Q| + |E|).
        These bounds assume constant-time state hashing and equality.

        References
        ----------
        Professor requirement #1: iterative and recursive DFS.
        Reference extension documentation: TraversalMixin.dfs returns a
        list and is iterative by default (excerpts supplied for this task).
        automata-lib 9.2.0: FA.iter_transitions and concrete implementations.
        ADR-0004: graph traversal foundation and start-state contract.
        """
        start = (
            self.initial_state
            if start_state is _DEFAULT_START
            else start_state
        )
        try:
            hash(start)
            valid_start = start in self.states
        except TypeError:
            valid_start = False
        if not valid_start:
            raise InvalidStateError(f"{start!r} is not a valid start state")

        successors = _build_successors(self)
        if recursive:
            return _dfs_recursive(start, successors)
        return _dfs_iterative(start, successors)

    def bfs(
        self: _GraphSource,
        start_state: FAStateT = _DEFAULT_START,
    ) -> list[FAStateT]:
        """Return states in breadth-first discovery order from one start.

        Parameters
        ----------
        start_state : FAStateT, optional
            A state of this automaton. If omitted, use initial_state.
            Explicit None selects the actual state None, not the default.
            States must be hashable, as required by upstream containers.

        Returns
        -------
        list[FAStateT]
            A fresh list containing every reachable state exactly once,
            with the start state first, in nondecreasing graph distance.
            Every transition counts as one edge, including epsilon edges.
            Ties follow discovery through the neighbor order supplied by
            iter_transitions. States are not sorted; this order need not
            be lexical or stable across runs. The source automaton is
            unchanged and no cache is populated.

        Raises
        ------
        InvalidStateError
            If the supplied start state is not in states, including an
            unhashable argument. None is invalid unless it is a state.

        Complexity
        ----------
        Adjacency construction: O(|Q| + T) time and O(|Q| + |E|) space.
        Q contains all states, E all transitions emitted by iter_transitions,
        and T is the time to exhaust that iterator. For DFA, T is O(|Q|+|E|).
        NFA also scans symbol entries with empty target sets; GNFA scans
        stored None-labelled entries even though they emit no edge.
        BFS after construction: O(|Q_reached| + |E_reached|) time and
        O(|Q_reached|) additional space for the queue, visited set and list.
        Overall time: O(|Q| + T); overall space: O(|Q| + |E|).
        These bounds assume constant-time state hashing and equality.

        References
        ----------
        Professor requirement #2: breadth-first exploration using a queue.
        Reference extension documentation: TraversalMixin.bfs starts at
        the initial state or a given state (excerpt supplied for this task).
        automata-lib 9.2.0: FA.iter_transitions and concrete implementations.
        ADR-0004: graph traversal foundation and start-state contract.
        """
        start = (
            self.initial_state
            if start_state is _DEFAULT_START
            else start_state
        )
        try:
            hash(start)
            valid_start = start in self.states
        except TypeError:
            valid_start = False
        if not valid_start:
            raise InvalidStateError(f"{start!r} is not a valid start state")

        successors = _build_successors(self)
        visited: set[FAStateT] = {start}
        order: list[FAStateT] = [start]
        queue: deque[FAStateT] = deque([start])

        while queue:
            state = queue.popleft()
            for neighbor in successors[state]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    order.append(neighbor)
                    queue.append(neighbor)

        return order
