"""DFA completeness tests based on the actual transition table."""

from copy import deepcopy
from collections.abc import Mapping
from typing import cast
from unittest.mock import patch

import pytest
from automata.fa.dfa import DFA
from automata.fa.fa import FAStateT
from automata.base.exceptions import InvalidStateError

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


def test_complete_adds_one_nonfinal_sink_for_all_missing_edges() -> None:
    source = ExtendedDFA(
        states={"s", "f", "d"}, input_symbols={"a", "b"},
        transitions={
            "s": {"a": "f"}, "f": {"b": "d"}, "d": {"a": "d"},
        },
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    completed = source.complete(trap_state="sink")
    assert type(completed) is ExtendedDFA
    assert completed is not source
    assert completed.states == source.states | {"sink"}
    assert completed.initial_state == source.initial_state
    assert completed.input_symbols == source.input_symbols
    assert completed.final_states == source.final_states
    assert completed.allow_partial is False
    assert completed.is_complete() is True
    assert completed.transitions == {
        "s": {"a": "f", "b": "sink"},
        "f": {"a": "sink", "b": "d"},
        "d": {"a": "d", "b": "sink"},
        "sink": {"a": "sink", "b": "sink"},
    }
    assert "sink" not in completed.final_states


@pytest.mark.parametrize("allow_partial", [False, True])
def test_already_complete_returns_fresh_copy_without_sink(
    allow_partial: bool,
) -> None:
    source = _two_state_dfa(allow_partial=allow_partial)
    completed = source.complete(trap_state="sink")
    assert type(completed) is ExtendedDFA
    assert completed is not source
    assert completed.states == source.states
    assert completed.transitions == source.transitions
    assert completed.input_symbols == source.input_symbols
    assert completed.final_states == source.final_states
    assert completed.initial_state == source.initial_state
    assert completed.allow_partial is allow_partial
    assert completed.is_complete() is True


def test_automatic_sink_skips_existing_negative_integer_states() -> None:
    source = ExtendedDFA(
        states={"s", -1, -2}, input_symbols={"a"},
        transitions={"s": {}, -1: {"a": "s"}, -2: {"a": -1}},
        initial_state="s", final_states={-1}, allow_partial=True,
    )
    completed = source.complete()
    assert completed.states == source.states | {-3}
    assert completed.transitions["s"]["a"] == -3
    transitions = cast(Mapping[FAStateT, Mapping[str, FAStateT]],
                       completed.transitions)
    assert transitions[-3] == {"a": -3}
    assert completed.is_complete() is True


def test_colliding_explicit_sink_raises_without_mutation() -> None:
    source = _two_state_dfa(allow_partial=True, missing_state="f")
    before = deepcopy(source.transitions)
    with pytest.raises(InvalidStateError):
        source.complete(trap_state="s")
    assert source.transitions == before
    assert source.is_complete() is False


@pytest.mark.parametrize(
    "word", ["", "a", "b", "aa", "ab", "ba", "bb", "abba", "bbbb"]
)
def test_completion_preserves_language(word: str) -> None:
    source = _two_state_dfa(allow_partial=True, missing_state="f")
    completed = source.complete(trap_state="sink")
    assert source.accepts(word) is completed.accepts(word)
    assert source.accepts("ab") is False  # the formerly missing edge


def test_completion_preserves_source_and_supports_extension_methods() -> None:
    source = _two_state_dfa(allow_partial=True, missing_state="f")
    before = (
        deepcopy(source.states), deepcopy(source.transitions),
        deepcopy(source.final_states), deepcopy(source.input_symbols),
        source.initial_state, source.allow_partial,
    )
    completed = source.complete()
    assert (
        source.states, source.transitions, source.final_states,
        source.input_symbols, source.initial_state, source.allow_partial,
    ) == before
    assert completed.is_complete() is True
    assert completed.reachable_states("s") == completed.accessible_states()
    assert completed.complete().states == completed.states


def test_induced_subautomaton_then_completion() -> None:
    source = _two_state_dfa(allow_partial=False)
    restricted = source.induced_subautomaton({"s"})
    assert source.is_complete() is True
    assert restricted.is_complete() is False
    completed = restricted.complete()
    assert completed.is_complete() is True
    assert type(completed) is ExtendedDFA
    assert completed.accepts("") == restricted.accepts("")
    assert completed.accepts("a") == restricted.accepts("a")


def test_none_and_heterogeneous_states_with_explicit_sink() -> None:
    source = ExtendedDFA(
        states={None, "q", 7}, input_symbols={"a", "b"},
        transitions={None: {"a": "q"}, "q": {"a": 7}, 7: {"b": None}},
        initial_state=None, final_states={"q"}, allow_partial=True,
    )
    completed = source.complete(trap_state=("sink",))
    assert completed.states == source.states | {("sink",)}
    transitions = cast(Mapping[FAStateT, Mapping[str, FAStateT]],
                       completed.transitions)
    assert transitions[None]["b"] == ("sink",)
    assert transitions[("sink",)] == {
        "a": ("sink",), "b": ("sink",),
    }
    assert completed.is_complete() is True


def test_completion_with_empty_alphabet_adds_no_sink() -> None:
    source = ExtendedDFA(
        states={"s"}, input_symbols=set(), transitions={"s": {}},
        initial_state="s", final_states={"s"},
    )
    completed = source.complete()
    assert completed is not source
    assert completed.states == source.states
    assert completed.is_complete() is True


def test_complete_delegates_to_upstream_and_preserves_to_complete() -> None:
    assert ExtendedDFA.to_complete is DFA.to_complete
    assert ExtendedDFA.complete is CompletenessMixin.complete
    source = _two_state_dfa(allow_partial=True, missing_state="f")
    with patch.object(
        ExtendedDFA, "to_complete", wraps=source.to_complete
    ) as upstream:
        completed = source.complete(trap_state="sink")
    upstream.assert_called_once_with("sink")
    assert type(completed) is ExtendedDFA


def test_complete_documented_source_compatibility() -> None:
    """Keep the mature reference's executable completion example working."""
    partiel = ExtendedDFA(
        states={"0"},
        input_symbols={"a", "b"},
        transitions={"0": {"a": "0"}},
        initial_state="0",
        final_states={"0"},
        allow_partial=True,
    )

    assert partiel.complete().is_complete() is True
