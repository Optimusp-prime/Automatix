"""Extension minimale de l'automate fini déterministe upstream."""

from automata.fa.dfa import DFA

from automata_extensions.fa.base import ExtendedFA


class ExtendedDFA(ExtendedFA, DFA):
    """Associe les mixins communs au comportement de DFA."""

    pass
