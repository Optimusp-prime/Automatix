"""Bounded optimized regex conversions from DFA."""

from copy import deepcopy
from itertools import product

import pytest

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from tests.fa.test_state_elimination import _mature_dfa


def _check_language(d: ExtendedDFA, expression: str | None) -> None:
    words = (
        "".join(letters)
        for length in range(4)
        for letters in product(sorted(d.input_symbols), repeat=length)
    )
    if expression is None:
        assert d.is_empty()
        return
    oracle = ExtendedNFA.from_regex(expression, input_symbols=d.input_symbols)
    assert all(oracle.accepts(word) == d.accepts(word) for word in words)


def test_both_exact_mature_outputs_and_original_conversions() -> None:
    d = _mature_dfa()
    before = deepcopy(d.input_parameters)
    assert d.to_regex_optimum() == "(b|ab*ab*a)*"
    assert d.to_regex_arden_optimum() == "(ab*ab*a|b)*"
    assert d.to_regex() == "(b*|b*ab*a((b|ab*ab*a))*ab*)"
    assert d.to_regex_arden() == "b*(ab*a((ab*ab*a|b))*ab*|())"
    _check_language(d, d.to_regex_optimum())
    _check_language(d, d.to_regex_arden_optimum())
    assert d.input_parameters == before


@pytest.mark.parametrize(
    ("final", "loop", "expected"),
    [(False, False, None), (True, False, ""), (True, True, "a*")],
)
def test_one_state_boundaries(
    final: bool, loop: bool, expected: str | None,
) -> None:
    d = ExtendedDFA(
        states={"q"}, input_symbols={"a"},
        transitions={"q": {"a": "q"} if loop else {}},
        initial_state="q", final_states={"q"} if final else set(),
        allow_partial=not loop,
    )
    for convert in (d.to_regex_optimum, d.to_regex_arden_optimum):
        assert convert() == expected
        _check_language(d, convert())


def test_partial_dfa_and_heterogeneous_states() -> None:
    d = ExtendedDFA(
        states={0, 1, None}, input_symbols={"a", "b"},
        transitions={0: {"a": 1}, 1: {}, None: {}},
        initial_state=0, final_states={1}, allow_partial=True,
    )
    before = deepcopy(d.input_parameters)
    for convert in (d.to_regex_optimum, d.to_regex_arden_optimum):
        expression = convert()
        _check_language(d, expression)
        assert expression == convert()
    assert d.input_parameters == before


def test_scope_is_dfa_only() -> None:
    for cls in (ExtendedNFA, ExtendedGNFA):
        assert not hasattr(cls, "to_regex_optimum")
        assert not hasattr(cls, "to_regex_arden_optimum")
