"""DFA right-language equation-system construction."""

from __future__ import annotations

from collections.abc import Hashable
from typing import cast

from automata.fa.dfa import DFA

from automata_extensions.equations import SystemOfEquations
from automata_extensions.fa.fa_mixins.equation_system import _build_equation_system


class DFAEquationSystemMixin:
    """Construct all DFA state right-language equations."""

    def to_equation_system(self) -> SystemOfEquations[Hashable]:
        """Return the rational equation system of every DFA state.

        Each transition ``q --a--> r`` contributes ``a X_r`` to equation
        ``X_q``. A final state contributes epsilon; a non-final state has
        the empty-language constant. Inaccessible states are included and
        missing transitions contribute nothing. The DFA is unchanged.

        Returns
        -------
        SystemOfEquations[Hashable]
            An immutable system keyed by actual state objects, ordered by
            the project's deterministic state-order convention.

        Raises
        ------
        ValueError
            If the alphabet contains a non-single-character symbol that
            cannot be represented by #49's Regex alphabet contract.

        Algorithm
        ---------
        Sort all states, scan each real transition once, union labels for
        repeated state pairs and assign epsilon to final-state constants.

        Complexity
        ----------
        For Q states, E transitions and Σ alphabet symbols, expected
        O(|Q| log |Q| + |E| + |Σ|) time and O(|Q| + |E| + |Σ|)
        auxiliary space, including ordering and constructed equations.
        Structural equality during union normalization can add AST
        comparison cost for repeated state pairs.

        References
        ----------
        Professor requirement #58; the right-language construction used
        conceptually by #54, now for all states and immutable Regex values.
        """
        return _build_equation_system(cast(DFA, self))
