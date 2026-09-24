"""DFA state elimination with the professor's verbose lexical rendering."""

from copy import deepcopy
from itertools import product

import pytest
from automata.fa.gnfa import GNFA
from automata.fa.nfa import NFA

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.fa_mixins.regex import RegexMixin
from tests.fa.test_state_elimination import _mature_dfa


def _assert_same_language(dfa: ExtendedDFA, expression: str | None) -> None:
    if expression is None:
        assert dfa.is_empty() is True
        return
    oracle = NFA.from_regex(expression, input_symbols=dfa.input_symbols)
    for length in range(5):
        for symbols in product(sorted(dfa.input_symbols), repeat=length):
            word = "".join(symbols)
            assert oracle.accepts_input(word) is dfa.accepts_input(word)


def test_mature_exact_output_and_upstream_difference() -> None:
    dfa = _mature_dfa()
    expression = dfa.to_regex()
    assert expression == "(b*|b*ab*a((b|ab*ab*a))*ab*)"
    assert GNFA.from_dfa(dfa).to_regex() == "(ab*ab*a|b)*"
    assert type(expression) is str
    _assert_same_language(dfa, expression)
    assert ExtendedNFA.from_regex(expression, input_symbols={"a", "b"}).accepts_input("aba") is False


def test_empty_language_follows_requirement_39_convention() -> None:
    dfa = ExtendedDFA(
        states={"q"}, input_symbols={"a"}, transitions={"q": {}},
        initial_state="q", final_states=set(), allow_partial=True,
    )
    assert dfa.to_regex() is None
    assert ExtendedGNFA.from_dfa(dfa).to_regex() is None
    _assert_same_language(dfa, dfa.to_regex())


@pytest.mark.parametrize(
    ("states", "symbols", "transitions", "initial", "finals", "partial", "expected"),
    [
        ({"q"}, set(), {"q": {}}, "q", {"q"}, False, ""),
        ({"q"}, {"a"}, {"q": {"a": "q"}}, "q", {"q"}, False, "a*"),
        ({"q0", "q1"}, {"a"}, {"q0": {"a": "q1"}, "q1": {}},
         "q0", {"q1"}, True, "a"),
        ({"q0", "q1"}, {"a"}, {"q0": {"a": "q1"}, "q1": {}},
         "q0", {"q0", "q1"}, True, "(()|a)"),
        ({"q0", "q1"}, {"a", "b"},
         {"q0": {"a": "q1", "b": "q0"}, "q1": {}},
         "q0", {"q0", "q1"}, True, "(b*|b*a)"),
    ],
)
def test_minimal_finite_cyclic_and_multiple_final_cases(
    states: set[str], symbols: set[str],
    transitions: dict[str, dict[str, str]], initial: str, finals: set[str],
    partial: bool, expected: str,
) -> None:
    dfa = ExtendedDFA(
        states=states, input_symbols=symbols, transitions=transitions,
        initial_state=initial, final_states=finals, allow_partial=partial,
    )
    expression = dfa.to_regex()
    assert expression == expected
    _assert_same_language(dfa, expression)
    # These expressions use only the #51 grammar.
    assert expression is not None
    thompson = ExtendedNFA.from_regex(expression, input_symbols=symbols)
    for length in range(4):
        for letters in product(sorted(symbols), repeat=length):
            word = "".join(letters)
            assert thompson.accepts_input(word) is dfa.accepts_input(word)


def test_unreachable_states_do_not_change_language() -> None:
    dfa = ExtendedDFA(
        states={"0", "1", "unused"}, input_symbols={"a"},
        transitions={"0": {"a": "1"}, "1": {},
                     "unused": {"a": "unused"}},
        initial_state="0", final_states={"1", "unused"}, allow_partial=True,
    )
    _assert_same_language(dfa, dfa.to_regex())


def test_parallel_symbols_and_lexical_order() -> None:
    dfa = ExtendedDFA(
        states={"z", "a"}, input_symbols={"a", "b"},
        transitions={"z": {"a": "a", "b": "a"}, "a": {}},
        initial_state="z", final_states={"a"}, allow_partial=True,
    )
    expression = dfa.to_regex()
    assert expression == dfa.to_regex()
    _assert_same_language(dfa, expression)


def test_none_and_heterogeneous_state_names() -> None:
    dfa = ExtendedDFA(
        states={0, "0", None}, input_symbols={"a"},
        transitions={0: {"a": "0"}, "0": {}, None: {}},
        initial_state=0, final_states={"0"}, allow_partial=True,
    )
    assert dfa.to_regex() == "a"
    _assert_same_language(dfa, dfa.to_regex())


def test_source_immutable_return_type_and_mro() -> None:
    dfa = _mature_dfa()
    before = deepcopy(dfa.input_parameters), dict(vars(dfa))
    first = dfa.to_regex()
    assert first == dfa.to_regex()
    assert type(first) is str
    assert (dfa.input_parameters, vars(dfa)) == before
    assert ExtendedDFA.to_regex is RegexMixin.to_regex
    assert ExtendedGNFA.to_regex is GNFA.to_regex
    assert RegexMixin in ExtendedDFA.__mro__
    assert RegexMixin not in ExtendedNFA.__mro__
    assert RegexMixin not in ExtendedGNFA.__mro__
