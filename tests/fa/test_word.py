"""Word recognition delegates to automata-lib's established simulation."""

from copy import deepcopy
from unittest.mock import patch

import pytest

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.fa_mixins.word import WordMixin


def _dfa(*, initial_final: bool = False) -> ExtendedDFA:
    return ExtendedDFA(
        states={"s", "f"},
        input_symbols={"a"},
        transitions={"s": {"a": "f"}, "f": {"a": "f"}},
        initial_state="s",
        final_states={"s", "f"} if initial_final else {"f"},
    )


def _nfa() -> ExtendedNFA:
    # One branch accepts immediately; another consumes a second symbol.
    return ExtendedNFA(
        states={"s", "left", "right", "f"},
        input_symbols={"a", "b"},
        transitions={
            "s": {"a": {"left", "right"}},
            "left": {"": {"f"}},
            "right": {"b": {"f"}},
        },
        initial_state="s",
        final_states={"f"},
    )


@pytest.mark.parametrize(
    ("word", "expected"),
    [("", False), ("a", True), ("aa", True), ("aaa", True), ("b", False), ("ab", False)],
)
def test_dfa_acceptance_matches_upstream(word: str, expected: bool) -> None:
    dfa = _dfa()
    result = dfa.accepts(word)
    assert type(result) is bool
    assert result is expected
    assert result is dfa.accepts_input(word)


def test_dfa_accepts_empty_word_when_initial_state_is_final() -> None:
    dfa = _dfa(initial_final=True)
    assert dfa.accepts("") is True
    assert dfa.accepts("a") is True


@pytest.mark.parametrize("word", ["", "a", "aa", "b"])
def test_partial_dfa_missing_transition_and_invalid_symbol(word: str) -> None:
    dfa = ExtendedDFA(
        states={"s", "f"}, input_symbols={"a"},
        transitions={"s": {"a": "f"}, "f": {}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    assert dfa.accepts(word) is dfa.accepts_input(word)
    assert dfa.accepts(word) is (word == "a")


@pytest.mark.parametrize(
    ("word", "expected"),
    [("", False), ("a", True), ("ab", True), ("abb", False), ("b", False), ("c", False)],
)
def test_nfa_branches_and_epsilon_after_consumption(
    word: str, expected: bool
) -> None:
    nfa = _nfa()
    result = nfa.accepts(word)
    assert type(result) is bool
    assert result is expected
    assert result is nfa.accepts_input(word)


@pytest.mark.parametrize(
    ("word", "expected"),
    [("", False), ("a", True), ("aa", False), ("b", False)],
)
def test_nfa_epsilon_before_symbol(word: str, expected: bool) -> None:
    nfa = ExtendedNFA(
        states={"s", "middle", "f"}, input_symbols={"a"},
        transitions={"s": {"": {"middle"}}, "middle": {"a": {"f"}}},
        initial_state="s", final_states={"f"},
    )
    assert nfa.accepts(word) is expected
    assert nfa.accepts(word) is nfa.accepts_input(word)


@pytest.mark.parametrize("accepting", [False, True])
def test_nfa_empty_word_via_epsilon(accepting: bool) -> None:
    nfa = ExtendedNFA(
        states={"s", "f"}, input_symbols=set(),
        transitions={"s": {"": {"f"}} if accepting else {}},
        initial_state="s", final_states={"f"},
    )
    assert nfa.accepts("") is accepting
    assert nfa.accepts("") is nfa.accepts_input("")


@pytest.mark.parametrize("kind", ["dfa", "nfa"])
def test_alias_calls_upstream_once(kind: str) -> None:
    automaton = _dfa() if kind == "dfa" else _nfa()
    with patch.object(type(automaton), "accepts_input", return_value=True) as upstream:
        assert automaton.accepts("a") is True
    upstream.assert_called_once_with("a")


def test_gnfa_explicitly_reports_upstream_limitation() -> None:
    gnfa = ExtendedGNFA(
        states={"s", "f"}, input_symbols={"a"},
        transitions={"s": {"f": "a"}},
        initial_state="s", final_state="f",
    )
    original = (
        deepcopy(gnfa.states),
        deepcopy(gnfa.transitions),
        deepcopy(gnfa.final_states),
    )
    with pytest.raises(NotImplementedError):
        gnfa.accepts_input("a")
    with pytest.raises(NotImplementedError, match="GNFA word recognition is unsupported"):
        gnfa.accepts("a")
    assert (gnfa.states, gnfa.transitions, gnfa.final_states) == original


@pytest.mark.parametrize("kind", ["dfa", "nfa"])
def test_word_recognition_preserves_automaton(kind: str) -> None:
    automaton = _dfa() if kind == "dfa" else _nfa()
    states = deepcopy(automaton.states)
    transitions = deepcopy(automaton.transitions)
    final_states = deepcopy(automaton.final_states)
    for word in ("", "a", "ab"):
        automaton.accepts(word)
    assert automaton.states == states
    assert automaton.transitions == transitions
    assert automaton.final_states == final_states


def test_public_classes_inherit_common_word_mixin() -> None:
    for cls in (ExtendedDFA, ExtendedNFA, ExtendedGNFA):
        assert WordMixin in cls.__mro__
