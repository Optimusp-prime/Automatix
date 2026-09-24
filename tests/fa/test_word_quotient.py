"""Left and right quotients by words on extended DFA/NFA classes."""

from copy import deepcopy

import pytest
from automata.fa.nfa import NFA

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.dfa_mixins.quotient import DFAQuotientMixin
from automata_extensions.fa.nfa_mixins.quotient import NFAQuotientMixin
from tests.fa.test_state_elimination import _mature_dfa


def _partial_dfa() -> ExtendedDFA:
    return ExtendedDFA(
        states={"s", "f", "unreachable"}, input_symbols={"a", "b"},
        transitions={
            "s": {"a": "f"},
            "f": {"b": "f"},
            "unreachable": {"a": "unreachable"},
        },
        initial_state="s", final_states={"f"}, allow_partial=True,
    )


def _epsilon_nfa() -> ExtendedNFA:
    return ExtendedNFA(
        states={"s", "p", "q", "r", "f"}, input_symbols={"a", "b"},
        transitions={
            "s": {"": {"p"}},
            "p": {"a": {"q"}},
            "q": {"": {"r"}},
            "r": {"b": {"f"}},
        },
        initial_state="s", final_states={"f"},
    )


def test_mature_source_compatibility_both_word_quotients() -> None:
    d = _mature_dfa()
    left = d.left_quotient_word("a")
    right = d.right_quotient_word("a")
    assert (left.accepts_input("aa"), right.accepts_input("aa")) == (True, True)
    assert type(left) is ExtendedDFA
    assert type(right) is ExtendedDFA


@pytest.mark.parametrize("word", ["", "a", "b", "ab", "bb", "x"])
@pytest.mark.parametrize("suffix", ["", "a", "b", "ab", "ba"])
def test_dfa_left_quotient_language_identity(word: str, suffix: str) -> None:
    source = _partial_dfa()
    result = source.left_quotient_word(word)
    assert type(result) is ExtendedDFA
    assert result.accepts_input(suffix) is source.accepts_input(word + suffix)


@pytest.mark.parametrize("word", ["", "a", "b", "ab", "bb", "x"])
@pytest.mark.parametrize("prefix", ["", "a", "b", "ab", "ba"])
def test_dfa_right_quotient_language_identity(word: str, prefix: str) -> None:
    source = _partial_dfa()
    result = source.right_quotient_word(word)
    assert type(result) is ExtendedDFA
    assert result.accepts_input(prefix) is source.accepts_input(prefix + word)


def test_dfa_left_changes_only_initial_for_defined_word() -> None:
    source = _partial_dfa()
    result = source.left_quotient_word("a")
    assert result is not source
    assert result.states == source.states
    assert result.input_symbols == source.input_symbols
    assert result.transitions == source.transitions
    assert result.final_states == source.final_states
    assert result.allow_partial is source.allow_partial
    assert result.initial_state == "f"
    assert "unreachable" in result.states
    assert result.accepts_input("") is True


def test_dfa_missing_edge_and_unknown_symbol_yield_empty_language() -> None:
    source = _partial_dfa()
    for word in ("b", "aa", "x"):
        result = source.left_quotient_word(word)
        assert type(result) is ExtendedDFA
        assert result.is_empty() is True
        assert result.input_symbols == source.input_symbols
        for suffix in ("", "a", "b", "ab"):
            assert result.accepts_input(suffix) is False


@pytest.mark.parametrize("final", [False, True])
def test_one_state_dfa_empty_word_and_language_extremes(final: bool) -> None:
    source = ExtendedDFA(
        states={"q"}, input_symbols={"a"},
        transitions={"q": {"a": "q"}}, initial_state="q",
        final_states={"q"} if final else set(),
    )
    for result in (source.left_quotient_word(""),
                   source.right_quotient_word("")):
        assert type(result) is ExtendedDFA
        for word in ("", "a", "aa"):
            assert result.accepts_input(word) is final


def test_dfa_quotients_preserve_source_and_composability() -> None:
    source = _partial_dfa()
    before = deepcopy(source.input_parameters), source.allow_partial
    left = source.left_quotient_word("a")
    right = source.right_quotient_word("b")
    assert (source.input_parameters, source.allow_partial) == before
    assert left is not source and right is not source
    assert type(left.trim()) is ExtendedDFA
    assert type(right.complete()) is ExtendedDFA
    assert right.accepts_input("a") is True


