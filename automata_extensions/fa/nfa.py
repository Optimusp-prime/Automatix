"""Extension minimale de l'automate fini non déterministe upstream."""

from automata.fa.nfa import NFA

from automata_extensions.fa.base import ExtendedFA


class ExtendedNFA(ExtendedFA, NFA):
    """Associe les mixins communs au comportement de NFA."""

    pass
