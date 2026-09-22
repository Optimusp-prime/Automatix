"""Extension minimale de l'automate fini généralisé upstream."""

from automata.fa.gnfa import GNFA

from automata_extensions.fa.base import ExtendedFA


class ExtendedGNFA(ExtendedFA, GNFA):
    """Associe les mixins communs au comportement de GNFA."""

    pass
