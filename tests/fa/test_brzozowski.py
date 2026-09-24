"""Brzozowski minimization and the reverse epsilon-start regression."""

from copy import deepcopy
from itertools import product

import pytest

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.fa_mixins.brzozowski import BrzozowskiMixin


def _mature_dfa() -> ExtendedDFA:
    # Exact three-state fixture used for the supplied mature examples.
    return ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a", "b"},
        transitions={
            "0": {"b": "0", "a": "1"},
            "1": {"b": "1", "a": "2"},
            "2": {"a": "0", "b": "2"},
        },
        initial_state="0", final_states={"0"},
    )


def _check_language(source: ExtendedDFA | ExtendedNFA, result: ExtendedDFA) -> None:
    assert type(result) is ExtendedDFA
    assert result.input_symbols == source.input_symbols
    assert result.is_minimal() is True
    for length in range(5):
        for letters in product(sorted(source.input_symbols), repeat=length):
            word = "".join(letters)
            assert result.accepts(word) is source.accepts(word)


def test_mature_executed_equality_and_actual_minimality() -> None:
    d = _mature_dfa()
    raw = d.reverse().determinize().reverse().determinize()
    assert len(raw.states) == 4
    assert raw.is_minimal() is False  # The synthetic reverse start survives.
    result = d.brzozowski_minimize()
    assert result == d.minimize()  # Mature executed result: True.
    assert len(result.states) == 3
    _check_language(d, result)


@pytest.mark.parametrize("accepting", [True, False])
def test_one_state_accepting_or_empty_language(accepting: bool) -> None:
    source = ExtendedDFA(
        states={"q"}, input_symbols={"a"},
        transitions={"q": {"a": "q"}}, initial_state="q",
        final_states={"q"} if accepting else set(),
    )
    result = source.brzozowski_minimize()
    assert len(result.states) == 1
    assert result == source.minimize()
    _check_language(source, result)


def test_nonminimal_equivalent_states_are_merged() -> None:
    source = ExtendedDFA(
        states={"s", "left", "right", "f"}, input_symbols={"a", "b"},
        transitions={
            "s": {"a": "left", "b": "right"},
            "left": {"a": "f", "b": "f"},
            "right": {"a": "f", "b": "f"},
            "f": {"a": "f", "b": "f"},
        }, initial_state="s", final_states={"f"},
    )
    result = source.brzozowski_minimize()
    assert source.is_minimal() is False
    assert len(result.states) == 3
    assert result == source.minimize()
    _check_language(source, result)


def test_inaccessible_state_is_not_exported() -> None:
    source = ExtendedDFA(
        states={"s", "f", "lost"}, input_symbols={"a"},
        transitions={"s": {"a": "f"}, "f": {"a": "f"},
                     "lost": {"a": "lost"}},
        initial_state="s", final_states={"f", "lost"},
    )
    result = source.brzozowski_minimize()
    assert len(result.states) == 2
    assert result == source.minimize()
    _check_language(source, result)


def test_partial_dfa_missing_transitions_remain_language_rejecting() -> None:
    source = ExtendedDFA(
        states={"s", "f"}, input_symbols={"a", "b"},
        transitions={"s": {"a": "f"}, "f": {}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    result = source.brzozowski_minimize()
    assert result.accepts("b") is False
    assert result.accepts("aa") is False
    assert result == source.minimize()
    _check_language(source, result)


def test_finite_language_and_epsilon_acceptance() -> None:
    source = ExtendedDFA(
        states={"s", "f"}, input_symbols={"a"},
        transitions={"s": {"a": "f"}, "f": {}},
        initial_state="s", final_states={"s", "f"}, allow_partial=True,
    )
    result = source.brzozowski_minimize()
    assert result.accepts("") is True
    assert result.accepts("a") is True
    assert result.accepts("aa") is False
    _check_language(source, result)


def test_empty_alphabet() -> None:
    source = ExtendedDFA(
        states={"s", "unused"}, input_symbols=set(),
        transitions={"s": {}, "unused": {}},
        initial_state="s", final_states={"s"},
    )
    result = source.brzozowski_minimize()
    assert len(result.states) == 1
    _check_language(source, result)


@pytest.mark.parametrize(
    "transitions,final_states",
    [
        ({"s": {"a": {"s", "f"}}, "f": {}}, {"f"}),
        ({"s": {"": {"m"}}, "m": {"a": {"f"}}, "f": {}}, {"f"}),
        ({"s": {"": {"f"}, "a": {"s"}}, "f": {}}, {"f"}),
        ({"s": {"a": {"m", "f"}}, "m": {"a": {"f"}}, "f": {}}, {"f"}),
    ],
)
def test_nfa_source_with_branches_and_epsilon(
    transitions: dict[str, dict[str, set[str]]],
    final_states: set[str],
) -> None:
    source = ExtendedNFA(
        states=set(transitions), input_symbols={"a"},
        transitions=transitions, initial_state="s", final_states=final_states,
    )
    before = deepcopy(source.input_parameters)
    result = source.brzozowski_minimize()
    _check_language(source, result)
    assert result == source.determinize().minimize()
    assert source.input_parameters == before


def test_immutability_repeated_calls_and_composability() -> None:
    source = _mature_dfa()
    before = deepcopy(source.input_parameters)
    result = source.brzozowski_minimize()
    again = source.brzozowski_minimize()
    assert result is not source and again is not result
    assert result == again
    assert result.complete().is_complete() is True
    assert result.reachable_states(result.initial_state) == result.states
    assert source.input_parameters == before


def test_public_import_mro_and_gnfa_scope() -> None:
    assert ExtendedDFA.brzozowski_minimize is BrzozowskiMixin.brzozowski_minimize
    assert ExtendedNFA.brzozowski_minimize is BrzozowskiMixin.brzozowski_minimize
    assert BrzozowskiMixin in ExtendedDFA.__mro__
    assert BrzozowskiMixin in ExtendedNFA.__mro__
    assert not hasattr(ExtendedGNFA, "brzozowski_minimize")
