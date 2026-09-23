"""DFA completeness tests based on the actual transition table."""

from copy import deepcopy
from unittest.mock import patch

import pytest
from automata.fa.dfa import DFA
from automata.fa.fa import FAStateT

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.dfa_mixins.completeness import CompletenessMixin


def _two_state_dfa(
    *, allow_partial: bool, missing_state: str | None = None
) -> ExtendedDFA:
    transitions = {
        "s": {"a": "f", "b": "s"},
        "f": {"a": "f", "b": "s"},
    }
    if missing_state is not None:
        del transitions[missing_state]["b"]
    return ExtendedDFA(
        states={"s", "f"}, input_symbols={"a", "b"},
        transitions=transitions, initial_state="s", final_states={"f"},
        allow_partial=allow_partial,
    )


@pytest.mark.parametrize("allow_partial", [False, True])
def test_complete_dfa_is_true_regardless_of_allow_partial(
    allow_partial: bool,
) -> None:
    dfa = _two_state_dfa(allow_partial=allow_partial)
    result = dfa.is_complete()
    assert type(result) is bool
    assert result is True
    assert dfa.allow_partial is allow_partial


@pytest.mark.parametrize("missing_state", ["s", "f"])
def test_missing_transition_on_either_state_is_incomplete(
    missing_state: str,
) -> None:
    dfa = _two_state_dfa(allow_partial=True, missing_state=missing_state)
    assert dfa.is_complete() is False
    assert dfa.allow_partial is True


def test_single_symbol_self_loop_is_complete() -> None:
    dfa = ExtendedDFA(
        states={"q"}, input_symbols={"a"},
        transitions={"q": {"a": "q"}},
        initial_state="q", final_states={"q"},
    )
    assert dfa.is_complete() is True


def test_single_symbol_missing_transition_is_incomplete() -> None:
    dfa = ExtendedDFA(
        states={"q"}, input_symbols={"a"}, transitions={"q": {}},
        initial_state="q", final_states=set(), allow_partial=True,
    )
    assert dfa.is_complete() is False


def test_empty_alphabet_is_vacuously_complete() -> None:
    dfa = ExtendedDFA(
        states={"s", "f"}, input_symbols=set(),
        transitions={"s": {}, "f": {}},
        initial_state="s", final_states={"f"},
    )
    assert dfa.input_symbols == frozenset()
    assert dfa.is_complete() is True


@pytest.mark.parametrize("missing", [False, True])
def test_none_and_heterogeneous_states(missing: bool) -> None:
    transitions: dict[FAStateT, dict[str, FAStateT]] = {
        0: {"a": "q"}, "q": {"a": None}, None: {"a": 0},
    }
    if missing:
        transitions[None] = {}
    dfa = ExtendedDFA(
        states={0, "q", None}, input_symbols={"a"},
        transitions=transitions, initial_state=0,
        final_states={"q"}, allow_partial=missing,
    )
    assert dfa.is_complete() is (not missing)


def test_induced_subautomaton_can_become_partial() -> None:
    source = _two_state_dfa(allow_partial=False)
    assert source.is_complete() is True
    restricted = source.induced_subautomaton({"s"})
    assert isinstance(restricted, ExtendedDFA)
    assert restricted.allow_partial is True
    assert restricted.is_complete() is False
    assert source.is_complete() is True


def test_full_set_restriction_preserves_completeness() -> None:
    source = _two_state_dfa(allow_partial=False)
    restricted = source.induced_subautomaton(source.states)
    assert restricted is not source
    assert restricted.allow_partial is False
    assert restricted.is_complete() is True


def test_is_complete_does_not_mutate_or_call_to_complete() -> None:
    dfa = _two_state_dfa(allow_partial=True, missing_state="f")
    original = (
        deepcopy(dfa.states), deepcopy(dfa.transitions),
        deepcopy(dfa.input_symbols), dfa.allow_partial,
    )
    with patch.object(ExtendedDFA, "to_complete", side_effect=AssertionError):
        assert dfa.is_complete() is False
    assert (dfa.states, dfa.transitions, dfa.input_symbols, dfa.allow_partial) == original


def test_dfa_only_mixin_and_upstream_mro() -> None:
    assert ExtendedDFA.is_complete is CompletenessMixin.is_complete
    assert CompletenessMixin in ExtendedDFA.__mro__
    assert ExtendedDFA.to_complete is DFA.to_complete
    for cls in (ExtendedNFA, ExtendedGNFA):
        assert CompletenessMixin not in cls.__mro__
        assert not hasattr(cls, "is_complete")
