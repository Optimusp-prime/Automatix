"""Vérifie les exports, l'héritage et une instanciation minimale."""

import inspect

import pytest
from automata.fa.dfa import DFA
from automata.fa.fa import FA
from automata.fa.gnfa import GNFA
from automata.fa.nfa import NFA

from automata_extensions.fa import (
    ExtendedDFA,
    ExtendedFA,
    ExtendedGNFA,
    ExtendedNFA,
)


@pytest.mark.parametrize(
    ("extended", "upstream"),
    [
        (ExtendedFA, FA),
        (ExtendedDFA, DFA),
        (ExtendedNFA, NFA),
        (ExtendedGNFA, GNFA),
    ],
)
def test_public_classes(extended: type[FA], upstream: type[FA]) -> None:
    """Les classes exportées conservent leurs parents et constructeurs."""
    assert issubclass(extended, ExtendedFA)
    assert issubclass(extended, upstream)
    assert extended.__init__ is upstream.__init__
    assert inspect.isabstract(extended) == inspect.isabstract(upstream)


def test_extended_fa_is_abstract() -> None:
    """La base commune conserve le contrat abstrait upstream."""
    with pytest.raises(TypeError, match="abstract"):
        ExtendedFA()  # type: ignore[abstract]  # Deliberate negative runtime test.


def test_extended_dfa_instantiation(simple_dfa: ExtendedDFA) -> None:
    """Le DFA concret utilise correctement l'API accepts_input héritée."""
    assert isinstance(simple_dfa, DFA)
    assert simple_dfa.accepts_input("a") is True
