"""Professor requirement #58: rational systems and automaton equations."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
from itertools import product
import re
from typing import Hashable

import pytest

from automata_extensions.equations import SystemOfEquations, solve_arden
from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.dfa_mixins.equation_system import DFAEquationSystemMixin
from automata_extensions.fa.nfa_mixins.equation_system import NFAEquationSystemMixin
from automata_extensions.regex import Regex, _ast


def _empty() -> Regex:
    return Regex("a").derivative("b")


def _accepts(expression: Regex, word: str, alphabet: set[str]) -> bool:
    if isinstance(expression._root, _ast.EmptyLanguage):
        return False
    return ExtendedNFA.from_regex(
        str(expression), input_symbols=alphabet
    ).accepts(word)


def _words(alphabet: str, maximum_length: int) -> list[str]:
    return [
        "".join(letters)
        for length in range(maximum_length + 1)
        for letters in product(alphabet, repeat=length)
    ]


def test_one_variable_matches_single_equation_arden() -> None:
    system = SystemOfEquations(
        ("X",), {"X": {"X": Regex("a")}}, {"X": Regex("b")}
    )
    solved = system.solve()
    assert tuple(solved) == ("X",)
    assert type(solved["X"]) is Regex
    assert str(solved["X"]) == str(solve_arden(Regex("a"), Regex("b"))) == "a*b"


def test_two_independent_equations_and_empty_constants() -> None:
    system = SystemOfEquations(
        ("X", "Y"), {"X": {"X": Regex("a")}},
        {"X": Regex(""), "Y": _empty()},
    )
    solved = system.solve()
    assert tuple(solved) == ("X", "Y")
    assert str(solved["X"]) == "a*"
    assert isinstance(solved["Y"]._root, _ast.EmptyLanguage)


def test_dependent_two_variable_system() -> None:
    # X = aX ∪ bY, Y = cY ∪ d.
    system = SystemOfEquations(
        ("X", "Y"),
        {"X": {"X": Regex("a"), "Y": Regex("b")},
         "Y": {"Y": Regex("c")}},
        {"X": _empty(), "Y": Regex("d")},
    )
    solved = system.solve()
    for word in _words("abcd", 4):
        assert _accepts(solved["X"], word, set("abcd")) is bool(
            re.fullmatch("a*bc*d", word)
        )
        assert _accepts(solved["Y"], word, set("abcd")) is bool(
            re.fullmatch("c*d", word)
        )


def test_mutual_recursion_and_empty_coefficient() -> None:
    # X = aY ∪ ε, Y = bX; hence X = (ab)* and Y = b(ab)*.
    system = SystemOfEquations(
        ("X", "Y"),
        {"X": {"X": _empty(), "Y": Regex("a")},
         "Y": {"X": Regex("b")}},
        {"X": Regex(""), "Y": _empty()},
    )
    solved = system.solve()
    for word in _words("ab", 5):
        assert _accepts(solved["X"], word, {"a", "b"}) is (word in ("", "ab", "abab"))
        assert _accepts(solved["Y"], word, {"a", "b"}) is (word in ("b", "bab", "babab"))


@pytest.mark.parametrize(
    ("variables", "coefficients", "constants", "error"),
    [
        (("X", "X"), {}, {"X": Regex("a")}, ValueError),
        (("X",), {}, {}, ValueError),
        (("X",), {}, {"X": Regex("a"), "Y": Regex("b")}, ValueError),
        (("X",), {"Y": {}}, {"X": Regex("a")}, ValueError),
        (("X",), {"X": {"Y": Regex("a")}}, {"X": Regex("b")}, ValueError),
        (("X",), {"X": {"X": "a"}}, {"X": Regex("b")}, TypeError),
        (("X",), {}, {"X": "b"}, TypeError),
        ((["X"],), {}, {}, TypeError),
    ],
)
def test_constructor_validation(
    variables: tuple[Hashable, ...],
    coefficients: dict[str, dict[str, Regex]],
    constants: dict[str, Regex],
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        SystemOfEquations[str](
            variables,  # type: ignore[arg-type]
            coefficients, constants,
        )


def test_caller_mappings_are_copied_and_results_are_read_only() -> None:
    row = {"X": Regex("a")}
    coefficients = {"X": row}
    constants = {"X": Regex("b")}
    system = SystemOfEquations(("X",), coefficients, constants)
    row.clear()
    coefficients.clear()
    constants.clear()
    assert str(system.coefficients["X"]["X"]) == "a"
    assert str(system.constants["X"]) == "b"
    with pytest.raises(TypeError):
        system.coefficients["X"]["X"] = Regex("c")  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        system.variables = ()  # type: ignore[misc]
    first = system.solve()
    second = system.solve()
    assert dict(first) == dict(second)
    assert first["X"] is not second["X"]
    with pytest.raises(TypeError):
        first["X"] = Regex("c")  # type: ignore[index]


def test_alphabet_metadata_merges_all_terms() -> None:
    system = SystemOfEquations(
        ("X", "Y"), {"X": {"Y": Regex("a", input_symbols={"a", "x"})}},
        {"X": _empty(), "Y": Regex("b", input_symbols={"b", "y"})},
    )
    solved = system.solve()
    assert solved["X"]._symbols == solved["Y"]._symbols == frozenset(
        {"a", "b", "x", "y"}
    )


def test_nullable_diagonal_at_input_is_rejected() -> None:
    system = SystemOfEquations(
        ("X",), {"X": {"X": Regex("a|()")}}, {"X": Regex("b")}
    )
    with pytest.raises(ValueError, match="variable 'X'"):
        system.solve()


def test_nullable_diagonal_created_by_substitution_is_rejected() -> None:
    # X = Y, Y = X ∪ b: eliminating X creates an epsilon self-coefficient.
    system = SystemOfEquations(
        ("X", "Y"),
        {"X": {"Y": Regex("")}, "Y": {"X": Regex("")}},
        {"X": _empty(), "Y": Regex("b")},
    )
    with pytest.raises(ValueError, match="variable 'Y'"):
        system.solve()


def test_epsilon_off_diagonal_without_epsilon_cycle_is_valid() -> None:
    system: SystemOfEquations[Hashable] = SystemOfEquations(
        (None, 1), {None: {1: Regex("")}},
        {None: _empty(), 1: Regex("a")},
    )
    solved = system.solve()
    assert tuple(solved) == (None, 1)
    assert str(solved[None]) == str(solved[1]) == "a"


def test_empty_system_is_an_empty_mapping() -> None:
    system = SystemOfEquations[str]((), {}, {})
    assert dict(system.solve()) == {}


def test_dfa_system_contains_all_states_and_right_languages() -> None:
    dfa = ExtendedDFA(
        states={"q0", "q1", "q2", "unused"},
        input_symbols={"a", "b"},
        transitions={"q0": {"a": "q1", "b": "q0"},
                     "q1": {"a": "q2"}, "q2": {}, "unused": {}},
        initial_state="q0", final_states={"q1", "q2", "unused"},
        allow_partial=True,
    )
    before = deepcopy(dfa.input_parameters)
    system = dfa.to_equation_system()
    assert set(system.variables) == dfa.states
    assert "unused" in system.variables
    assert isinstance(system.constants["q0"]._root, _ast.EmptyLanguage)
    assert isinstance(system.constants["q1"]._root, _ast.Epsilon)
    assert str(system.coefficients["q0"]["q1"]) == "a"
    assert "b" not in system.coefficients["q1"]
    solved = system.solve()
    assert set(solved) == dfa.states
    for state in dfa.states:
        right = ExtendedDFA(
            states=dfa.states, input_symbols=dfa.input_symbols,
            transitions=dfa.transitions, initial_state=state,
            final_states=dfa.final_states, allow_partial=True,
        )
        for word in _words("ab", 3):
            assert _accepts(solved[state], word, {"a", "b"}) is right.accepts(word)
    assert dfa.input_parameters == before


@pytest.mark.parametrize("final", [False, True])
def test_one_state_dfa_with_and_without_final(final: bool) -> None:
    dfa = ExtendedDFA(
        states={None}, input_symbols={"a"}, transitions={None: {"a": None}},
        initial_state=None, final_states={None} if final else set(),
    )
    solved = dfa.to_equation_system().solve()
    assert None in solved
    for word in ("", "a", "aa"):
        assert _accepts(solved[None], word, {"a"}) is final


def test_dfa_parallel_symbols_union_and_heterogeneous_states() -> None:
    dfa = ExtendedDFA(
        states={None, 1, "other"}, input_symbols={"a", "b"},
        transitions={None: {"a": 1, "b": 1}, 1: {}, "other": {}},
        initial_state=None, final_states={1}, allow_partial=True,
    )
    system = dfa.to_equation_system()
    assert str(system.coefficients[None][1]) == "a|b"
    for word in ("", "a", "b", "aa"):
        # Upstream's known partial-DFA/None sentinel bug (#55) makes
        # accepts() unsuitable as an oracle for this particular fixture.
        assert _accepts(system.solve()[None], word, {"a", "b"}) is (
            word in {"a", "b"}
        )


def test_nfa_nondeterminism_and_state_right_languages() -> None:
    nfa = ExtendedNFA(
        states={"p", "q", "r", "f"}, input_symbols={"a", "b"},
        transitions={"p": {"a": {"q", "r"}}, "q": {"b": {"f"}},
                     "r": {"a": {"f"}}, "f": {}},
        initial_state="p", final_states={"f"},
    )
    before = deepcopy(nfa.input_parameters)
    system = nfa.to_equation_system()
    assert set(system.variables) == nfa.states
    assert str(system.coefficients["p"]["q"]) == "a"
    assert str(system.coefficients["p"]["r"]) == "a"
    solved = system.solve()
    for state in nfa.states:
        right = ExtendedNFA(
            states=nfa.states, input_symbols=nfa.input_symbols,
            transitions=nfa.transitions, initial_state=state,
            final_states=nfa.final_states,
        )
        for word in _words("ab", 3):
            assert _accepts(solved[state], word, {"a", "b"}) is right.accepts(word)
    assert nfa.input_parameters == before


def test_epsilon_cycle_nfa_is_normalized_without_state_renaming() -> None:
    nfa = ExtendedNFA(
        states={"p", "q", "f"}, input_symbols={"a"},
        transitions={"p": {"": {"q"}},
                     "q": {"": {"p"}, "a": {"f"}}, "f": {}},
        initial_state="p", final_states={"f"},
    )
    before = deepcopy(nfa.input_parameters)
    system = nfa.to_equation_system()
    assert set(system.variables) == nfa.states
    assert all(
        not _ast.nullable(coefficient._root)
        for row in system.coefficients.values()
        for coefficient in row.values()
    )
    solved = system.solve()
    for word in ("", "a", "aa"):
        assert _accepts(solved["p"], word, {"a"}) is nfa.accepts(word)
    assert nfa.input_parameters == before


def test_nfa_epsilon_reaches_final_and_preserves_empty_word() -> None:
    nfa = ExtendedNFA(
        states={"p", "f"}, input_symbols={"a"},
        transitions={"p": {"": {"f"}}, "f": {}},
        initial_state="p", final_states={"f"},
    )
    system = nfa.to_equation_system()
    assert isinstance(system.constants["p"]._root, _ast.Epsilon)
    assert _accepts(system.solve()["p"], "", {"a"})


def test_mro_and_public_scopes() -> None:
    assert ExtendedDFA.to_equation_system is DFAEquationSystemMixin.to_equation_system
    assert ExtendedNFA.to_equation_system is NFAEquationSystemMixin.to_equation_system
    assert not hasattr(ExtendedGNFA, "to_equation_system")
