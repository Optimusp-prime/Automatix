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
    """Expose DFA table-filling analysis without later minimization APIs."""

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
