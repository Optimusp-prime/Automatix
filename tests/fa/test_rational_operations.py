"""Concatenation and Kleene star via upstream epsilon-NFA constructions."""

from copy import deepcopy

import pytest
from automata.fa.nfa import NFA

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.dfa_mixins.set_operations import DFASetOperationsMixin
from automata_extensions.fa.fa_mixins.language_operations import LanguageOperationsMixin
from tests.fa.test_state_elimination import _mature_dfa


def _exact_symbol_dfa(symbol: str, alphabet: set[str]) -> ExtendedDFA:
    return ExtendedDFA(
        states={"s", "f"}, input_symbols=alphabet,
        transitions={"s": {symbol: "f"}, "f": {}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )


def _exact_symbol_nfa(symbol: str, alphabet: set[str]) -> ExtendedNFA:
    return ExtendedNFA(
        states={"s", "f"}, input_symbols=alphabet,
        transitions={"s": {symbol: {"f"}}},
        initial_state="s", final_states={"f"},
    )


def _epsilon_nfa(final: bool, alphabet: set[str]) -> ExtendedNFA:
    return ExtendedNFA(
        states={"q"}, input_symbols=alphabet, transitions={"q": {}},
        initial_state="q", final_states={"q"} if final else set(),
    )


def test_mature_source_compatibility_concatenation_and_star() -> None:
    d = _mature_dfa()
    c = d.concatenation(d)
    k = d.kleene_star()
    assert c.accepts_input("aaaaaa") is True
    assert k.accepts_input("") is True
    assert type(c) is ExtendedNFA
    assert type(k) is ExtendedNFA


def test_upstream_source_compatibility_concatenation() -> None:
    n1 = _exact_symbol_nfa("a", {"a", "b"})
    n2 = _exact_symbol_nfa("b", {"a", "b"})
    assert n1.concatenation(n2).accepts_input("ab") is True


def test_upstream_source_compatibility_kleene_star() -> None:
    n = ExtendedNFA(
        states={"s", "m", "f"}, input_symbols={"a", "b"},
        transitions={"s": {"a": {"m"}}, "m": {"b": {"f"}}},
        initial_state="s", final_states={"f"},
    )
    assert n.kleene_star().accepts_input("abab") is True


@pytest.mark.parametrize(
    ("word", "accepted"),
    [("", False), ("a", False), ("b", False), ("ab", True),
     ("aab", False), ("abb", False), ("ba", False)],
)
def test_dfa_concatenation_exact_language(word: str, accepted: bool) -> None:
    left = _exact_symbol_dfa("a", {"a", "b"})
    right = _exact_symbol_dfa("b", {"a", "b"})
    result = left.concatenation(right)
    assert type(result) is ExtendedNFA
    assert result.accepts(word) is accepted


def test_concatenation_collision_safe_and_union_alphabet() -> None:
    # Both sources use the same state names, yet upstream maps them disjointly.
    left = _exact_symbol_dfa("a", {"a"})
    right = _exact_symbol_dfa("b", {"b"})
    result = left.concatenation(right)
    assert result.states == {0, 1, 2, 3}
    assert result.input_symbols == {"a", "b"}
    assert result.accepts("ab") is True
    assert result.accepts("a") is False
    assert result.accepts("b") is False


def test_concatenation_with_epsilon_language_on_each_side() -> None:
    epsilon = _epsilon_nfa(True, {"a"})
    symbol = _exact_symbol_dfa("a", {"a"})
    for result in (epsilon.concatenation(symbol),
                   symbol.concatenation(epsilon)):
        assert type(result) is ExtendedNFA
        assert result.accepts("a") is True
        assert result.accepts("") is False
        assert result.accepts("aa") is False


def test_concatenation_with_empty_language_is_empty() -> None:
    empty = _epsilon_nfa(False, {"a"})
    symbol = _exact_symbol_dfa("a", {"a"})
    for result in (empty.concatenation(symbol),
                   symbol.concatenation(empty)):
        assert result.is_empty() is True
        assert result.accepts("") is False
        assert result.accepts("a") is False


def test_nfa_concatenation_preserves_existing_epsilon_edges() -> None:
    left = ExtendedNFA(
        states={"l0", "l1", "lf"}, input_symbols={"a", "b"},
        transitions={"l0": {"": {"l1"}}, "l1": {"a": {"lf"}}},
        initial_state="l0", final_states={"lf"},
    )
    right = ExtendedNFA(
        states={"r0", "r1", "rf"}, input_symbols={"a", "b"},
        transitions={"r0": {"b": {"r1"}}, "r1": {"": {"rf"}}},
        initial_state="r0", final_states={"rf"},
    )
    result = left.concatenation(right)
    assert type(result) is ExtendedNFA
    assert result.accepts("ab") is True
    assert result.accepts("a") is False
    assert result.accepts("b") is False


def test_concatenation_is_immutable_and_composable() -> None:
    left = _exact_symbol_dfa("a", {"a"})
    right = _exact_symbol_nfa("a", {"a"})
    before_left = deepcopy(left.input_parameters)
    before_right = deepcopy(right.input_parameters)
    result = left.concatenation(right)
    assert id(result) != id(left) and result is not right
    assert left.input_parameters == before_left
    assert right.input_parameters == before_right
    minimized = result.determinize().minimize()
    assert type(minimized) is ExtendedDFA
    assert minimized.accepts("aa") is True


@pytest.mark.parametrize(
    ("word", "accepted"),
    [("", True), ("ab", True), ("abab", True),
     ("a", False), ("aba", False), ("ba", False)],
)
def test_dfa_kleene_star_exact_language(word: str, accepted: bool) -> None:
    source = ExtendedDFA(
        states={"s", "m", "f"}, input_symbols={"a", "b"},
        transitions={"s": {"a": "m"}, "m": {"b": "f"}, "f": {}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    result = source.kleene_star()
    assert type(result) is ExtendedNFA
    assert result.accepts(word) is accepted


def test_star_of_empty_and_epsilon_languages() -> None:
    for source in (_epsilon_nfa(False, {"a"}),
                   _epsilon_nfa(True, {"a"})):
        result = source.kleene_star()
        assert type(result) is ExtendedNFA
        assert result.accepts("") is True
        assert result.accepts("a") is False
        assert result.accepts("aa") is False
    assert _epsilon_nfa(False, {"a"}).kleene_star().is_empty() is False


def test_star_preserves_existing_epsilon_and_avoids_state_collision() -> None:
    source = ExtendedNFA(
        states={0, 1}, input_symbols={"a"},
        transitions={0: {"": {1}}, 1: {"a": {1}}},
        initial_state=0, final_states={1},
    )
    result = source.kleene_star()
    assert type(result) is ExtendedNFA
    assert result.states == {0, 1, 2}
    assert result.initial_state == 2
    assert 2 in result.final_states
    assert result.transitions[2][""] == {0}
    assert result.accepts("") is True
    assert result.accepts("aaa") is True


def test_star_is_immutable_and_composable() -> None:
    source = _exact_symbol_nfa("a", {"a"})
    before = deepcopy(source.input_parameters)
    result = source.kleene_star()
    assert result is not source
    assert source.input_parameters == before
    without_epsilon = result.remove_epsilon_transitions()
    assert type(without_epsilon) is ExtendedNFA
    for word in ("", "a", "aa", "aaa"):
        assert without_epsilon.accepts(word) is True


def test_mro_and_existing_operations_remain_intact() -> None:
    for cls in (ExtendedDFA, ExtendedNFA):
        assert cls.concatenation is LanguageOperationsMixin.concatenation
        assert cls.kleene_star is LanguageOperationsMixin.kleene_star
        assert cls.__mro__.count(LanguageOperationsMixin) == 1
    assert LanguageOperationsMixin not in ExtendedGNFA.__mro__
    assert not hasattr(ExtendedGNFA, "concatenation")
    assert ExtendedDFA.union is DFASetOperationsMixin.union
    assert ExtendedNFA.concatenate is NFA.concatenate
