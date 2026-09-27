"""Bounded order search over the established DFA-to-regex engines."""

from __future__ import annotations

from collections.abc import Callable, Sequence, Set
from itertools import islice, permutations
from typing import Protocol, cast

from automata.fa.fa import FAStateT

from automata_extensions.fa.fa_mixins.regex import _state_order_key
from automata_extensions.regex import Regex


class _OrderConversions(Protocol):
    """Existing conversion engines consumed without reimplementing them."""

    @property
    def states(self) -> Set[FAStateT]: ...

    def accessible_states(self) -> frozenset[FAStateT]: ...

    def _to_regex_for_order(self, order: Sequence[FAStateT]) -> str | None: ...

    def _to_regex_arden_for_order(
        self, order: Sequence[FAStateT]
    ) -> str | None: ...


def _best_expression(
    states: Sequence[FAStateT],
    convert: Callable[[Sequence[FAStateT]], str | None],
) -> str | None:
    """Try the first 24 lexical orders, then rank canonical AST renderings."""
    candidates: list[str] = []
    for order in islice(permutations(states), 24):
        raw = convert(order)
        if raw is not None:
            normalized = str(Regex(raw))
            candidates.append("" if normalized == "()" else normalized)
    return min(candidates, key=lambda expression: (len(expression), expression)) if candidates else None


class RegexOptimumMixin:
    """Search deterministic state orders for shorter equivalent regexes."""

    def to_regex_optimum(self) -> str | None:
        """Convert a DFA by trying multiple state-elimination orders.

        The existing #53 GNFA elimination engine is run on up to 24
        lexicographic permutations of all states. The private #49 AST
        applies its normalizations to each string. Choose the shortest
        rendered result, breaking ties lexicographically. No global
        minimum is claimed. The source DFA remains unchanged.

        Returns
        -------
        str | None
            Equivalent regex, or None for the empty language.

        Complexity
        ----------
        For n states and k = min(n!, 24) attempted orders, at least
        O(k*n**3) elimination-label updates plus k GNFA constructions.
        String growth, AST parsing and structural comparisons add their
        actual total cost S, potentially exponential in n. Thus time is
        O(k*n**3 + S + k*V), where V is one upstream construction cost;
        peak space includes O(n**2) intermediate labels and the k rendered
        candidates of total length C (their combined character count), plus
        AST working memory. For n <= 4,
        every permutation is tried, so the search is factorial.

        References
        ----------
        Mature RegexOptimumMixin example; requirements #49 and #53;
        ADR-0024.
        """
        source = cast(_OrderConversions, self)
        return _best_expression(
            sorted(source.states, key=_state_order_key),
            source._to_regex_for_order,
        )

    def to_regex_arden_optimum(self) -> str | None:
        """Solve DFA language equations over several variable orders.

        Reuse the established #54 Arden elimination engine with at most
        24 lexicographic permutations of accessible states. Normalize
        each candidate through the private #49 AST and choose shortest,
        with lexical tie-break. This is a bounded heuristic, not a
        globally minimal regular expression. The DFA is unchanged.

        Returns
        -------
        str | None
            Equivalent regex, or None for the empty language.

        Complexity
        ----------
        With m accessible states and k = min(m!, 24), the shared Arden
        solver makes O(k*m**3) coefficient updates plus k scans of edges.
        Total string growth, AST parsing and structural comparisons add
        cost S, potentially exponential in m. Time is
        O(k*m**3 + k*T + S), where T scans transitions once per order;
        peak space includes O(m**2) equation coefficients and the k
        candidate strings of total length C (combined characters) plus
        AST working memory.
        For m <= 4 the order search is factorial.

        References
        ----------
        Mature RegexOptimumMixin Arden example; requirements #49 and #54;
        ADR-0024.
        """
        source = cast(_OrderConversions, self)
        return _best_expression(
            sorted(source.accessible_states(), key=_state_order_key),
            source._to_regex_arden_for_order,
        )
