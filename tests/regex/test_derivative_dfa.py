"""Direct derivative automata, independent language checks and normalization."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
from itertools import product
from unittest.mock import patch

import pytest
from automata.fa.dfa import DFA
from automata.fa.nfa import NFA

from automata_extensions.fa import ExtendedDFA, ExtendedNFA
from automata_extensions.regex import Regex, _ast
from automata_extensions.regex._derivative_dfa import _normalize


@pytest.mark.parametrize("expression", [
    "ab", "a*b", "(a|b)*a*b*",  # TD51.1-3
    "(a*b|dc)*(b*d|ad)*", "(ab|a*b|cd)((ca*|bd)(ab*|abd))*",  # TD51.4-5
    "", "()", "a", "a|b", "(a|())b", "(a|aa)*",
    "(a*|b*)*", "((a|b)*a(a|b)*)*", "(ab|ba)*", "(a|ab|ba)*",
])
def test_matches_independent_upstream_and_extension_thompson(expression: str) -> None:
    alphabet = set("abcd") if "c" in expression or "d" in expression else set("ab")
    source = Regex(expression, input_symbols=alphabet)
    derived = source.to_dfa()
    upstream = DFA.from_nfa(NFA.from_regex(expression, input_symbols=alphabet))
    thompson = ExtendedNFA.from_regex(expression, input_symbols=alphabet).determinize()
    assert type(derived) is ExtendedDFA
    assert derived.is_complete() is True
    assert upstream == derived
    assert derived.is_equivalent(thompson)
    assert derived.accessible_states() == derived.states
    for length in range(4):
        for letters in product(sorted(alphabet), repeat=length):
            word = "".join(letters)
            assert derived.accepts(word) is upstream.accepts_input(word)


def test_states_are_regexes_and_each_transition_is_a_left_quotient() -> None:
    alphabet = {"a", "b", "c"}
    dfa = Regex("ab|ac", input_symbols=alphabet).to_dfa()
    assert all(isinstance(state, Regex) for state in dfa.states)
    assert str(dfa.initial_state) == "ab|ac"
    after_a = dfa.transitions[dfa.initial_state]["a"]
    assert str(after_a) == "b|c"
    for state in dfa.states:
        assert set(dfa.transitions[state]) == alphabet
        assert (state in dfa.final_states) is _ast.nullable(state._root)
        for symbol, target in dfa.transitions[state].items():
            assert target._root == _normalize(state.derivative(symbol)._root)


@pytest.mark.parametrize("expression,accepting", [("", True), ("()", True)])
def test_empty_alphabet_has_one_complete_state(expression: str, accepting: bool) -> None:
    dfa = Regex(expression, input_symbols=set()).to_dfa()
    assert len(dfa.states) == 1
    assert dfa.is_complete()
    assert dfa.accepts("") is accepting
    assert not dfa.accepts("a")
    assert dict(dfa.transitions[dfa.initial_state]) == {}


def test_internal_empty_language_does_not_become_a_literal_when_converted() -> None:
    empty = Regex("a", input_symbols={"a", "b"}).derivative("b")
    dfa = empty.to_dfa()
    assert len(dfa.states) == 1
    assert dfa.is_empty()
    assert not dfa.accepts("")
    assert all(target == dfa.initial_state for target in dfa.transitions[dfa.initial_state].values())


def test_literal_empty_set_glyph_and_empty_language_are_distinct_states() -> None:
    dfa = Regex("∅", input_symbols={"∅", "a"}).to_dfa()
    assert dfa.accepts("∅")
    assert not dfa.accepts("")
    assert not dfa.accepts("∅∅")
    initial = dfa.initial_state
    sink = dfa.transitions[initial]["a"]
    assert str(initial) == str(sink) == "∅"
    assert initial != sink
    assert isinstance(initial._root, _ast.Literal)
    assert isinstance(sink._root, _ast.EmptyLanguage)
    assert sink not in dfa.final_states
    assert all(target == sink for target in dfa.transitions[sink].values())


def test_explicit_extra_alphabet_symbols_get_a_rejecting_sink() -> None:
    dfa = Regex("a*", input_symbols={"a", "b", "c"}).to_dfa()
    assert dfa.input_symbols == frozenset({"a", "b", "c"})
    assert len(dfa.states) == 2
    assert dfa.accepts("aaa")
    assert not dfa.accepts("b")
    assert not dfa.accepts("ac")


def test_alphabet_is_inferred_and_unicode_characters_are_supported() -> None:
    dfa = Regex("éλ*").to_dfa()
    assert dfa.input_symbols == frozenset({"é", "λ"})
    assert dfa.accepts("éλλ")
    assert not dfa.accepts("λé")


@pytest.mark.parametrize("left,right", [
    ("a|b", "b|a"), ("a|(b|a)", "b|a"),
    ("(a|b)|c", "c|(b|a)"), ("(ab)c", "a(bc)"),
    ("(a|b)*", "(b|a)*"), ("()a|a()", "a"),
])
def test_aci_and_associative_normal_forms_have_identical_graphs(left: str, right: str) -> None:
    first = Regex(left, input_symbols=set("abc")).to_dfa()
    second = Regex(right, input_symbols=set("abc")).to_dfa()
    assert first.states == second.states
    assert first.transitions == second.transitions
    assert first.initial_state == second.initial_state
    assert first.final_states == second.final_states


def test_reordered_duplicate_alternatives_terminate_on_ambiguous_star() -> None:
    source = Regex("((a|aa)|(aa|a))*", input_symbols={"a", "b"})
    dfa = source.to_dfa()
    assert len(dfa.states) < 10
    assert dfa == DFA.from_nfa(NFA.from_regex("a*", input_symbols={"a", "b"}))


def test_conversion_calls_derivatives_without_thompson_or_subset_construction() -> None:
    source = Regex("ab|ac")
    original_derivative = Regex.derivative
    calls: list[tuple[Regex, str]] = []

    def traced(self: Regex, symbol: str) -> Regex:
        calls.append((self, symbol))
        return original_derivative(self, symbol)

    with (
        patch.object(Regex, "derivative", traced),
        patch.object(ExtendedNFA, "from_regex", side_effect=AssertionError("Thompson")),
        patch.object(NFA, "from_regex", side_effect=AssertionError("upstream regex")),
        patch.object(ExtendedNFA, "determinize", side_effect=AssertionError("subsets")),
        patch.object(DFA, "from_nfa", side_effect=AssertionError("upstream subsets")),
    ):
        dfa = source.to_dfa()
    assert dfa.accepts("ab") and dfa.accepts("ac")
    assert len(calls) == len(dfa.states) * len(dfa.input_symbols)


def test_source_is_unchanged_results_are_fresh_and_transforms_compose() -> None:
    source = Regex("(a|b)*a", input_symbols={"a", "b"})
    before = deepcopy(source)
    rendered = str(source)
    first = source.to_dfa()
    again = source.to_dfa()
    assert source == before and str(source) == rendered
    assert first is not again and first.is_equivalent(again)
    assert first.trim().minimize().is_equivalent(first)
    assert first.complement().complement().is_equivalent(first)
    assert source.derivative("a").to_dfa().is_equivalent(first.left_quotient_word("a"))
    with pytest.raises(FrozenInstanceError):
        first.initial_state._root = _ast.EMPTY


def test_existing_derivative_rendering_is_unchanged() -> None:
    assert str(Regex("b|a").derivative("z")) == "∅"
    assert str(Regex("(b|a)*").derivative("a")) == "(b|a)*"
    assert str(Regex("(a|b)*a").derivative("a")) == "(a|b)*a|()"
