"""Accessible subset construction using the extension's epsilon closures."""

from collections import deque
from typing import TYPE_CHECKING, FrozenSet, cast

from automata.fa.fa import FAStateT

if TYPE_CHECKING:
    from automata_extensions.fa.dfa import ExtendedDFA
    from automata_extensions.fa.nfa import ExtendedNFA


class DeterminizationMixin:
    """Transform an NFA into a language-equivalent ExtendedDFA."""

    def determinize(self) -> "ExtendedDFA":
        """Construct a DFA over the reachable epsilon-closed state subsets.

        Returns
        -------
        ExtendedDFA
            A new language-equivalent DFA with the same alphabet. States
            are frozensets of source states, initially the epsilon closure
            of the source initial state. A subset is final exactly when it
            contains a source final state. Empty destination subsets are
            omitted, yielding a partial DFA when necessary, as in upstream
            DFA.from_nfa(..., retain_names=True, minify=False). No renaming
            or minimization occurs. The source is unchanged; no cache is added.

        Complexity
        ----------
        Let n = |Q|, R be the number of discovered subsets, s = |Sigma|,
        M the maximum number of destinations examined for one symbol over
        Q, and e the total epsilon-edge count. Time is
        O(n + e + R*s*(n + M + e) + V), including subset hashing and
        constructor freezing/validation V. R can be as large as 2**n.
        Peak space is O(R*n*(1 + s) + n + V_space): stored subsets, fresh
        destination frozensets on edges, local move/closure work and
        constructor workspace. Equal target sets need not share identity.
        These bounds assume expected constant-time original-state hashing;
        no global powerset or closure cache is constructed.

        References
        ----------
        Professor requirement #35: accessible subset construction.
        Supplied mature DeterminizationMixin APIs; requirement #34 closures.
        automata-lib 9.2.0 DFA.from_nfa, DFA._expand_dfa and
        NFA._iterate_through_symbol_path_pairs (partial-result convention).
        """
        from automata_extensions.fa.dfa import ExtendedDFA

        nfa = cast("ExtendedNFA", self)
        initial = nfa.epsilon_closure(nfa.initial_state)
        transitions: dict[FrozenSet[FAStateT], dict[str, FrozenSet[FAStateT]]] = {
            initial: {}
        }
        finals: set[FrozenSet[FAStateT]] = set()
        pending = deque([initial])
        while pending:
            subset = pending.popleft()
            if not subset.isdisjoint(nfa.final_states):
                finals.add(subset)
            for symbol in nfa.input_symbols:
                move: set[FAStateT] = set()
                for state in subset:
                    move.update(nfa.transitions.get(state, {}).get(symbol, ()))
                target = nfa.epsilon_closure_of_set(move)
                if not target:
                    continue
                transitions[subset][symbol] = target
                if target not in transitions:
                    transitions[target] = {}
                    pending.append(target)

        return ExtendedDFA(
            states=frozenset(transitions), input_symbols=nfa.input_symbols,
            transitions=transitions, initial_state=initial, final_states=finals,
            allow_partial=any(
                len(paths) != len(nfa.input_symbols)
                for paths in transitions.values()
            ),
        )

    def to_dfa(self) -> "ExtendedDFA":
        """Return determinize(), the pedagogical alias for NFA conversion.

        Returns
        -------
        ExtendedDFA
            A fresh DFA with frozenset states and the same language.

        Complexity
        ----------
        The wrapper adds O(1) time/space to determinize(); reachable subset
        construction can produce exponentially many states. See determinize
        for the move, closure, storage and constructor bounds.

        References
        ----------
        Professor requirement #35 and supplied mature to_dfa alias example.
        """
        return self.determinize()
