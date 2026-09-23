"""Word recognition delegates to automata-lib's established simulation."""

from copy import deepcopy
from unittest.mock import patch

import pytest
from automata.base.exceptions import RejectionException

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


@pytest.mark.parametrize(
    ("word", "expected"),
    [("a", ["s", "f"]), ("aaa", ["s", "f", "f", "f"])],
)
def test_dfa_accepted_word_trace_matches_upstream(
    word: str, expected: list[str]
) -> None:
    dfa = _dfa()
    trace = dfa.execution_trace(word)
    assert type(trace) is list
    assert trace == expected
    assert trace == list(dfa.read_input_stepwise(word))
    assert trace[0] == dfa.initial_state
    assert len(trace) == len(word) + 1


@pytest.mark.parametrize(
    ("word", "expected"),
    [("", ["s"]), ("b", ["s", None]), ("aa", ["s", "f", None])],
)
def test_dfa_rejected_trace_keeps_final_configuration(
    word: str, expected: list[str | None]
) -> None:
    dfa = ExtendedDFA(
        states={"s", "f"}, input_symbols={"a"},
        transitions={"s": {"a": "f"}, "f": {}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    with pytest.raises(RejectionException):
        list(dfa.read_input_stepwise(word))
    assert dfa.execution_trace(word) == expected
    assert len(dfa.execution_trace(word)) == len(word) + 1


def test_dfa_empty_accepted_trace() -> None:
    dfa = _dfa(initial_final=True)
    assert dfa.execution_trace("") == [dfa.initial_state]
    assert dfa.execution_trace("") == list(dfa.read_input_stepwise(""))


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        ("a", [frozenset({"s"}), frozenset({"left", "right", "f"})]),
        ("ab", [frozenset({"s"}), frozenset({"left", "right", "f"}), frozenset({"f"})]),
    ],
)
def test_nfa_accepted_trace_tracks_active_sets(
    word: str, expected: list[frozenset[str]]
) -> None:
    nfa = _nfa()
    trace = nfa.execution_trace(word)
    assert type(trace) is list
    assert trace == expected
    assert trace == list(nfa.read_input_stepwise(word))
    assert all(type(configuration) is frozenset for configuration in trace)
    assert len(trace) == len(word) + 1


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        ("", [frozenset({"s"})]),
        ("b", [frozenset({"s"}), frozenset()]),
        (
            "abb",
            [
                frozenset({"s"}),
                frozenset({"left", "right", "f"}),
                frozenset({"f"}),
                frozenset(),
            ],
        ),
    ],
)
def test_nfa_rejected_trace_keeps_empty_configuration(
    word: str, expected: list[frozenset[str]]
) -> None:
    nfa = _nfa()
    with pytest.raises(RejectionException):
        list(nfa.read_input_stepwise(word))
    trace = nfa.execution_trace(word)
    assert trace == expected
    assert all(type(configuration) is frozenset for configuration in trace)


@pytest.mark.parametrize("word", ["", "a"])
def test_nfa_initial_epsilon_closure_and_epsilon_after_symbol(word: str) -> None:
    nfa = ExtendedNFA(
        states={"s", "middle", "target", "f"},
        input_symbols={"a"},
        transitions={
            "s": {"": {"middle"}},
            "middle": {"a": {"target"}},
            "target": {"": {"f"}},
        },
        initial_state="s", final_states={"f"},
    )
    trace = nfa.execution_trace(word)
    assert trace[0] == frozenset({"s", "middle"})
    if word:
        assert trace == [frozenset({"s", "middle"}), frozenset({"target", "f"})]
        assert trace == list(nfa.read_input_stepwise(word))
    else:
        assert trace == [frozenset({"s", "middle"})]


def test_nfa_empty_word_accepted_through_epsilon_trace() -> None:
    nfa = ExtendedNFA(
        states={"s", "f"}, input_symbols=set(),
        transitions={"s": {"": {"f"}}},
        initial_state="s", final_states={"f"},
    )
    assert nfa.execution_trace("") == [frozenset({"s", "f"})]
    assert nfa.execution_trace("") == list(nfa.read_input_stepwise(""))


def test_trace_propagates_unrelated_upstream_errors() -> None:
    dfa = _dfa()
    with patch.object(
        ExtendedDFA, "read_input_stepwise", side_effect=ValueError("broken")
    ):
        with pytest.raises(ValueError, match="broken"):
            dfa.execution_trace("a")


@pytest.mark.parametrize("kind", ["dfa", "nfa"])
def test_execution_trace_preserves_source(kind: str) -> None:
    automaton = _dfa() if kind == "dfa" else _nfa()
    original = (
        deepcopy(automaton.states),
        deepcopy(automaton.transitions),
        deepcopy(automaton.final_states),
    )
    for word in ("", "a", "ab"):
        automaton.execution_trace(word)
    assert (automaton.states, automaton.transitions, automaton.final_states) == original


def test_gnfa_trace_limitation_matches_word_recognition() -> None:
    gnfa = ExtendedGNFA(
        states={"s", "f"}, input_symbols={"a"},
        transitions={"s": {"f": "a"}},
        initial_state="s", final_state="f",
    )
    original = deepcopy(gnfa.transitions)
    with pytest.raises(
        NotImplementedError, match="GNFA execution traces are unsupported"
    ):
        gnfa.execution_trace("a")
    with pytest.raises(
        NotImplementedError, match="GNFA word recognition is unsupported"
    ):
        gnfa.accepts("a")
    assert gnfa.transitions == original
