"""DFA complement tests for completion followed by final-state inversion."""

from copy import deepcopy

import pytest

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.dfa_mixins.complement import ComplementMixin


def _partial_dfa() -> ExtendedDFA:
    return ExtendedDFA(
        states={"0"}, input_symbols={"a", "b"},
        transitions={"0": {"a": "0"}}, initial_state="0",
        final_states={"0"}, allow_partial=True,
    )


def test_partial_dfa_is_completed_before_finals_are_inverted() -> None:
    source = _partial_dfa()
    completed = source.complete()
    result = source.complement()
    sink = next(iter(completed.states - source.states))

    assert type(result) is ExtendedDFA
    assert result is not source
    assert result.states == completed.states
    assert result.input_symbols == completed.input_symbols
    assert result.initial_state == completed.initial_state
    assert result.transitions == completed.transitions
    assert result.final_states == completed.states - completed.final_states
    assert sink in result.final_states
    assert result.transitions[sink] == {"a": sink, "b": sink}
    assert result.allow_partial is False
    assert result.is_complete() is True


def test_complete_dfa_complement_keeps_structure_without_sink() -> None:
    source = ExtendedDFA(
        states={"s", "f"}, input_symbols={"a", "b"},
        transitions={
            "s": {"a": "f", "b": "s"},
            "f": {"a": "f", "b": "s"},
        },
        initial_state="s", final_states={"f"},
    )
    result = source.complement()
    assert result is not source
    assert result.states == source.states
    assert result.transitions == source.transitions
    assert result.initial_state == source.initial_state
    assert result.input_symbols == source.input_symbols
    assert result.final_states == source.states - source.final_states
    assert result.is_complete() is True


def test_source_compatibility_default_is_unminimized() -> None:
    """Derive the mature example's no-argument, minify=False behavior."""
    d = ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a"},
        transitions={
            "0": {"a": "1"}, "1": {"a": "1"}, "2": {"a": "2"},
        },
        initial_state="0", final_states={"0"},
    )
    c1 = d.complement()
    explicit = d.complement(minify=False)
    assert c1.accepts_input("a") is True
    assert c1.states == d.states  # unreachable state "2" is not minified away
    assert c1.states == explicit.states
    assert c1.transitions == explicit.transitions
    assert c1.final_states == explicit.final_states


@pytest.mark.parametrize("word", ["", "a", "aa", "b", "ab", "ba", "bb"])
def test_complement_language_of_partial_dfa(word: str) -> None:
    source = _partial_dfa()
    result = source.complement()
    assert result.accepts(word) is (not source.accepts(word))


def test_missing_transition_is_accepted_after_complement() -> None:
    source = _partial_dfa()
    assert source.accepts("b") is False
    assert source.complement().accepts("b") is True
    assert source.accepts("") is True
    assert source.complement().accepts("") is False


@pytest.mark.parametrize("word", ["", "a", "aa", "b", "ab", "ba", "bb"])
def test_double_complement_preserves_language(word: str) -> None:
    source = _partial_dfa()
    restored = source.complement().complement()
    assert restored.accepts(word) is source.accepts(word)


@pytest.mark.parametrize("final_states", [set(), {"q"}])
def test_no_final_or_all_final_states(final_states: set[str]) -> None:
    source = ExtendedDFA(
        states={"q"}, input_symbols={"a"},
        transitions={"q": {"a": "q"}},
        initial_state="q", final_states=final_states,
    )
    result = source.complement()
    assert result.final_states == source.states - source.final_states
    for word in ("", "a", "aa"):
        assert result.accepts(word) is (not source.accepts(word))


def test_empty_alphabet_is_complemented_without_sink() -> None:
    source = ExtendedDFA(
        states={"q"}, input_symbols=set(), transitions={"q": {}},
        initial_state="q", final_states=set(),
    )
    result = source.complement()
    assert result.states == source.states
    assert result.final_states == source.states
    assert result.accepts("") is True
    assert result.is_complete() is True


def test_none_and_heterogeneous_states() -> None:
    source = ExtendedDFA(
        states={None, "q", 7}, input_symbols={"a"},
        transitions={None: {"a": "q"}, "q": {"a": 7}, 7: {"a": 7}},
        initial_state=None, final_states={"q"},
    )
    result = source.complement()
    assert result.states == source.states
    assert result.initial_state is None
    assert result.final_states == {None, 7}
    assert result.is_complete() is True


def test_retain_names_is_accepted_without_minification() -> None:
    source = _partial_dfa()
    plain = source.complement()
    with_names = source.complement(retain_names=True)
    assert with_names is not plain
    assert with_names.states == plain.states
    assert with_names.transitions == plain.transitions
    assert with_names.final_states == plain.final_states


@pytest.mark.parametrize("retain_names", [False, True])
def test_minify_true_uses_extension_minimization(retain_names: bool) -> None:
    source = _partial_dfa()
    result = source.complement(minify=True, retain_names=retain_names)
    assert type(result) is ExtendedDFA
    assert result.is_minimal() is True
    assert result.is_equivalent(source.complement()) is True
    assert source.is_complete() is False


def test_source_compatibility_minified_complement_retains_names() -> None:
    d = ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a"},
        transitions={"0": {"a": "1"}, "1": {"a": "2"}, "2": {"a": "0"}},
        initial_state="0", final_states={"2"},
    )
    c2 = d.complement(minify=True, retain_names=True)
    assert sorted(c2.states) == ["0", "1", "2"]
    assert c2.is_minimal() is True


def test_complement_does_not_mutate_source() -> None:
    source = _partial_dfa()
    before = (
        deepcopy(source.states), deepcopy(source.transitions),
        deepcopy(source.final_states), deepcopy(source.input_symbols),
        source.initial_state, source.allow_partial,
    )
    result = source.complement()
    assert result is not source
    assert (
        source.states, source.transitions, source.final_states,
        source.input_symbols, source.initial_state, source.allow_partial,
    ) == before


def test_complement_result_remains_composable() -> None:
    result = _partial_dfa().complement()
    assert type(result) is ExtendedDFA
    assert result.is_complete() is True
    assert result.complete().is_complete() is True
    assert result.accessible_states() == result.reachable_states("0")


def test_complement_mro_is_dfa_only() -> None:
    assert ExtendedDFA.complement is ComplementMixin.complement
    assert ComplementMixin in ExtendedDFA.__mro__
    for cls in (ExtendedNFA, ExtendedGNFA):
        assert ComplementMixin not in cls.__mro__
