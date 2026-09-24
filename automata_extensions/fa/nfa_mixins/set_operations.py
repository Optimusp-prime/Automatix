"""Typed extension wrappers for upstream NFA set constructions."""

from typing import Self, cast

from automata.fa.nfa import NFA


class NFASetOperationsMixin:
    """Preserve the ExtendedNFA type while delegating NFA set operations."""

    def union(self, other: NFA) -> Self:
        """Return a new NFA accepting words accepted by either operand.

        Upstream creates a fresh epsilon-branching initial state and uses the
        union of the two input alphabets. The source NFAs are not modified.

        Parameters
        ----------
        other : NFA
            The other NFA; its alphabet may differ.

        Returns
        -------
        Self
            A fresh ExtendedNFA when called on an ExtendedNFA.

        Complexity
        ----------
        O(|Q1| + |Q2| + T1 + T2 + V) time and corresponding space for the
        copied states/transitions, plus upstream validation V. T1/T2 count
        stored transition destinations.

        References
        ----------
        Professor requirement #42 and automata-lib 9.2.0 NFA.union.
        """
        return cast(Self, NFA.union(cast(NFA, self), other))

    def intersection(self, other: NFA) -> Self:
        """Return a new NFA accepting words accepted by both operands.

        Upstream builds reachable state pairs, synchronizing symbol edges
        while allowing either component to take an epsilon edge. Its result
        alphabet is the union of the operand alphabets. Sources are unchanged.

        Parameters
        ----------
        other : NFA
            The other NFA; its alphabet may differ.

        Returns
        -------
        Self
            A fresh ExtendedNFA when called on an ExtendedNFA.

        Complexity
        ----------
        O(R × |Sigma1 ∪ Sigma2| + G + V) time and O(R + G + M) space,
        where R is the number of reachable pairs and G the number of
        generated epsilon/symbol edges, including local destination-pair
        products; V/M are upstream construction and validation costs.

        References
        ----------
        Professor requirement #43, the supplied mature NFA regex example,
        and automata-lib 9.2.0 NFA.intersection.
        """
        return cast(Self, NFA.intersection(cast(NFA, self), other))