def test_nfa_left_quotient_captures_multiple_active_states() -> None:
    source = ExtendedNFA(
        states={"s", "p", "q", "f"}, input_symbols={"a", "b", "c"},
        transitions={
            "s": {"a": {"p", "q"}},
            "p": {"b": {"f"}},
            "q": {"c": {"f"}},
        },
        initial_state="s", final_states={"f"},
    )
    result = source.left_quotient_word("a")
    assert type(result) is ExtendedNFA
    assert result.initial_state not in source.states
    assert result.transitions[result.initial_state][""] == {"p", "q"}
    assert result.accepts_input("b") is True
    assert result.accepts_input("c") is True
    assert result.accepts_input("") is False


@pytest.mark.parametrize("word", ["", "a", "b", "ab", "ba", "x"])
@pytest.mark.parametrize("suffix", ["", "a", "b", "ab", "bb"])
def test_nfa_left_quotient_language_identity(word: str, suffix: str) -> None:
    source = _epsilon_nfa()
    result = source.left_quotient_word(word)
    assert type(result) is ExtendedNFA
    assert result.accepts_input(suffix) is source.accepts_input(word + suffix)


@pytest.mark.parametrize("word", ["", "a", "b", "ab", "ba", "x"])
@pytest.mark.parametrize("prefix", ["", "a", "b", "ab", "bb"])
def test_nfa_right_quotient_language_identity(word: str, prefix: str) -> None:
    source = _epsilon_nfa()
    result = source.right_quotient_word(word)
    assert type(result) is ExtendedNFA
    assert result.accepts_input(prefix) is source.accepts_input(prefix + word)


def test_nfa_epsilon_closure_before_and_after_consumption() -> None:
    source = _epsilon_nfa()
    initial = source.left_quotient_word("")
    after_a = source.left_quotient_word("a")
    assert initial.transitions[initial.initial_state][""] == {"s", "p"}
    assert after_a.transitions[after_a.initial_state][""] == {"q", "r"}
    assert after_a.accepts_input("b") is True
    assert source.right_quotient_word("b").accepts_input("a") is True


def test_nfa_no_reached_state_and_invalid_symbol() -> None:
    source = _epsilon_nfa()
    for word in ("b", "x"):
        result = source.left_quotient_word(word)
        assert result.transitions[result.initial_state] == {}
        assert result.is_empty() is True
        assert result.accepts_input("") is False
        assert result.accepts_input("ab") is False


@pytest.mark.parametrize("final", [False, True])
def test_one_state_nfa_empty_word_and_language_extremes(final: bool) -> None:
    source = ExtendedNFA(
        states={"q"}, input_symbols={"a"},
        transitions={"q": {"a": {"q"}}}, initial_state="q",
        final_states={"q"} if final else set(),
    )
    for result in (source.left_quotient_word(""),
                   source.right_quotient_word("")):
        assert type(result) is ExtendedNFA
        for word in ("", "a", "aa"):
            assert result.accepts_input(word) is final


def test_right_quotient_reverses_multisymbol_word() -> None:
    source = ExtendedNFA(
        states={"s", "c", "a", "b"}, input_symbols={"a", "b", "c"},
        transitions={
            "s": {"c": {"c"}},
            "c": {"a": {"a"}},
            "a": {"b": {"b"}},
        },
        initial_state="s", final_states={"b"},
    )
    result = source.right_quotient_word("ab")
    assert result.accepts_input("c") is True
    assert result.accepts_input("a") is False
    assert result.accepts_input("") is False


def test_nfa_quotients_preserve_source_and_composability() -> None:
    source = _epsilon_nfa()
    before = deepcopy(source.input_parameters)
    left = source.left_quotient_word("a")
    right = source.right_quotient_word("b")
    assert source.input_parameters == before
    assert left is not source and right is not source
    assert type(left.determinize()) is ExtendedDFA
    assert type(right.remove_epsilon_transitions()) is ExtendedNFA


def test_names_avoid_upstream_automaton_quotient_collision_and_mro() -> None:
    assert ExtendedDFA.left_quotient_word is DFAQuotientMixin.left_quotient_word
    assert ExtendedDFA.right_quotient_word is DFAQuotientMixin.right_quotient_word
    assert ExtendedNFA.left_quotient_word is NFAQuotientMixin.left_quotient_word
    assert ExtendedNFA.right_quotient_word is NFAQuotientMixin.right_quotient_word
    assert ExtendedNFA.left_quotient is NFA.left_quotient
    assert ExtendedNFA.right_quotient is NFA.right_quotient
    assert not hasattr(ExtendedGNFA, "left_quotient_word")
    assert not hasattr(ExtendedGNFA, "right_quotient_word")
