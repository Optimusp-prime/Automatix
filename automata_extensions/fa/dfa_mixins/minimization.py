"""DFA state distinguishability by iterative table filling."""

from collections import defaultdict, deque
from collections.abc import Mapping
from itertools import combinations
from types import MappingProxyType
from typing import Protocol, Self, TypeAlias, cast

from automata.fa.dfa import DFA
from automata.fa.fa import FAStateT


_StatePair: TypeAlias = frozenset[FAStateT]


class _CompletableDFA(Protocol):
    """Only the existing completion operation needed for partial DFA."""

    def complete(self) -> DFA: ...


class _DistinguishabilityQuery(Protocol):
    """Existing pair analysis reused by the equivalence partition."""

    def distinguishable_states(self) -> set[_StatePair]: ...


class _MinimizationQueries(Protocol):
    """Existing accessibility, restriction and partition operations."""

    def accessible_states(self) -> frozenset[FAStateT]: ...

    def induced_subautomaton(self, states: frozenset[FAStateT]) -> DFA: ...

    def equivalence_classes(self) -> list[frozenset[FAStateT]]: ...


def _pair_order_key(state: FAStateT) -> tuple[str, str, str, str]:
    """Order common and heterogeneous state labels deterministically."""
    return (str(state), type(state).__module__, type(state).__qualname__, repr(state))


def _distinguishability_table(dfa: DFA) -> dict[_StatePair, int]:
    """Record the first round marking each pair with one shared BFS."""
    pairs = [frozenset((p, q)) for p, q in combinations(dfa.states, 2)]
    rounds: dict[_StatePair, int] = {}
    pending: deque[_StatePair] = deque()
    dependents: dict[_StatePair, set[_StatePair]] = defaultdict(set)

    for pair in pairs:
        p, q = tuple(pair)
        if (p in dfa.final_states) != (q in dfa.final_states):
            rounds[pair] = 0
            pending.append(pair)
        for symbol in dfa.input_symbols:
            next_p = dfa.transitions[p][symbol]
            next_q = dfa.transitions[q][symbol]
            if next_p != next_q:
                dependents[frozenset((next_p, next_q))].add(pair)

    while pending:
        distinguished = pending.popleft()
        for pair in dependents[distinguished]:
            if pair not in rounds:
                rounds[pair] = rounds[distinguished] + 1
                pending.append(pair)

    return rounds


