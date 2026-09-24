"""Construct the canonical DFA of a language's left quotients."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from automata_extensions.fa.dfa import ExtendedDFA


class ResidualMixin:
    """Assemble the distinct left quotients into a complete DFA."""

    def residual_automaton(self) -> ExtendedDFA:
        """Return the DFA whose states represent distinct left quotients.

        Reuse #59's ordered quotients R0, ..., R(k-1). State ``qi`` denotes
        Ri, so ``q0`` is initial. It is final exactly when Ri contains the
        empty word. For every input symbol, find the unique quotient equal
        to that symbol's left quotient of Ri. Missing source transitions
        lead to the rejecting empty residual, making this DFA complete.
        Neither the source nor the intermediate quotient DFAs are modified.

        Returns
        -------
        ExtendedDFA
            Fresh, complete canonical residual automaton with states
            ``q0``, ..., ``q(k-1)`` in #59 quotient order.

        Raises
        ------
        AssertionError
            If #59's quotient set is not closed under one-symbol left
            quotient or does not identify a unique residual language.

        Complexity
        ----------
        Let Q be source states, Sigma its alphabet, k the number of #59
        quotients, T the source transition-scan cost, and V/M upstream
        construction time/memory. Let C59/S59 be #59's documented
        time/space bounds. One derived quotient costs
        C47 = O(|Q| + T + V); one semantic equality check costs
        Ceq = O((2|Q| + R)|Sigma| + V), where R <= (|Q|+1)^2
        bounds reachable product pairs after completion. Thus expected
        total time is O(C59 + k|Sigma|(C47 + k*Ceq) + V), including the
        result constructor. Peak space is O(S59 + |Q| + T + M +
        (2|Q| + R)|Sigma| + k|Sigma|): #59's k full quotient DFAs,
        one temporary derived quotient/comparison, and the output table.
        Constant-time hash and transition lookup are assumed.

        References
        ----------
        Professor requirement #60 and the supplied mature
        ``residual_automaton`` example. Reuses #59, #47 and #25.
        """
        source = cast("ExtendedDFA", self)
        quotients = source.myhill_nerode_quotients()
        names = tuple(f"q{index}" for index in range(len(quotients)))
        transitions: dict[str, dict[str, str]] = {}
        final_states: set[str] = set()

        for index, quotient in enumerate(quotients):
            name = names[index]
            if quotient.accepts_input(""):
                final_states.add(name)

            paths: dict[str, str] = {}
            for symbol in sorted(source.input_symbols):
                derivative = quotient.left_quotient_word(symbol)
                matches = [
                    candidate_index
                    for candidate_index, candidate in enumerate(quotients)
                    if derivative.is_equivalent(candidate)
                ]
                if len(matches) != 1:
                    raise AssertionError(
                        "quotient derivative must identify exactly one residual"
                    )
                paths[symbol] = names[matches[0]]
            transitions[name] = paths

        return type(source)(
            states=set(names),
            input_symbols=source.input_symbols,
            transitions=transitions,
            initial_state="q0",
            final_states=final_states,
            allow_partial=False,
        )
