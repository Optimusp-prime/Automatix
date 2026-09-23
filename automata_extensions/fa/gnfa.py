"""Extension minimale de l'automate fini généralisé upstream."""

from typing import FrozenSet, Self

from automata.fa.fa import FAStateT
from automata.fa.gnfa import GNFA

from automata_extensions.fa.base import ExtendedFA


class ExtendedGNFA(ExtendedFA, GNFA):
    """Associe les mixins communs au comportement de GNFA."""

    def is_finite(self) -> bool:
        """Decline finiteness until GNFA regex labels can be analyzed.

        A regex label such as ``a*`` can denote infinitely many words on
        a single acyclic GNFA edge. The DFA/NFA useful-cycle test would
        therefore give a misleading answer for this representation.

        Returns
        -------
        bool
            No result is returned for a GNFA in this phase.

        Raises
        ------
        NotImplementedError
            GNFA regex-label finiteness is outside requirement #14's
            explicitly agreed DFA/NFA guarantee.

        Complexity
        ----------
        O(1) time and space; no analysis or mutation is performed.

        References
        ----------
        User clarification for requirement #14: preserve real finiteness
        for DFA/NFA and defer regex-label semantics for GNFA. ADR-0010.
        """
        raise NotImplementedError(
            "GNFA regex labels require semantic finiteness analysis"
        )

    def _restrict_to_states(self, kept: FrozenSet[FAStateT]) -> Self:
        """Rebuild the GNFA transition table, retaining None-valued slots."""
        if not kept:
            initial = self.initial_state
            final = self.final_state
            return type(self)(
                states={initial, final},
                input_symbols=self.input_symbols,
                transitions={initial: {final: None}},
                initial_state=initial,
                final_state=final,
            )

        transitions = {
            source: {
                target: label
                for target, label in self.transitions.get(
                    source, {}
                ).items()
                if target in kept
            }
            for source in kept
            if source != self.final_state
        }
        return type(self)(
            states=kept,
            input_symbols=self.input_symbols,
            transitions=transitions,
            initial_state=self.initial_state,
            final_state=self.final_state,
        )
