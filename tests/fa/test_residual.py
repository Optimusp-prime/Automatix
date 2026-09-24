"""Residual DFA assembled from the distinct left quotients of a language."""

from copy import deepcopy
from itertools import product

import pytest

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from tests.fa.test_state_elimination import _mature_dfa


def _single_a() -> ExtendedDFA:
    return ExtendedDFA(
        states={"s", "f"}, input_symbols={"a", "b"},
        transitions={"s": {"a": "f"}, "f": {}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )


def _assert_same_language(source: ExtendedDFA, result: ExtendedDFA) -> None:
    assert result.is_equivalent(source)
    for length in range(4):
        for symbols in product(sorted(source.input_symbols), repeat=length):
            word = "".join(symbols)
            assert result.accepts(word) is source.accepts(word)


def _right_language(dfa: ExtendedDFA, state: str) -> ExtendedDFA:
    return ExtendedDFA(
        states=dfa.states, input_symbols=dfa.input_symbols,
        transitions=dfa.transitions, initial_state=state,
        final_states=dfa.final_states,
    )


def test_mature_source_compatibility_exact_names_and_language() -> None:
    source = _mature_dfa()
    residual = source.residual_automaton()
    assert sorted(map(str, residual.states)) == ["q0", "q1", "q2"]
    assert type(residual) is ExtendedDFA
    assert residual is not source
    assert residual.initial_state == "q0"
    assert residual.final_states == {"q0"}
    assert len(residual.states) == len(source.myhill_nerode_quotients()) == 3
    assert residual.is_complete() is True
    assert residual.is_minimal() is True
    _assert_same_language(source, residual)


def test_each_named_state_recognizes_corresponding_quotient() -> None:
    source = _mature_dfa()
    quotients = source.myhill_nerode_quotients()
    residual = source.residual_automaton()
    for index, quotient in enumerate(quotients):
        assert _right_language(residual, f"q{index}").is_equivalent(quotient)
        assert (f"q{index}" in residual.final_states) is quotient.accepts("")


def test_partial_single_a_is_complete_with_rejecting_empty_sink() -> None:
    source = _single_a()
    residual = source.residual_automaton()
    assert residual.states == {"q0", "q1", "q2"}
    assert residual.initial_state == "q0"
    assert residual.final_states == {"q1"}
    assert residual.transitions == {
        "q0": {"a": "q1", "b": "q2"},
        "q1": {"a": "q2", "b": "q2"},
        "q2": {"a": "q2", "b": "q2"},
    }
    assert residual.is_complete() is True
    assert residual.is_minimal() is True
    _assert_same_language(source, residual)


def test_explicit_dead_state_avoids_duplicate_empty_residual() -> None:
    source = ExtendedDFA(
        states={"s", "f", "dead"}, input_symbols={"a", "b"},
        transitions={"s": {"a": "f", "b": "dead"}, "f": {}, "dead": {}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    residual = source.residual_automaton()
    assert residual.states == {"q0", "q1", "q2"}
    assert residual.transitions["q2"] == {"a": "q2", "b": "q2"}
    assert residual.final_states == {"q1"}
    _assert_same_language(source, residual)


def test_unreachable_and_equivalent_reachable_states_do_not_add_residuals() -> None:
    source = ExtendedDFA(
        states={"s", "one", "two", "unreachable"},
        input_symbols={"a", "b"},
        transitions={
            "s": {"a": "one", "b": "two"},
            "one": {"a": "one", "b": "one"},
            "two": {"a": "two", "b": "two"},
            "unreachable": {"a": "unreachable", "b": "unreachable"},
        },
        initial_state="s", final_states={"one", "two"},
    )
    assert len(source.equivalence_classes()) == 3
    residual = source.residual_automaton()
    assert residual.states == {"q0", "q1"}
    assert residual.is_minimal() is True
    _assert_same_language(source, residual)


@pytest.mark.parametrize("final", [False, True])
def test_one_state_complete_empty_and_universal_languages(final: bool) -> None:
    source = ExtendedDFA(
        states={0}, input_symbols={"a", "b"},
        transitions={0: {"a": 0, "b": 0}}, initial_state=0,
        final_states={0} if final else set(),
    )
    residual = source.residual_automaton()
    assert residual.states == {"q0"}
    assert residual.final_states == ({"q0"} if final else set())
    assert residual.transitions["q0"] == {"a": "q0", "b": "q0"}
    assert residual.is_minimal() is True
    _assert_same_language(source, residual)


def test_one_state_partial_empty_language_has_one_residual() -> None:
    source = ExtendedDFA(
        states={None}, input_symbols={"a"}, transitions={None: {}},
        initial_state=None, final_states=set(), allow_partial=True,
    )
    residual = source.residual_automaton()
    assert residual.states == {"q0"}
    assert residual.final_states == set()
    assert residual.transitions["q0"] == {"a": "q0"}
    _assert_same_language(source, residual)


def test_epsilon_only_language_and_empty_alphabet() -> None:
    for alphabet in ({"a"}, set()):
        source = ExtendedDFA(
            states={"s"}, input_symbols=alphabet, transitions={"s": {}},
            initial_state="s", final_states={"s"}, allow_partial=True,
        )
        residual = source.residual_automaton()
        assert residual.initial_state == "q0"
        assert "q0" in residual.final_states
        assert residual.is_complete()
        assert len(residual.states) == (2 if alphabet else 1)
        _assert_same_language(source, residual)


def test_names_beyond_q9_follow_quotient_indices() -> None:
    states = set(range(11))
    source = ExtendedDFA(
        states=states, input_symbols={"a"},
        transitions={state: {"a": (state + 1) % 11} for state in states},
        initial_state=0, final_states={0},
    )
    residual = source.residual_automaton()
    assert residual.states == {f"q{index}" for index in range(11)}
    assert residual.initial_state == "q0"
    assert residual.transitions["q9"]["a"] == "q10"
    assert residual.transitions["q10"]["a"] == "q0"
    assert residual.is_minimal()
    _assert_same_language(source, residual)


def test_repeated_calls_source_and_quotients_remain_unchanged() -> None:
    source = _single_a()
    before = deepcopy(source.input_parameters), source.allow_partial
    quotients = source.myhill_nerode_quotients()
    quotient_snapshots = [deepcopy(q.input_parameters) for q in quotients]
    first = source.residual_automaton()
    second = source.residual_automaton()
    assert first is not second
    assert first.states == second.states
    assert first.transitions == second.transitions
    assert first.final_states == second.final_states
    assert (source.input_parameters, source.allow_partial) == before
    assert [q.input_parameters for q in quotients] == quotient_snapshots
    assert type(first.complete()) is ExtendedDFA
    assert type(first.myhill_nerode_quotients()[0]) is ExtendedDFA
    assert not hasattr(ExtendedNFA, "residual_automaton")
    assert not hasattr(ExtendedGNFA, "residual_automaton")
