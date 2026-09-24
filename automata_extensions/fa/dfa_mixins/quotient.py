"""Word quotients specialized for deterministic automata."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from automata.fa.fa import FAStateT

from automata_extensions.fa.fa_mixins.quotient import _right_quotient_via_reversal

if TYPE_CHECKING:
    from automata_extensions.fa.dfa import ExtendedDFA


class DFAQuotientMixin:
    """Construct word quotients while preserving the ExtendedDFA type."""

    def left_quotient_word(self, word: str) -> ExtendedDFA:
        """Return a DFA for the language ``{u | word + u in L(self)}``.

        Read ``word`` from the original initial state, then rebuild the
        automaton with the reached state as its initial state. A missing
        transition (including an unknown symbol) yields a fresh empty-
        language representative. The source is unchanged.

        Parameters
        ----------
        word : str
            Word to remove from the left, possibly empty.

        Returns
        -------
        ExtendedDFA
            Fresh same-alphabet quotient without trimming or minimization.

        Complexity
        ----------
        O(|word| + |Q| + T + V) time and O(|Q| + T + M) space,
        including copying the DFA and upstream constructor validation V/M.
        T counts stored transition entries. On a missing edge, the existing
        empty-language restriction helper builds a smaller representative.

        References
        ----------
        Professor requirement #47 and the supplied mature
        ``left_quotient_word`` example. The ``_word`` suffix avoids upstream
        NFA.left_quotient, whose argument is an automaton.
        """
        source = cast("ExtendedDFA", self)
        current: FAStateT = source.initial_state
        for symbol in word:
            # Membership in the actual row distinguishes a missing edge
            # from None when None is a valid state name.
            if symbol not in source.transitions[current]:
                return source._restrict_to_states(frozenset())
            current = source.transitions[current][symbol]

        return type(source)(
            states=source.states,
            input_symbols=source.input_symbols,
            transitions=source.transitions,
            initial_state=current,
            final_states=source.final_states,
            allow_partial=source.allow_partial,
        )

    def right_quotient_word(self, word: str) -> ExtendedDFA:
        """Return a DFA for the language ``{u | u + word in L(self)}``.

        Apply the professor's reverse/left-quotient/reverse duality. The
        resulting NFA is determinized using verified requirement #35 so
        this DFA-specific method returns a composable ExtendedDFA. Neither
        trimming nor minimization is implicit, and the source is unchanged.

        Parameters
        ----------
        word : str
            Word to remove from the right, possibly empty.

        Returns
        -------
        ExtendedDFA
            Fresh deterministic quotient over the same alphabet.

        Complexity
        ----------
        Let C36a/C36b, C47 and C35 be the time costs of the two reversals,
        NFA left quotient and determinization on their actual intermediate
        inputs, including constructor validation. Let S36a/S36b, S47 and
        S35 be their peak space costs. This composition takes
        O(|word| + C36a + C47 + C36b + C35) time and
        O(S36a + S47 + S36b + S35) peak space; the latter conservatively
        includes retained intermediates. For an N-state NFA entering #35,
        its reachable-subset count can reach 2**N. See ``determinize``
        for its bound in terms of that count and the transition graph.

        References
        ----------
        Professor requirement #48: reverse, left quotient by reversed
        word, reverse. Reuses requirements #36, #47 and #35. The ``_word``
        suffix avoids the upstream NFA automaton-quotient name collision.
        """
        source = cast("ExtendedDFA", self)
        return _right_quotient_via_reversal(source, word).determinize()
