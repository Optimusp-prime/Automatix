"""Brzozowski minimization through the existing reversal and subset APIs."""

from __future__ import annotations

from typing import TYPE_CHECKING, FrozenSet, cast

from automata.fa.fa import FAStateT

if TYPE_CHECKING:
    from automata_extensions.fa.dfa import ExtendedDFA
    from automata_extensions.fa.nfa import ExtendedNFA


def _determinize_logical_reverse(reversed_nfa: ExtendedNFA) -> ExtendedDFA:
    """Discard only the epsilon-start identity added by this reverse()."""
    auxiliary = reversed_nfa.initial_state
    if (
        auxiliary in reversed_nfa.final_states
        or set(reversed_nfa.transitions[auxiliary]) != {""}
    ):
        raise AssertionError("reverse() no longer has an epsilon-only fresh start")

    determinized = reversed_nfa.determinize()

    # No edge of reverse() enters its fresh initial state. Thus only the
    # initial subset can contain it, and removing it changes no future moves
    # or finality. Its logical subset may already have a DFA state.
    names: dict[FAStateT, FrozenSet[FAStateT]] = {
        state: frozenset(cast(FrozenSet[FAStateT], state) - {auxiliary})
        for state in determinized.states
    }
    transitions: dict[FrozenSet[FAStateT], dict[str, FrozenSet[FAStateT]]] = {}
    for state, paths in determinized.transitions.items():
        named = names[state]
        mapped = {symbol: names[target] for symbol, target in paths.items()}
        if named in transitions and transitions[named] != mapped:
            raise AssertionError("reverse-start normalization changed transitions")
        transitions[named] = mapped

    finals = {names[state] for state in determinized.final_states}
    for state in determinized.states:
        if (state in determinized.final_states) != (names[state] in finals):
            raise AssertionError("reverse-start normalization changed finality")

    return type(determinized)(
        states=set(names.values()),
        input_symbols=determinized.input_symbols,
        transitions=transitions,
        initial_state=names[determinized.initial_state],
        final_states=finals,
        allow_partial=determinized.allow_partial,
    )


class BrzozowskiMixin:
    """Minimize DFA/NFA languages by two logical reversals."""

    def brzozowski_minimize(self) -> ExtendedDFA:
        """Return a minimal DFA by reversing and determinizing twice.

        The existing ``reverse()`` uses a fresh epsilon-only initial NFA
        state to encode the reversed set of initial states. After each
        verified ``determinize()``, a private normalization removes only
        that fresh state's identity from subset labels. It may merge the
        resulting duplicate subset, but performs no general minimization.
        The source automaton is unchanged.

        Returns
        -------
        ExtendedDFA
            Fresh minimal deterministic automaton for the source language.

        Complexity
        ----------
        Two reversals, two reachable-subset constructions and two linear
        output rebuilds. Each determinization can discover exponentially
        many subsets of its input NFA; the second input may itself be
        exponentially larger than the original. Time and space are bounded
        by the generated intermediate graphs and their constructor
        validation, not by ordinary DFA partition-refinement bounds.

        References
        ----------
        Professor requirement #50; classical Brzozowski algorithm.
        Reuses requirements #36 (reverse) and #35 (determinize).
        ADR-0016 records the single-initial-state representation bridge.
        """
        source = cast("ExtendedDFA | ExtendedNFA", self)
        first_dfa = _determinize_logical_reverse(source.reverse())
        return _determinize_logical_reverse(first_dfa.reverse())
