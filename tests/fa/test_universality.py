"""Universality is emptiness of the completed DFA's complement."""

from copy import deepcopy
from unittest.mock import patch

import pytest

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.dfa_mixins.complement import ComplementMixin


@pytest.mark.parametrize("alphabet", [set(), {"a"}, {"a", "b"}])
@pytest.mark.parametrize("accepting", [False, True])
def test_universal_or_empty_single_state_dfa(
    alphabet: set[str], accepting: bool,
) -> None:
    source = ExtendedDFA(
        states={"q"}, input_symbols=alphabet,
        transitions={"q": {a: "q" for a in alphabet}},
        initial_state="q", final_states={"q"} if accepting else set(),
    )
    before = deepcopy(source.input_parameters), dict(vars(source))
    result = source.is_universal()
    assert type(result) is bool
    assert result is accepting
    assert result is source.complement().is_empty()
    assert (source.input_parameters, vars(source)) == before


def test_partial_accepting_dfa_is_not_universal() -> None:
    source = ExtendedDFA(
        states={"q"}, input_symbols={"a", "b"},
        transitions={"q": {"a": "q"}}, initial_state="q",
        final_states={"q"}, allow_partial=True,
    )
    assert source.accepts("") is True
    assert source.accepts("aaa") is True
    assert source.is_universal() is False
    assert source.complement().accepts("b") is True


def test_unreachable_nonfinal_state_does_not_prevent_universality() -> None:
    source = ExtendedDFA(
        states={"s", "f", "unused"}, input_symbols={"a", "b"},
        transitions={"s": {"a": "f", "b": "s"},
                     "f": {"a": "s", "b": "f"}, "unused": {}},
        initial_state="s", final_states={"s", "f"}, allow_partial=True,
    )
    assert source.is_complete() is False
    assert source.is_universal() is True


def test_none_and_heterogeneous_states() -> None:
    source = ExtendedDFA(
        states={None, 1, "s"}, input_symbols={"a"},
        transitions={None: {"a": 1}, 1: {"a": "s"}, "s": {"a": None}},
        initial_state=None, final_states={None, 1, "s"},
    )
    assert source.is_universal() is True


def test_universality_source_compatibility_regression_and_no_minimization() -> None:
    # Cycle fixture consistent with d.is_universal() -> False.
    d = ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a"},
        transitions={"0": {"a": "1"}, "1": {"a": "2"}, "2": {"a": "0"}},
        initial_state="0", final_states={"0"},
    )
    with patch.object(ExtendedDFA, "minimize", side_effect=AssertionError("unneeded")):
        assert d.is_universal() is False
        assert d.is_universal() is d.complement().is_empty()


def test_universality_is_dfa_only() -> None:
    assert ExtendedDFA.is_universal is ComplementMixin.is_universal
    for cls in (ExtendedNFA, ExtendedGNFA):
        assert not hasattr(cls, "is_universal")
