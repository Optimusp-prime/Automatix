"""DFA state distinguishability by iterative table filling."""

from collections import defaultdict, deque
from itertools import combinations
from typing import Protocol, TypeAlias, cast

from automata.fa.dfa import DFA
from automata.fa.fa import FAStateT


_StatePair: TypeAlias = frozenset[FAStateT]


class _CompletableDFA(Protocol):
    """Only the existing completion operation needed for partial DFA."""

    def complete(self) -> DFA: ...


class _DistinguishabilityQuery(Protocol):
    """Existing pair analysis reused by the equivalence partition."""

    def distinguishable_states(self) -> set[_StatePair]: ...


def _distinguishability_table(dfa: DFA) -> set[_StatePair]:
    """Mark epsilon-distinct pairs, then propagate marks to predecessor pairs."""
    pairs = [frozenset((p, q)) for p, q in combinations(dfa.states, 2)]
    marked: set[_StatePair] = set()
    pending: deque[_StatePair] = deque()
    dependents: dict[_StatePair, set[_StatePair]] = defaultdict(set)

    for pair in pairs:
        p, q = tuple(pair)
        if (p in dfa.final_states) != (q in dfa.final_states):
            marked.add(pair)
            pending.append(pair)
        for symbol in dfa.input_symbols:
            next_p = dfa.transitions[p][symbol]
            next_q = dfa.transitions[q][symbol]
            if next_p != next_q:
                dependents[frozenset((next_p, next_q))].add(pair)

    while pending:
        for pair in dependents[pending.popleft()]:
            if pair not in marked:
                marked.add(pair)
                pending.append(pair)

    return marked


class MinimizationMixin:
    """Analyze DFA distinguishability and its induced state partition."""

    def distinguishable_states(self) -> set[frozenset[FAStateT]]:
        """Return unordered pairs distinguishable by some input word.

        Two distinct states are distinguishable when a word is accepted
        from exactly one of them. Final/nonfinal pairs are marked by the
        empty word; marks then propagate backward along equal symbols until
        no new pair is marked. All original states, including unreachable
        ones, participate. A partial DFA is completed only for analysis;
        pairs involving its synthetic trap are excluded from the result.

        Returns
        -------
        set[frozenset[FAStateT]]
            Distinguishable unordered pairs of distinct original states.

        Complexity
        ----------
        O(|Q|² × |Sigma| + V) expected time and
        O(|Q|² × |Sigma| + M) auxiliary space. Completion adds at most one
        state; each pair-symbol dependency is built once and each marked
        pair is processed once. V/M cover upstream completion and validation.
        Constant-time state hashing and mapping lookup are assumed.

        References
        ----------
        Professor requirement #29: iterative refinement of state pairs.
        The supplied mature reference describes table filling.
        """
        original = cast(DFA, self)
        completed = cast(_CompletableDFA, self).complete()
        marked = _distinguishability_table(completed)
        return {pair for pair in marked if pair.issubset(original.states)}

    def equivalence_classes(self) -> list[frozenset[FAStateT]]:
        """Partition all DFA states by Myhill–Nerode equivalence.

        States share a class exactly when no word distinguishes them.
        This includes unreachable states. Class order is unspecified,
        and the source automaton is not modified.

        Returns
        -------
        list[frozenset[FAStateT]]
            Nonempty, disjoint classes whose union is the full state set.

        Complexity
        ----------
        O(|Q|² × |Sigma| + |Q|² × alpha(|Q|) + V) expected time and
        O(|Q|² × |Sigma| + M) auxiliary space. The first term and V/M
        come from ``distinguishable_states``; union-find examines all
        O(|Q|²) pairs with inverse-Ackermann amortized operations.

        References
        ----------
        Professor requirement #30: stable partition of DFA states by
        non-distinguishability. Reuses requirement #29 table filling.
        """
        dfa = cast(DFA, self)
        distinguishable = cast(
            _DistinguishabilityQuery, self
        ).distinguishable_states()
        parent: dict[FAStateT, FAStateT] = {state: state for state in dfa.states}
        rank: dict[FAStateT, int] = {state: 0 for state in dfa.states}

        def find(state: FAStateT) -> FAStateT:
            while parent[state] != state:
                parent[state] = parent[parent[state]]
                state = parent[state]
            return state

        for p, q in combinations(dfa.states, 2):
            if frozenset((p, q)) in distinguishable:
                continue
            root_p, root_q = find(p), find(q)
            if root_p == root_q:
                continue
            if rank[root_p] < rank[root_q]:
                root_p, root_q = root_q, root_p
            parent[root_q] = root_p
            if rank[root_p] == rank[root_q]:
                rank[root_p] += 1

        groups: dict[FAStateT, set[FAStateT]] = defaultdict(set)
        for state in dfa.states:
            groups[find(state)].add(state)
        return [frozenset(group) for group in groups.values()]
