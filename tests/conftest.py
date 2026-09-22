"""Fixtures minimales pour vérifier l'instanciation upstream."""

import pytest

from automata_extensions.fa import ExtendedDFA


@pytest.fixture
def simple_dfa() -> ExtendedDFA:
    """Construit un DFA à deux états via le constructeur upstream."""
    return ExtendedDFA(
        states=frozenset({"q0", "q1"}),
        input_symbols=frozenset({"a"}),
        transitions={
            "q0": {"a": "q1"},
            "q1": {"a": "q1"},
        },
        initial_state="q0",
        final_states=frozenset({"q1"}),
    )
