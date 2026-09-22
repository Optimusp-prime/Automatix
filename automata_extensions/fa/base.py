"""Base abstraite commune aux extensions d'automates finis."""

from automata.fa.fa import FA

from automata_extensions.fa.mixins.analyse import AnalyseMixin
from automata_extensions.fa.mixins.conversions import ConversionMixin
from automata_extensions.fa.mixins.grammaire import GrammaireMixin
from automata_extensions.fa.mixins.visualisation import VisualisationMixin


class ExtendedFA(
    AnalyseMixin,
    ConversionMixin,
    GrammaireMixin,
    VisualisationMixin,
    FA,
):
    """Regroupe les mixins communs tout en conservant l'abstraction de FA."""

    pass
