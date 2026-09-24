"""Extension minimale de l'automate fini non déterministe upstream."""

from typing import FrozenSet, Self

from automata.fa.fa import FAStateT
from automata.fa.nfa import NFA

from automata_extensions.fa.base import ExtendedFA
from automata_extensions.fa.fa_mixins.brzozowski import BrzozowskiMixin
from automata_extensions.fa.fa_mixins.determinism import DeterminismMixin
from automata_extensions.fa.fa_mixins.grammar_fa import GrammarMixin
from automata_extensions.fa.fa_mixins.language_operations import LanguageOperationsMixin
from automata_extensions.fa.fa_mixins.reverse import ReverseMixin
from automata_extensions.fa.nfa_mixins.determinization import DeterminizationMixin
from automata_extensions.fa.nfa_mixins.elimination import EliminationMixin
from automata_extensions.fa.nfa_mixins.epsilon import EpsilonMixin
from automata_extensions.fa.nfa_mixins.equation_system import NFAEquationSystemMixin
from automata_extensions.fa.nfa_mixins.grammar_nfa import NFAGrammarMixin
from automata_extensions.fa.nfa_mixins.quotient import NFAQuotientMixin
from automata_extensions.fa.nfa_mixins.set_operations import NFASetOperationsMixin
from automata_extensions.fa.nfa_mixins.thompson import ThompsonMixin


class ExtendedNFA(
    NFAEquationSystemMixin, ThompsonMixin, NFAGrammarMixin, GrammarMixin, BrzozowskiMixin, DeterminismMixin, ReverseMixin, EpsilonMixin, NFASetOperationsMixin,
    DeterminizationMixin,
    EliminationMixin, LanguageOperationsMixin, NFAQuotientMixin, ExtendedFA, NFA
):
    """Associe les mixins communs au comportement de NFA."""

    def _restrict_to_states(self, kept: FrozenSet[FAStateT]) -> Self:
        """Rebuild an NFA while retaining only destinations in kept."""
        if not kept:
            initial = self.initial_state
            return type(self)(
                states={initial},
                input_symbols=self.input_symbols,
                transitions={initial: {}},
                initial_state=initial,
                final_states=set(),
            )

        transitions = {
            source: {
                symbol: destinations & kept
                for symbol, destinations in paths.items()
            }
            for source, paths in self.transitions.items()
            if source in kept
        }
        return type(self)(
            states=kept,
            input_symbols=self.input_symbols,
            transitions=transitions,
            initial_state=self.initial_state,
            final_states=self.final_states & kept,
        )