def _original_pair_rounds(source: DFA, completed: DFA) -> dict[_StatePair, int | None]:
    """Run table filling on the complete DFA and retain original pairs."""
    rounds = _distinguishability_table(completed)
    ordered = sorted(source.states, key=_pair_order_key)
    return {
        frozenset((p, q)): rounds.get(frozenset((p, q)))
        for p, q in combinations(ordered, 2)
    }


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
        rounds = _original_pair_rounds(original, completed)
        return {pair for pair, round_number in rounds.items() if round_number is not None}

    def pair_table(self) -> Mapping[_StatePair, int | None]:
        """Return all original DFA state pairs and their marking rounds.

        Final/nonfinal pairs have round 0. A pair first distinguished by
        a word of length k has round k. Equivalent pairs map to None.
        Partial DFAs are completed only for analysis; their synthetic
        sink never appears as a public key. The returned mapping is read
        only, with pair insertion order based on a safe state-label key.
        The source remains unchanged.

        Returns
        -------
        Mapping[frozenset[FAStateT], int | None]
            Every unordered pair of distinct original states and its
            shortest distinguishing-word length, or None.

        Complexity
        ----------
        O(|Q|² * |Sigma| + V + |Q| log |Q|) expected time and
        O(|Q|² * |Sigma| + M) space. Q is the source state set,
        Sigma its alphabet, and V/M upstream completion and validation
        time/space; state-key construction and comparison add their
        actual string costs.

        References
        ----------
        Mature MinimizationMixin pair-table description; primary #29;
        ADR-0023.
        """
        original = cast(DFA, self)
        completed = cast(_CompletableDFA, self).complete()
        return MappingProxyType(_original_pair_rounds(original, completed))

    def pair_table_str(self, show_round: bool = True) -> str:
        """Render the complete pair table as deterministic ASCII rows.

        The first line lists all but the last state. Row i lists state i
        followed by cells for pairs with the preceding states. With
        show_round=True, a marked pair shows its shortest distinguishing
        round and an equivalent pair shows a dot. Otherwise a marked pair
        shows X and an equivalent pair a dot. The one-space initial header
        for one-character labels follows the explicit M3 prompt example.
        A one-state DFA has no pairs and returns an empty string.

        Parameters
        ----------
        show_round : bool, default: True
            Display marking round numbers instead of X marks.

        Returns
        -------
        str
            Triangular table, without a terminal newline.

        Complexity
        ----------
        Pair analysis costs O(|Q|² * |Sigma| + V + |Q| log |Q|)
        expected time and O(|Q|² * |Sigma| + M) space. Formatting adds
        O(R) time and space for R output characters, including state
        labels; Q is states, Sigma the alphabet, V/M upstream completion
        and validation costs. No source mutation or cache is introduced.

        References
        ----------
        Mature MinimizationMixin pair-table description; M3 prompt's
        exact ASCII example; ADR-0023.
        """
        source = cast(DFA, self)
        ordered = sorted(source.states, key=_pair_order_key)
        if len(ordered) < 2:
            return ""
        table = self.pair_table()
        labels = [str(state) for state in ordered]
        row_width = max(map(len, labels))
        cell_width = max(
            1, *(len(label) for label in labels[:-1]),
            *(len(str(round_number)) for round_number in table.values()
              if round_number is not None),
        )
        header = " " * row_width + " ".join(
            label.rjust(cell_width) for label in labels[:-1]
        )
        rows = [header]
        for index, state in enumerate(ordered[1:], 1):
            cells: list[str] = []
            for previous in ordered[:index]:
                round_number = table[frozenset((previous, state))]
                token = (
                    str(round_number) if show_round else "X"
                ) if round_number is not None else "."
                cells.append(token.rjust(cell_width))
            rows.append(labels[index].rjust(row_width) + " " + " ".join(cells))
        return "\n".join(rows)

    def print_pair_table(self, show_round: bool = True) -> None:
        """Print exactly the triangular view followed by one newline.

        Parameters
        ----------
        show_round : bool, default: True
            Display marking rounds rather than X marks.

        Returns
        -------
        None
            The table is written to standard output.

        Complexity
        ----------
        O(|Q|² * |Sigma| + V + |Q| log |Q| + R) expected time and
        O(|Q|² * |Sigma| + M + R) space, delegated to pair_table_str.
        Q is states, Sigma the alphabet, V/M upstream completion and
        validation costs, and R the output length. Printing adds O(R)
        output work. The DFA is unchanged.

        References
        ----------
        Mature MinimizationMixin print_pair_table; ADR-0023.
        """
        print(self.pair_table_str(show_round=show_round))

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

    def is_minimal(self) -> bool:
        """Return whether every state is accessible and inequivalent.

        A DFA with an unreachable state is not minimal, even if all its
        Myhill–Nerode classes are singletons. The query does not mutate
        the automaton or construct a minimized one.

        Returns
        -------
        bool
            True exactly when all states are accessible and every
            equivalence class contains one state.

        Complexity
        ----------
        O(|Q| + T + |Q|² × |Sigma| + |Q|² × alpha(|Q|) + V)
        expected time and O(|Q|² × |Sigma| + |Q| + |E| + M)
        auxiliary space, including the delegated accessibility and
        equivalence-class analyses. V/M cover upstream validation.

        References
        ----------
        Professor requirement #31 and the supplied mature clarification:
        accessibility plus singleton Myhill–Nerode classes.
        """
        dfa = cast(DFA, self)
        queries = cast(_MinimizationQueries, self)
        return (
            queries.accessible_states() == dfa.states
            and all(len(group) == 1 for group in queries.equivalence_classes())
        )

    def minimize(self, *, keep_original_names: bool = False) -> Self:
        """Return a fresh minimal DFA recognizing the same language.

        Restrict to accessible states, partition them by Myhill–Nerode
        equivalence, and construct the quotient. By default an output state
        is its frozenset equivalence class. With ``keep_original_names``,
        an arbitrary member names each class, except that the initial
        state's class is named by the original initial state.

        For partial DFA, equivalent states can differ by an absent edge
        versus an edge to an empty-language class. Retaining any defined
        edge from a class preserves language and keeps all quotient classes
        reachable. The analysis-only completion trap is never exported.
        The source automaton is not modified.

        Parameters
        ----------
        keep_original_names : bool, default: False
            Name each quotient state by a member of its class instead of
            the class frozenset itself.

        Returns
        -------
        Self
            Fresh minimal ExtendedDFA with the same input alphabet and
            accepted language.

        Complexity
        ----------
        O(|Q| + T + |R|² × |Sigma| + |R|² × alpha(|R|) + V)
        expected time and O(|R|² × |Sigma| + |Q| + |E| + M)
        auxiliary space. R is the accessible-state set. V/M include the
        induced subautomaton and quotient constructors plus validation.
        Each accessible transition is inspected once for the quotient.

        References
        ----------
        Professor requirement #32: merge equivalent accessible states.
        Reuses requirements #3, #19 and #30, not upstream ``DFA.minify``.
        """
        dfa = cast(DFA, self)
        queries = cast(_MinimizationQueries, self)
        accessible = queries.accessible_states()
        reachable = queries.induced_subautomaton(accessible)
        classes = cast(_MinimizationQueries, reachable).equivalence_classes()

        class_of: dict[FAStateT, frozenset[FAStateT]] = {
            state: group for group in classes for state in group
        }
        name_of: dict[frozenset[FAStateT], FAStateT] = {}
        for group in classes:
            if keep_original_names:
                name_of[group] = (
                    dfa.initial_state if dfa.initial_state in group
                    else next(iter(group))
                )
            else:
                name_of[group] = group

        transitions: dict[FAStateT, dict[str, FAStateT]] = {}
        for group in classes:
            paths: dict[str, FAStateT] = {}
            for state in group:
                for symbol, destination in reachable.transitions[state].items():
                    target = name_of[class_of[destination]]
                    if symbol in paths and paths[symbol] != target:
                        raise AssertionError("equivalent states have conflicting destinations")
                    paths[symbol] = target
            transitions[name_of[group]] = paths

        final_states = {
            name_of[group]
            for group in classes
            if not group.isdisjoint(reachable.final_states)
        }
        allow_partial = reachable.allow_partial or any(
            len(paths) < len(reachable.input_symbols)
            for paths in transitions.values()
        )
        return cast(
            Self,
            type(dfa)(
                states=set(name_of.values()),
                input_symbols=dfa.input_symbols,
                transitions=transitions,
                initial_state=name_of[class_of[dfa.initial_state]],
                final_states=final_states,
                allow_partial=allow_partial,
            ),
        )
