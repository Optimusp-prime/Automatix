"""Lazy synchronized product of two deterministic finite automata."""

from collections.abc import Callable
from typing import Self, cast

from automata.fa.dfa import DFA
from automata.fa.fa import FAStateT


class ProductMixin:
    """Construct reachable pairs of DFA states without eager Q1 × Q2."""

    def product(
        self,
        other: DFA,
        is_final: Callable[[FAStateT, FAStateT], bool],
    ) -> Self:
        """Return the lazy synchronized product of two DFA transition graphs.

        Only pairs reachable from the pair of initial states are constructed.
        ``is_final`` decides acceptance for each pair. For partial operands,
        automata-lib's binary-product convention uses a collision-free
        implicit trap on a side missing a transition when the other side
        defines it; if both sides lack the symbol, the product edge is absent.
        Neither source automaton is modified.

        Parameters
        ----------
        other : DFA
            The second DFA, with the same input alphabet.
        is_final : Callable[[FAStateT, FAStateT], bool]
            Predicate receiving the two component states of a product pair.

        Returns
        -------
        Self
            Fresh ExtendedDFA with reachable state pairs as its states.

        Raises
        ------
        SymbolMismatchError
            If the two input alphabets differ.

        Complexity
        ----------
        O(|Q1| + |Q2| + R × |Sigma| + V) time and
        O(R × |Sigma| + M) auxiliary space, assuming expected constant-time
        hashing and predicate evaluation. R is the number of reachable
        pairs, including implicit traps; V and M are upstream construction
        and validation costs. Trap-name selection may inspect operand states.

        References
        ----------
        Professor requirement #23 and the supplied mature ProductMixin
        example. automata-lib 9.2.0 DFA._cross_product and DFA._expand_dfa.
        The source PDFs were not accessed.
        """
        lhs = cast(DFA, self)
        initial, expand = DFA._cross_product(
            lhs, other, lhs_relevant=True, rhs_relevant=True
        )

        def pair_is_final(pair: tuple[FAStateT, FAStateT]) -> bool:
            return is_final(pair[0], pair[1])

        return cast(
            Self,
            type(lhs)._expand_dfa(
                pair_is_final,
                initial,
                expand,
                lhs.input_symbols,
                retain_names=True,
                minify=False,
            ),
        )
