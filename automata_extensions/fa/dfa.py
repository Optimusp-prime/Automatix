"""Extension minimale de l'automate fini déterministe upstream."""

from typing import FrozenSet, Self

from automata.fa.dfa import DFA
from automata.fa.fa import FAStateT

from automata_extensions.fa.base import ExtendedFA
from automata_extensions.fa.fa_mixins.brzozowski import BrzozowskiMixin
from automata_extensions.fa.dfa_mixins.complement import ComplementMixin
from automata_extensions.fa.dfa_mixins.completeness import CompletenessMixin
from automata_extensions.fa.dfa_mixins.equation_system import DFAEquationSystemMixin
from automata_extensions.fa.dfa_mixins.inclusion import InclusionMixin
from automata_extensions.fa.dfa_mixins.isomorphism import IsomorphismMixin
from automata_extensions.fa.dfa_mixins.minimization import MinimizationMixin
from automata_extensions.fa.dfa_mixins.myhill_nerode import MyhillNerodeMixin
from automata_extensions.fa.dfa_mixins.prefix import PrefixMixin
from automata_extensions.fa.dfa_mixins.product import ProductMixin
from automata_extensions.fa.dfa_mixins.quotient import DFAQuotientMixin
from automata_extensions.fa.dfa_mixins.residual import ResidualMixin
from automata_extensions.fa.dfa_mixins.set_operations import DFASetOperationsMixin
from automata_extensions.fa.dfa_mixins.syntactic_monoid import SyntacticMonoidMixin
from automata_extensions.fa.fa_mixins.determinism import DeterminismMixin
from automata_extensions.fa.fa_mixins.grammar_fa import GrammarMixin
from automata_extensions.fa.fa_mixins.language_operations import LanguageOperationsMixin
from automata_extensions.fa.fa_mixins.morphism import MorphismMixin
from automata_extensions.fa.fa_mixins.reverse import ReverseMixin
from automata_extensions.fa.fa_mixins.regex import RegexMixin
from automata_extensions.fa.fa_mixins.regex_arden import ArdenMixin


class ExtendedDFA(
    DFAEquationSystemMixin, ArdenMixin, RegexMixin, BrzozowskiMixin, CompletenessMixin, ComplementMixin, ProductMixin, DFASetOperationsMixin,
    GrammarMixin, InclusionMixin,
    IsomorphismMixin, PrefixMixin, MinimizationMixin, MyhillNerodeMixin, DeterminismMixin,
    LanguageOperationsMixin, DFAQuotientMixin, ResidualMixin, SyntacticMonoidMixin,
    MorphismMixin, ReverseMixin,
    ExtendedFA, DFA
):
    """Associe les mixins communs au comportement de DFA."""

    def _restrict_to_states(self, kept: FrozenSet[FAStateT]) -> Self:
        """Rebuild a DFA, allowing missing edges after restriction."""
        if not kept:
            initial = self.initial_state
            transitions = {
                initial: (
                    {} if self.allow_partial else
                    {symbol: initial for symbol in self.input_symbols}
                )
            }
            return type(self)(
                states={initial},
                input_symbols=self.input_symbols,
                transitions=transitions,
                initial_state=initial,
                final_states=set(),
                allow_partial=self.allow_partial,
            )

        transitions = {
            source: {
                symbol: target
                for symbol, target in self.transitions[source].items()
                if target in kept
            }
            for source in kept
        }
        allow_partial = self.allow_partial or any(
            len(paths) < len(self.input_symbols)
            for paths in transitions.values()
        )
        return type(self)(
            states=kept,
            input_symbols=self.input_symbols,
            transitions=transitions,
            initial_state=self.initial_state,
            final_states=self.final_states & kept,
            allow_partial=allow_partial,
        )
