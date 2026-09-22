"""Base abstraite commune aux extensions d'automates finis."""

from automata.fa.fa import FA

from automata_extensions.fa.fa_mixins.accessibility import AccessibilityMixin
from automata_extensions.fa.fa_mixins.analyse import AnalyseMixin
from automata_extensions.fa.fa_mixins.conversions import ConversionMixin
from automata_extensions.fa.fa_mixins.grammaire import GrammaireMixin
from automata_extensions.fa.fa_mixins.scc import SCCMixin
from automata_extensions.fa.fa_mixins.traversal import TraversalMixin
from automata_extensions.fa.fa_mixins.visualisation import VisualisationMixin


class ExtendedFA(
    AccessibilityMixin,
    SCCMixin,
    TraversalMixin,
    AnalyseMixin,
    ConversionMixin,
    GrammaireMixin,
    VisualisationMixin,
    FA,
):
    """Regroupe les mixins communs tout en conservant l'abstraction de FA."""

    pass
