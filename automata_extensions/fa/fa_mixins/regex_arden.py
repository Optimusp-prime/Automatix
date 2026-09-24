"""DFA language equations solved by Arden's lemma."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from automata.fa.fa import FAStateT

from automata_extensions.fa.fa_mixins.regex import (
    _concatenate,
    _star,
    _state_order_key,
    _union,
)

if TYPE_CHECKING:
    from automata_extensions.fa.dfa import ExtendedDFA


class ArdenMixin:
    """Solve DFA state-language equations without state elimination."""

    def to_regex_arden(self) -> str | None:
        """Convert a DFA to a regex by solving its language equations.

        For each state q, X_q denotes words accepted from q. An edge
        q --a--> r contributes a X_r, and a final state contributes epsilon.
        Resolve X = A X | B as A* B by Arden's lemma, substitute that
        expression into later equations, then substitute backward to obtain
        X_initial. The source DFA is not modified.

        Returns
        -------
        str | None
            An equivalent regex, or None for the empty language, matching
            the established #53 DFA conversion convention. Epsilon alone
            is the empty string; epsilon within a union is written ``()``.

        Complexity
        ----------
        For m accessible states and T examined DFA transitions, building
        equations takes O(m**2 + T) time/space; forward substitution makes
        O(m**3) coefficient updates. String-copying costs depend on total
        intermediate expression lengths, which may grow exponentially.
        Back substitution constructs the final expression and can also
        have exponential length. No minimality is promised.

        References
        ----------
        Professor requirement #54 and its Arden rule X = AX | B -> A*B
        when A has no epsilon; supplied mature ArdenMixin example. Uses
        only the #53 private regex-label algebra, not its state-elimination
        algorithm or GNFA.to_regex().
        """
        source = cast("ExtendedDFA", self)
        ordered = sorted(source.accessible_states(), key=_state_order_key)
        coefficients: dict[FAStateT, dict[FAStateT, str | None]] = {
            state: {target: None for target in ordered} for state in ordered
        }
        constants: dict[FAStateT, str | None] = {
            state: "" if state in source.final_states else None
            for state in ordered
        }
        for state in ordered:
            for symbol, target in sorted(source.transitions.get(state, {}).items()):
                coefficients[state][target] = _union(
                    coefficients[state][target], symbol
                )

        # A saved row is X_q = loop_star * (sum of later coefficients
        # times their variables, union the constant). Its variable terms
        # remain unexpanded until backward substitution.
        rows: dict[
            FAStateT, tuple[str, dict[FAStateT, str | None], str | None]
        ] = {}
        for position, state in enumerate(ordered):
            later = ordered[position + 1:]
            loop_star = _star(coefficients[state][state])
            row = {target: coefficients[state][target] for target in later}
            constant = constants[state]
            rows[state] = (loop_star, row, constant)

            for successor in later:
                incoming = coefficients[successor][state]
                if incoming is None:
                    continue
                for target in later:
                    via = _concatenate(incoming, loop_star, row[target])
                    # Route-first union preserves the mature Arden trace.
                    coefficients[successor][target] = _union(
                        via, coefficients[successor][target]
                    )
                constants[successor] = _union(
                    _concatenate(incoming, loop_star, constant),
                    constants[successor],
                )
                coefficients[successor][state] = None

        solutions: dict[FAStateT, str | None] = {}
        for position in range(len(ordered) - 1, -1, -1):
            state = ordered[position]
            loop_star, row, constant = rows[state]
            remainder: str | None = None
            for target in ordered[position + 1:]:
                remainder = _union(
                    remainder, _concatenate(row[target], solutions[target])
                )
            remainder = _union(remainder, constant)
            solutions[state] = _concatenate(loop_star, remainder)

        return solutions[source.initial_state]
