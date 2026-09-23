"""Structural isomorphism of deterministic finite automata."""

from __future__ import annotations

from collections import deque
from typing import cast

from automata.fa.dfa import DFA
from automata.fa.fa import FAStateT


class IsomorphismMixin:
    """Compare DFA structure up to a bijective renaming of states."""

    def is_isomorphic_to(self, other: DFA) -> bool:
        """Test for a state bijection preserving initial, final and labeled edges.

        Missing transitions are structural too. Every state participates,
        including states unreachable from the initial state. Neither DFA is
        modified.

        Parameters
        ----------
        other : DFA
            DFA to compare with this one.

        Returns
        -------
        bool
            Whether a structure-preserving bijection exists.

        Complexity
        ----------
        Propagating one candidate mapping costs O(|Q| × |Sigma|). With
        unreachable states, backtracking may inspect factorially many
        candidates: O(|Q|! × |Q|² × |Sigma|) worst-case time and
        O(|Q|² + |Q| × |Sigma|) auxiliary space, including recursion and
        copied partial mappings. Python's recursion limit applies to very
        large state sets.

        References
        ----------
        Professor requirement #26: automaton isomorphism by state renaming.
        """
        left = cast(DFA, self)
        if (
            len(left.states) != len(other.states)
            or left.input_symbols != other.input_symbols
            or len(left.final_states) != len(other.final_states)
        ):
            return False

        def signature(
            dfa: DFA, state: FAStateT
        ) -> tuple[bool, frozenset[str], frozenset[str]]:
            paths = dfa.transitions[state]
            return (
                state in dfa.final_states,
                frozenset(paths),
                frozenset(
                    symbol for symbol, target in paths.items() if target == state
                ),
            )

        left_signatures = {state: signature(left, state) for state in left.states}
        right_signatures = {state: signature(other, state) for state in other.states}

        def propagate(
            mapping: dict[FAStateT, FAStateT],
            inverse: dict[FAStateT, FAStateT],
            start: tuple[FAStateT, FAStateT],
        ) -> tuple[dict[FAStateT, FAStateT], dict[FAStateT, FAStateT]] | None:
            extended = mapping.copy()
            reversed_mapping = inverse.copy()
            pending = deque([start])
            expanded: set[FAStateT] = set()

            while pending:
                source, target = pending.popleft()
                if (
                    (source in extended and extended[source] != target)
                    or (
                        target in reversed_mapping
                        and reversed_mapping[target] != source
                    )
                    or left_signatures[source] != right_signatures[target]
                ):
                    return None
                extended[source] = target
                reversed_mapping[target] = source
                if source in expanded:
                    continue
                expanded.add(source)
                for symbol, destination in left.transitions[source].items():
                    pending.append((destination, other.transitions[target][symbol]))

            return extended, reversed_mapping

        def search(
            mapping: dict[FAStateT, FAStateT],
            inverse: dict[FAStateT, FAStateT],
        ) -> bool:
            if len(mapping) == len(left.states):
                return True
            source = next(state for state in left.states if state not in mapping)
            for target in other.states:
                if target in inverse or left_signatures[source] != right_signatures[target]:
                    continue
                extended = propagate(mapping, inverse, (source, target))
                if extended is not None and search(*extended):
                    return True
            return False

        initial = propagate({}, {}, (left.initial_state, other.initial_state))
        return initial is not None and search(*initial)
