"""Thompson construction and public regex compatibility."""

from itertools import product

import pytest
from automata.base.exceptions import InvalidRegexError
from automata.fa.nfa import NFA

from automata_extensions.fa import ExtendedNFA
from automata_extensions.fa.nfa_mixins.thompson import _ThompsonBuilder
from automata_extensions.regex import _ast


def _words(alphabet: str, max_length: int = 4) -> list[str]:
    return ["".join(letters) for size in range(max_length + 1)
            for letters in product(alphabet, repeat=size)]


@pytest.mark.parametrize(
    ("expression", "alphabet"),
    [
        ("", set()), ("()", set()), ("a", {"a", "b"}),
        ("a|b", {"a", "b"}), ("ab", {"a", "b"}),
        ("a*", {"a", "b"}), ("(a|b)*a", {"a", "b"}),
        ("(a|())b", {"a", "b"}),
    ],
)
def test_thompson_language_matches_upstream_oracle(
    expression: str, alphabet: set[str]
) -> None:
    actual = ExtendedNFA.from_regex(expression, input_symbols=alphabet)
    expected = NFA.from_regex(expression, input_symbols=alphabet)
    assert type(actual) is ExtendedNFA
    assert actual.input_symbols == alphabet
    for word in _words("ab"):
        assert actual.accepts_input(word) == expected.accepts_input(word)


def test_source_compatibility_executed_mature_example() -> None:
    nfa = ExtendedNFA.from_regex("(a|b)*a", input_symbols={"a", "b"})
    assert nfa.accepts_input("aba") is True


def test_literal_epsilon_and_internal_empty_fragments() -> None:
    literal = ExtendedNFA.from_regex("a")
    assert len(literal.states) == 2
    assert literal.transitions[literal.initial_state]["a"] == literal.final_states
    assert literal.input_symbols == {"a"}

    epsilon = ExtendedNFA.from_regex("()")
    assert len(epsilon.states) == 2
    assert epsilon.input_symbols == set()
    assert epsilon.transitions[epsilon.initial_state][""] == epsilon.final_states
    assert epsilon.accepts_input("") is True

    builder = _ThompsonBuilder()
    empty = builder.build(_ast.EMPTY)
    assert builder.transitions[empty.start] == {}
    assert builder.transitions[empty.final] == {}
    assert empty.start != empty.final


def test_union_concatenation_and_star_have_thompson_edges() -> None:
    union = ExtendedNFA.from_regex("a|b")
    assert len(union.states) == 6
    assert len(union.transitions[union.initial_state][""]) == 2
    assert union.accepts_input("a") and union.accepts_input("b")

    concat = ExtendedNFA.from_regex("ab")
    assert len(concat.states) == 4
    assert sum("" in paths for paths in concat.transitions.values()) == 1
    assert concat.accepts_input("ab") and not concat.accepts_input("a")

    star = ExtendedNFA.from_regex("a*")
    assert len(star.states) == 4
    assert len(star.transitions[star.initial_state][""]) == 2
    assert star.accepts_input("") and star.accepts_input("aaa")


def test_explicit_alphabet_and_invalid_grammar() -> None:
    nfa = ExtendedNFA.from_regex("a", input_symbols={"a", "b"})
    assert nfa.input_symbols == {"a", "b"}
    assert nfa.accepts_input("b") is False
    for invalid in ("a+", "a?", "[a]", "a|", "(a", "*a"):
        with pytest.raises(InvalidRegexError):
            ExtendedNFA.from_regex(invalid)
    with pytest.raises(InvalidRegexError):
        ExtendedNFA.from_regex("a", input_symbols={"b"})


def test_extended_result_and_fresh_state_graph() -> None:
    first = ExtendedNFA.from_regex("(a|b)*a")
    second = ExtendedNFA.from_regex("(a|b)*a")
    assert first is not second
    assert first.states == second.states
    assert first.transitions == second.transitions
    assert first.determinize().accepts_input("aba") is True
    assert first.states == second.states
