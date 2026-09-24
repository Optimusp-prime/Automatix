"""Word quotients specialized for nondeterministic automata."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from automata.fa.fa import FAStateT

from automata_extensions.fa.fa_mixins.quotient import _right_quotient_via_reversal

if TYPE_CHECKING:
    from automata_extensions.fa.nfa import ExtendedNFA


class NFAQuotientMixin:
    """Construct word quotients without determinizing an NFA."""

    def left_quotient_word(self, word: str) -> ExtendedNFA:
        """Return an NFA for the language ``{u | word + u in L(self)}``.

        Reuse the final configuration of ``execution_trace``; upstream
        includes epsilon closure before and after consuming symbols. A
        collision-free new initial state has epsilon edges to all reached
        states. If none were reached, it has no outgoing edges and the
        result recognizes the empty language. The source is unchanged.

        Parameters
        ----------
        word : str
            Word to remove from the left, possibly empty.

        Returns
        -------
        ExtendedNFA
            Fresh same-alphabet quotient with the original final states.

        Complexity
        ----------
        The upstream trace simulation depends on ``|word|``, active-state
        sets and epsilon closures; materializing its configurations can
        take O(|word| × |Q|) space. Copying states/transitions adds
        O(|Q| + T) time/space, plus constructor validation V/M. No cache or
        determinization is introduced.

        References
        ----------
        Professor requirement #47 and the supplied mature
        ``left_quotient_word`` example. Reuses requirement #16 execution
        trace and upstream NFA epsilon semantics. Upstream NFA.left_quotient
        instead takes another automaton and remains untouched.
        """
        source = cast("ExtendedNFA", self)
        active = frozenset(source.execution_trace(word)[-1])
        states: set[FAStateT] = set(source.states)
        initial = source._add_new_state(states)
        transitions = {
            state: {
                symbol: set(destinations)
                for symbol, destinations in paths.items()
            }
            for state, paths in source.transitions.items()
        }
        transitions[initial] = {"": set(active)} if active else {}
        return type(source)(
            states=states,
            input_symbols=source.input_symbols,
            transitions=transitions,
            initial_state=initial,
            final_states=source.final_states,
        )

    def right_quotient_word(self, word: str) -> ExtendedNFA:
        """Return an NFA for the language ``{u | u + word in L(self)}``.

        Use the professor's reverse/left-quotient/reverse duality, including
        reversal of the supplied word. The source is unchanged.

        Parameters
        ----------
        word : str
            Word to remove from the right, possibly empty.

        Returns
        -------
        ExtendedNFA
            Fresh quotient with the same input alphabet.

        Complexity
        ----------
        Two upstream NFA reversals and one NFA left quotient copy and
        validate their intermediate graphs. Time is their combined
        O(|Q| + T + V) construction costs plus upstream simulation of
        ``word``; peak space includes the O(|word| × |Q|) trace and the
        largest intermediate transition table. No determinization occurs.

        References
        ----------
        Professor requirement #48; requirements #36 and #47. Upstream
        NFA.right_quotient takes an automaton, not a word, and is untouched.
        """
        source = cast("ExtendedNFA", self)
        return _right_quotient_via_reversal(source, word)
