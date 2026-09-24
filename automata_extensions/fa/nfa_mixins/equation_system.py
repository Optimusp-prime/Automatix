"""NFA right-language equation-system construction."""

from __future__ import annotations

from collections.abc import Hashable
from typing import TYPE_CHECKING, cast

from automata_extensions.equations import SystemOfEquations
from automata_extensions.fa.fa_mixins.equation_system import _build_equation_system

if TYPE_CHECKING:
    from automata_extensions.fa.nfa import ExtendedNFA


class NFAEquationSystemMixin:
    """Construct all NFA state right-language equations."""

    def to_equation_system(self) -> SystemOfEquations[Hashable]:
        """Return the rational equation system of every NFA state.

        Every consuming edge contributes a term. When a real epsilon edge
        exists, first normalize through #37's
        ``remove_epsilon_transitions()``, preserving states and language.
        Thus the generated coefficients satisfy the unique-solution Arden
        precondition. The source NFA remains unchanged.

        Returns
        -------
        SystemOfEquations[Hashable]
            An immutable system for every original state, including those
            unreachable from the initial state.

        Raises
        ------
        ValueError
            If the alphabet contains a non-single-character symbol that
            cannot be represented by #49's Regex alphabet contract.

        Algorithm
        ---------
        Optionally remove epsilon transitions, then use the shared
        DFA/NFA constructor on all consuming edges and final states.

        Complexity
        ----------
        Without epsilon edges, expected O(|Q| log |Q| + T + |Σ|)
        time and O(|Q| + |E| + |Σ|) space, where T includes scanning
        transition entries with empty target sets and all |E| emitted
        edges. Structural equality can add cost when unioning repeated
        pairs. With epsilon edges, first add #37's
        O(n*(n+e) + n*s*(n+M+e) + V) time and
        O(n + n*n*s + V_space) peak space for n states, s symbols, e
        epsilon edges, maximum symbol-destination count M and upstream
        validation V. The shared constructor then scans the normalized
        edges E' at the no-epsilon cost above.

        References
        ----------
        Professor requirement #58; #37 epsilon removal and #49 Regex AST.
        """
        source = cast("ExtendedNFA", self)
        if any(paths.get("") for paths in source.transitions.values()):
            source = source.remove_epsilon_transitions()
        return _build_equation_system(source)
