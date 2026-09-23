"""Prefix-closed DFA language analysis."""

from typing import Protocol, Self, cast

from automata.fa.dfa import DFA
from automata.fa.fa import FAStateT


class _UsefulDFA(Protocol):
    """Only the existing useful-state query needed by the predicate."""

    def useful_states(self) -> frozenset[FAStateT]:
        """Return states on an accepting path."""
        ...


class PrefixMixin:
    """Analyze prefix closure of deterministic finite automata."""

    def is_prefix_closed(self) -> bool:
        """Return whether every useful state is final.

        Equivalently, every prefix of an accepted word is accepted.
        The empty language satisfies the criterion vacuously. This query
        does not modify the automaton or cache any result.

        Returns
        -------
        bool
            True exactly when the DFA language is prefix-closed.

        Complexity
        ----------
        O(|Q| + T) expected time and O(|Q| + |E|) auxiliary space.
        ``useful_states`` computes accessibility and coaccessibility over
        all states and emitted transitions; the final subset check adds
        at most O(|Q|) expected time. No adjacency is cached.

        References
        ----------
        Professor requirement #27: all useful states are final.
        """
        dfa = cast(DFA, self)
        useful = cast(_UsefulDFA, self)
        return useful.useful_states().issubset(dfa.final_states)

    def prefix_closed_sublanguage(self) -> Self:
        """Return the greatest prefix-closed sublanguage as a new DFA.

        Keep a transition exactly when both its source and destination are
        final in the source automaton. Preserve states, alphabet, initial
        state and final states. The source automaton is not modified.

        Returns
        -------
        Self
            Fresh ExtendedDFA accepting precisely the words whose every
            prefix was accepted by the source. The result may be partial.

        Complexity
        ----------
        O(|Q| + T + V) time and O(|Q| + T_kept + M) auxiliary space,
        where T counts inspected transitions, T_kept counts retained
        transitions, and V/M account for upstream construction and
        validation. Each state and transition is filtered once.

        References
        ----------
        Professor requirement #28: delete transitions that violate
        prefix closure. The supplied mature reference names this API.
        """
        dfa = cast(DFA, self)
        transitions: dict[FAStateT, dict[str, FAStateT]] = {}
        for state in dfa.states:
            transitions[state] = {}
            if state not in dfa.final_states:
                continue
            for symbol, destination in dfa.transitions[state].items():
                if destination in dfa.final_states:
                    transitions[state][symbol] = destination
        allow_partial = dfa.allow_partial or any(
            len(paths) < len(dfa.input_symbols)
            for paths in transitions.values()
        )
        return cast(
            Self,
            type(dfa)(
                states=dfa.states,
                input_symbols=dfa.input_symbols,
                transitions=transitions,
                initial_state=dfa.initial_state,
                final_states=dfa.final_states,
                allow_partial=allow_partial,
            ),
        )
