"""Professor requirement #57: one Arden rational-language equation."""

from dataclasses import FrozenInstanceError

import pytest

from automata_extensions.equations import solve_arden
from automata_extensions.fa import ExtendedNFA
from automata_extensions.regex import Regex, _ast


def test_classical_arden_equation_and_language() -> None:
    # X = aX ∪ b has the unique solution a*b.
    result = solve_arden(Regex("a"), Regex("b"))
    assert type(result) is Regex
    assert str(result) == "a*b"
    automaton = ExtendedNFA.from_regex(str(result), input_symbols={"a", "b"})
    for word in ("b", "ab", "aab", "aaab"):
        assert automaton.accepts(word)
    for word in ("", "a", "ba"):
        assert not automaton.accepts(word)


@pytest.mark.parametrize(
    ("coefficient", "constant", "expected"),
    [
        ("a", "", "a*"),
        ("ab", "c", "(ab)*c"),
        ("a|b", "c", "(a|b)*c"),
    ],
)
def test_nonnullable_coefficients(
    coefficient: str, constant: str, expected: str
) -> None:
    assert str(solve_arden(Regex(coefficient), Regex(constant))) == expected


def test_empty_language_coefficient_and_constant() -> None:
    empty = Regex("a").derivative("b")
    assert isinstance(empty._root, _ast.EmptyLanguage)
    assert str(solve_arden(empty, Regex("b"))) == "b"
    result = solve_arden(Regex("a"), empty)
    assert isinstance(result._root, _ast.EmptyLanguage)
    assert str(result) == "∅"  # Diagnostic rendering, not public parser syntax.


@pytest.mark.parametrize("coefficient", ["", "()", "a|()", "(a|())b*"])
def test_nullable_coefficient_is_rejected(coefficient: str) -> None:
    with pytest.raises(ValueError, match="epsilon outside"):
        solve_arden(Regex(coefficient), Regex("b"))


def test_operands_are_immutable_and_result_is_fresh() -> None:
    coefficient = Regex("a")
    constant = Regex("b")
    first = solve_arden(coefficient, constant)
    second = solve_arden(coefficient, constant)
    assert first is not coefficient and first is not constant
    assert first is not second and first == second
    assert str(coefficient) == "a" and str(constant) == "b"
    with pytest.raises(FrozenInstanceError):
        first._root = _ast.EMPTY  # type: ignore[misc]


def test_merged_explicit_alphabet_preserves_unused_symbols() -> None:
    coefficient = Regex("a", input_symbols={"a", "x"})
    constant = Regex("b", input_symbols={"b", "y"})
    result = solve_arden(coefficient, constant)
    assert result._symbols == frozenset({"a", "b", "x", "y"})
    assert coefficient._symbols == frozenset({"a", "x"})
    assert constant._symbols == frozenset({"b", "y"})


def test_empty_coefficient_still_returns_fresh_regex() -> None:
    coefficient = Regex("a").derivative("b")
    constant = Regex("b")
    result = solve_arden(coefficient, constant)
    assert result._root == constant._root
    assert result._symbols == frozenset({"a", "b"})
    assert result is not constant


def test_non_regex_operands_rejected() -> None:
    with pytest.raises(TypeError, match="Regex values"):
        solve_arden("a", Regex("b"))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Regex values"):
        solve_arden(Regex("a"), "b")  # type: ignore[arg-type]
