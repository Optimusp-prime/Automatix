"""Professor requirement #49: recursive derivatives of regex syntax trees."""

from dataclasses import FrozenInstanceError
from itertools import product

import pytest
from automata.base.exceptions import InvalidRegexError
from automata.fa.nfa import NFA

from automata_extensions.regex import Regex
from automata_extensions.regex import _ast


@pytest.mark.parametrize(
    ("expression", "symbol", "expected"),
    [
        ("", "a", "∅"),
        ("()", "a", "∅"),
        ("a", "a", "()"),
        ("b", "a", "∅"),
        ("a|b", "a", "()"),
        ("ab", "a", "b"),
        ("a*", "a", "a*"),
        ("(a|b)*", "a", "(a|b)*"),
        ("(a|b)*a", "a", "(a|b)*a|()"),
        ("()a", "a", "()"),
        ("a?", "a", None),
    ],
)
def test_recursive_rules(
    expression: str, symbol: str, expected: str | None,
) -> None:
    if expected is None:
        with pytest.raises(InvalidRegexError):
            Regex(expression)
    else:
        assert str(Regex(expression).derivative(symbol)) == expected


def test_nullable_left_concatenation_contributes_both_branches() -> None:
    assert str(Regex("(a|())b").derivative("a")) == "b"
    assert str(Regex("(a|())b").derivative("b")) == "()"
    assert str(Regex("a*b").derivative("b")) == "()"


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("ab|c", "ab|c"),
        ("a|bc", "a|bc"),
        ("(a|b)*", "(a|b)*"),
        ("a|a", "a"),
        ("a()", "a"),
        ("()a", "a"),
        ("a**", "a*"),
        ("()*", "()"),
        ("", "()"),
    ],
)
def test_precedence_and_minimal_normalization(
    expression: str, expected: str,
) -> None:
    assert str(Regex(expression)) == expected


@pytest.mark.parametrize(
    "expression",
    ["a|", "|a", "a||b", "(a", "a)", "*a", "(a|)", "a+", "a?", "a&b", "a^b", ".", "[ab]", "a{2}", "a\\"],
)
def test_malformed_or_unsupported_syntax(expression: str) -> None:
    with pytest.raises(InvalidRegexError):
        Regex(expression)


def test_explicit_alphabet_is_single_character_and_contains_literals() -> None:
    assert str(Regex("a", input_symbols={"a", "b"}).derivative("b")) == "∅"
    with pytest.raises(InvalidRegexError, match="not in input_symbols"):
        Regex("a", input_symbols={"b"})
    with pytest.raises(InvalidRegexError, match="single characters"):
        Regex("a", input_symbols={"a", "bb"})
    assert str(Regex("", input_symbols=set()).derivative("a")) == "∅"


def test_empty_language_is_an_internal_node_not_an_input_token() -> None:
    result = Regex("a").derivative("b")
    assert isinstance(result._root, _ast.EmptyLanguage)
    # The visible ∅ is still an ordinary literal in constructor input.
    assert str(Regex("∅").derivative("∅")) == "()"
    assert isinstance(Regex("∅").derivative("a")._root, _ast.EmptyLanguage)


def test_derivative_symbol_must_be_one_character() -> None:
    regex = Regex("ab")
    for symbol in ("", "ab"):
        with pytest.raises(ValueError, match="exactly one"):
            regex.derivative(symbol)
    with pytest.raises(TypeError, match="string"):
        regex.derivative(None)  # type: ignore[arg-type]
    assert isinstance(regex.derivative("z")._root, _ast.EmptyLanguage)


def test_immutable_new_values_and_chaining() -> None:
    source = Regex("ab")
    first = source.derivative("a")
    again = source.derivative("a")
    assert first is not source and again is not first
    assert first == again
    assert str(source) == "ab"
    assert str(first) == "b"
    assert str(first.derivative("b")) == "()"
    with pytest.raises(FrozenInstanceError):
        source._root = _ast.EMPTY  # type: ignore[misc]


def test_private_constructor_identities() -> None:
    a = _ast.Literal("a")
    assert _ast.union(_ast.EMPTY, a) == a
    assert _ast.union(a, _ast.EMPTY) == a
    assert _ast.union(a, a) == a
    assert _ast.concatenate(_ast.EPSILON, a) == a
    assert _ast.concatenate(a, _ast.EPSILON) == a
    assert _ast.concatenate(_ast.EMPTY, a) == _ast.EMPTY
    assert _ast.concatenate(a, _ast.EMPTY) == _ast.EMPTY
    assert _ast.star(_ast.EMPTY) == _ast.EPSILON
    assert _ast.star(_ast.EPSILON) == _ast.EPSILON
    assert _ast.star(_ast.star(a)) == _ast.star(a)
    assert hash(_ast.union(a, _ast.Literal("b")))


@pytest.mark.parametrize("expression", ["a", "a|b", "ab", "a*", "(a|b)*", "(a|b)*a", "a*b", "(a|())b"])
def test_derivative_language_matches_independent_upstream_nfa(expression: str) -> None:
    original = Regex(expression, input_symbols={"a", "b"})
    derived = original.derivative("a")
    if isinstance(derived._root, _ast.EmptyLanguage):
        # Upstream has no distinct textual empty-language expression.
        assert all(
            not NFA.from_regex(expression, input_symbols={"a", "b"}).accepts_input("a" + word)
            for length in range(4)
            for letters in product("ab", repeat=length)
            for word in ["".join(letters)]
        )
        return
    source_nfa = NFA.from_regex(expression, input_symbols={"a", "b"})
    derivative_nfa = NFA.from_regex(str(derived), input_symbols={"a", "b"})
    for length in range(4):
        for letters in product("ab", repeat=length):
            word = "".join(letters)
            assert derivative_nfa.accepts_input(word) == source_nfa.accepts_input("a" + word)
