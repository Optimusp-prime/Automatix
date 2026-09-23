"""Base abstraite commune aux extensions d'automates finis."""

from abc import abstractmethod
from typing import FrozenSet, Self

from automata.fa.fa import FA, FAStateT

from automata_extensions.fa.fa_mixins.accessibility import AccessibilityMixin
from automata_extensions.fa.fa_mixins.analyse import AnalyseMixin
from automata_extensions.fa.fa_mixins.conversions import ConversionMixin
from automata_extensions.fa.fa_mixins.cycle import CycleMixin
from automata_extensions.fa.fa_mixins.graph import GraphMixin
from automata_extensions.fa.fa_mixins.grammaire import GrammaireMixin
from automata_extensions.fa.fa_mixins.scc import SCCMixin
from automata_extensions.fa.fa_mixins.subautomaton import SubautomatonMixin
from automata_extensions.fa.fa_mixins.traversal import TraversalMixin
from automata_extensions.fa.fa_mixins.visualisation import VisualisationMixin
from automata_extensions.fa.fa_mixins.word import WordMixin


class ExtendedFA(
    AccessibilityMixin,
    CycleMixin,
    GraphMixin,
    SCCMixin,
    SubautomatonMixin,
    TraversalMixin,
    WordMixin,
    AnalyseMixin,
    ConversionMixin,
    GrammaireMixin,
    VisualisationMixin,
    FA,
):
    """Regroupe les mixins communs tout en conservant l'abstraction de FA."""

    @abstractmethod
    def _restrict_to_states(self, kept: FrozenSet[FAStateT]) -> Self:
        """Rebuild a same-type concrete automaton over the retained states."""
        raise NotImplementedError
