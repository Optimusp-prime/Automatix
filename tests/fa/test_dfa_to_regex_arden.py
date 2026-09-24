"""DFA language-equation conversion by Arden's lemma (requirement #54)."""

from copy import deepcopy
from itertools import product

import pytest
from automata.fa.nfa import NFA

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.fa_mixins.regex_arden import ArdenMixin
from tests.fa.test_state_elimination import _mature_dfa


def _check_language(dfa: ExtendedDFA, expression: str | None) -> None:
    words = (
        "".join(letters)
        for length in range(5)
        for letters in product(sorted(dfa.input_symbols), repeat=length)
    )
    if expression is None:
        assert dfa.is_empty() is True
        assert all(not dfa.accepts_input(word) for word in words)
        return
    oracle = NFA.from_regex(expression, input_symbols=dfa.input_symbols)
    assert all(
        oracle.accepts_input(word) is dfa.accepts_input(word)
        for word in words
    )


def test_mature_arden_output_exact_and_distinct_from_state_elimination() -> None:
    dfa = _mature_dfa()
    expression = dfa.to_regex_arden()
    assert expression == "b*(ab*a((ab*ab*a|b))*ab*|())"
    assert dfa.to_regex() == "(b*|b*ab*a((b|ab*ab*a))*ab*)"
    assert expression != dfa.to_regex()
    _check_language(dfa, expression)
    _check_language(dfa, dfa.to_regex())
    assert expression is not None
    thompson = ExtendedNFA.from_regex(expression, input_symbols={"a", "b"})
    assert thompson.accepts_input("") is True
    assert thompson.accepts_input("aba") is False


@pytest.mark.parametrize(
    ("final", "loop", "expected"),
    [
        (False, False, None),
        (True, False, ""),
        (True, True, "a*"),
        (False, True, None),
    ],
)
def test_one_state_empty_epsilon_and_self_recursive_arden(
    final: bool, loop: bool, expected: str | None,
) -> None:
    dfa = ExtendedDFA(
        states={"q"}, input_symbols={"a"},
        transitions={"q": {"a": "q"} if loop else {}},
        initial_state="q", final_states={"q"} if final else set(),
        allow_partial=not loop,
    )
    assert dfa.to_regex_arden() == expected
    _check_language(dfa, expected)
    assert (dfa.to_regex_arden() is None) is (not final)


def test_transition_direction_and_partial_finite_chain() -> None:
    dfa = ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a", "b"},
        transitions={"0": {"a": "1"}, "1": {"b": "2"}, "2": {}},
        initial_state="0", final_states={"2"}, allow_partial=True,
    )
    assert dfa.to_regex_arden() == "ab"
    assert dfa.accepts_input("ab") is True
    assert dfa.accepts_input("ba") is False
    _check_language(dfa, dfa.to_regex_arden())


def test_multiple_finals_and_initial_final_epsilon_alternative() -> None:
    dfa = ExtendedDFA(
        states={"q0", "q1"}, input_symbols={"a"},
        transitions={"q0": {"a": "q1"}, "q1": {}},
        initial_state="q0", final_states={"q0", "q1"}, allow_partial=True,
    )
    assert dfa.to_regex_arden() == "(a|())"
    _check_language(dfa, dfa.to_regex_arden())


def test_multiple_outgoing_edges_and_mutual_recursion() -> None:
    dfa = ExtendedDFA(
        states={"0", "1"}, input_symbols={"a", "b"},
        transitions={"0": {"a": "1", "b": "0"},
                     "1": {"a": "0", "b": "1"}},
        initial_state="0", final_states={"1"},
    )
    expression = dfa.to_regex_arden()
    assert expression is not None
    assert expression == dfa.to_regex_arden()
    _check_language(dfa, expression)


def test_inaccessible_final_state_does_not_affect_equations() -> None:
    dfa = ExtendedDFA(
        states={"0", "1", "unused"}, input_symbols={"a"},
        transitions={"0": {"a": "1"}, "1": {},
                     "unused": {"a": "unused"}},
        initial_state="0", final_states={"1", "unused"}, allow_partial=True,
    )
    reachable_only = ExtendedDFA(
        states={"0", "1"}, input_symbols={"a"},
        transitions={"0": {"a": "1"}, "1": {}},
        initial_state="0", final_states={"1"}, allow_partial=True,
    )
    assert dfa.to_regex_arden() == reachable_only.to_regex_arden() == "a"
    _check_language(dfa, dfa.to_regex_arden())


def test_none_and_heterogeneous_states() -> None:
    dfa = ExtendedDFA(
        states={0, "0", None}, input_symbols={"a"},
        transitions={0: {"a": "0"}, "0": {}, None: {}},
        initial_state=0, final_states={"0"}, allow_partial=True,
    )
    assert dfa.to_regex_arden() == "a"
    _check_language(dfa, dfa.to_regex_arden())


def test_source_unchanged_and_dfa_only_mro() -> None:
    dfa = _mature_dfa()
    before = deepcopy(dfa.input_parameters), dict(vars(dfa))
    assert type(dfa.to_regex_arden()) is str
    assert dfa.to_regex_arden() == dfa.to_regex_arden()
    assert (dfa.input_parameters, vars(dfa)) == before
    assert ExtendedDFA.to_regex_arden is ArdenMixin.to_regex_arden
    assert ArdenMixin in ExtendedDFA.__mro__
    assert ArdenMixin not in ExtendedNFA.__mro__
    assert ArdenMixin not in ExtendedGNFA.__mro__
    assert not hasattr(ExtendedNFA, "to_regex_arden")
    assert not hasattr(ExtendedGNFA, "to_regex_arden")
