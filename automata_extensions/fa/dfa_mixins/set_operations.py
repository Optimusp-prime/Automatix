"""DFA language union, intersection, and difference by composition."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from automata.fa.dfa import DFA

if TYPE_CHECKING:
    from automata_extensions.fa.dfa import ExtendedDFA


class DFASetOperationsMixin:
    """Combine DFA languages through the existing lazy product."""

    def union(
        self, other: DFA, *, retain_names: bool = False, minify: bool = False
    ) -> ExtendedDFA:
        """Return a fresh DFA accepting either operand's language.

        Parameters
        ----------
        other : DFA
            DFA over the same alphabet.
        retain_names : bool, default: False
            Preserve representative state names if explicitly minimizing.
        minify : bool, default: False
            Apply the existing extension minimization only when requested.

        Returns
        -------
        ExtendedDFA
            Reachable-pair synchronized product with OR finals, unminimized
            by default.

        Raises
        ------
        SymbolMismatchError
            If the input alphabets differ.

        Complexity
        ----------
        O(|Q1| + |Q2| + R × |Sigma| + V) expected time and
        O(R × |Sigma| + M) auxiliary space, as in ``product``. R counts
        reachable pairs, including implicit traps; V/M include upstream
        construction and validation. Explicit minimization adds the cost
        documented by ``minimize``.

        References
        ----------
        Professor requirement #42 and the supplied mature DFA union example.
        Reuses requirement #23; no implicit minimization or source mutation.
        """
        left = cast("ExtendedDFA", self)
        result = left.product(
            other,
            is_final=lambda q1, q2: (
                q1 in left.final_states or q2 in other.final_states
            ),
        )
        return (
            result.minimize(keep_original_names=retain_names)
            if minify else result
        )

    def intersection(
        self, other: DFA, *, retain_names: bool = False, minify: bool = False
    ) -> ExtendedDFA:
        """Return a fresh DFA accepting both operands' languages.

        Parameters
        ----------
        other : DFA
            DFA over the same alphabet.
        retain_names : bool, default: False
            Preserve representative state names if explicitly minimizing.
        minify : bool, default: False
            Apply the existing extension minimization only when requested.

        Returns
        -------
        ExtendedDFA
            Reachable-pair synchronized product with AND finals, unminimized
            by default.

        Raises
        ------
        SymbolMismatchError
            If the input alphabets differ.

        Complexity
        ----------
        O(|Q1| + |Q2| + R × |Sigma| + V) expected time and
        O(R × |Sigma| + M) auxiliary space, as in ``product``. Explicit
        minimization adds the cost documented by ``minimize``.

        References
        ----------
        Professor requirement #43 and the supplied mature DFA intersection
        example. Reuses requirement #23; no implicit minimization or mutation.
        """
        left = cast("ExtendedDFA", self)
        result = left.product(
            other,
            is_final=lambda q1, q2: (
                q1 in left.final_states and q2 in other.final_states
            ),
        )
        return (
            result.minimize(keep_original_names=retain_names)
            if minify else result
        )

    def difference(
        self, other: DFA, *, retain_names: bool = False, minify: bool = False
    ) -> ExtendedDFA:
        """Return a fresh DFA accepting self but rejecting other.

        Complement the right DFA before intersecting, as specified by the
        professor. ``minify=False`` preserves the extension's unminimized
        default even if ``other`` is an upstream DFA. Neither source changes.

        Parameters
        ----------
        other : DFA
            DFA over the same alphabet.
        retain_names : bool, default: False
            Preserve representative state names if explicitly minimizing.
        minify : bool, default: False
            Apply the existing extension minimization only when requested.

        Returns
        -------
        ExtendedDFA
            DFA for ``L(self) - L(other)``.

        Raises
        ------
        SymbolMismatchError
            If the input alphabets differ.

        Complexity
        ----------
        O(|Q2| × |Sigma| + |Q1| + R × |Sigma| + V) expected time and
        O((|Q2| + R) × |Sigma| + M) auxiliary space. This includes right
        completion, final-state inversion, the lazy intersection product,
        and upstream construction/validation V/M. Explicit minimization
        adds the cost documented by ``minimize``.

        References
        ----------
        Professor requirement #44: intersection with complement. Reuses
        requirements #22, #23 and #43 and the supplied mature DFA example.
        """
        left = cast("ExtendedDFA", self)
        return left.intersection(
            other.complement(minify=False),
            retain_names=retain_names,
            minify=minify,
        )
