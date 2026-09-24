"""Epsilon removal by propagation through the extension's closures."""

from typing import TYPE_CHECKING, FrozenSet, Self, cast

from automata.fa.fa import FAStateT

if TYPE_CHECKING:
    from automata_extensions.fa.nfa import ExtendedNFA


class EliminationMixin:
    """Construct epsilon-free NFAs without removing original states."""

    def remove_epsilon_transitions(self) -> Self:
        """Return an equivalent NFA with no epsilon transition keys.

        For each q and input symbol a, propagate a-transitions from the
        epsilon closure of q, then close their destinations under epsilon.
        Mark q final exactly when its closure contains an original final.

        Returns
        -------
        Self
            A new ExtendedNFA of the same concrete type, preserving all
            states, the alphabet and initial state. No trimming,
            determinization or minimization occurs. Empty destination sets
            are omitted. The source is unchanged and no cache is added.

        Complexity
        ----------
        Let n=|Q|, s=|Sigma|, e be the epsilon-edge count, and M the maximum
        total destinations for one symbol over Q. Time is
        O(n*(n+e) + n*s*(n+M+e) + V). A single-state closure is computed
        once per q; each move closure is recomputed without a cache.
        Peak space is O(n + n*n*s + V_space), including the possibly dense
        result. V/V_space cover constructor freezing and validation.
        Bounds assume expected constant-time state hashing and lookups.

        References
        ----------
        Professor requirement #37: epsilon-closure propagation.
        Requirement #34 supplies both closure APIs. Supplied mature
        EliminationMixin contract; automata-lib 9.2.0 NFA representation.
        """
        nfa = cast("ExtendedNFA", self)
        transitions: dict[FAStateT, dict[str, FrozenSet[FAStateT]]] = {}
        finals: set[FAStateT] = set()
        for state in nfa.states:
            closure = nfa.epsilon_closure(state)
            if not closure.isdisjoint(nfa.final_states):
                finals.add(state)
            paths: dict[str, FrozenSet[FAStateT]] = {}
            for symbol in nfa.input_symbols:
                move: set[FAStateT] = set()
                for reached in closure:
                    move.update(nfa.transitions.get(reached, {}).get(symbol, ()))
                targets = nfa.epsilon_closure_of_set(move)
                if targets:
                    paths[symbol] = targets
            transitions[state] = paths

        return cast(Self, type(nfa)(
            states=nfa.states, input_symbols=nfa.input_symbols,
            transitions=transitions, initial_state=nfa.initial_state,
            final_states=finals,
        ))

    def eliminate_lambda(self) -> Self:
        """Delegate to the extension's epsilon-elimination transformation.

        Returns
        -------
        Self
            A fresh ExtendedNFA, equivalent and epsilon-free, retaining all
            original states. Unlike upstream elimination, no unreachable
            states are removed and no cached NetworkX closures are used.

        Complexity
        ----------
        O(1) wrapper overhead plus remove_epsilon_transitions() costs,
        including repeated closures and construction of the result.

        References
        ----------
        Supplied mature compatibility alias for requirement #37;
        automata-lib 9.2.0 NFA.eliminate_lambda(self) -> Self signature.
        """
        return self.remove_epsilon_transitions()
