"""Language-level syntactic monoid and transformation-closure regressions."""

from copy import deepcopy

import pytest

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.dfa_mixins.syntactic_monoid import _append_letter
from tests.fa.test_residual import _single_a
from tests.fa.test_state_elimination import _mature_dfa


def test_mature_source_compatibility_exact_three_transformations() -> None:
    d = _mature_dfa()
    assert sorted(map(str, d.residual_automaton().states)) == ["q0", "q1", "q2"]
    result = d.syntactic_monoid()
    assert len(result) == 3  # Executed mature reference example.
    assert result == frozenset({(0, 1, 2), (1, 2, 0), (2, 0, 1)})


def test_representation_identity_generators_and_right_closure() -> None:
    source = _single_a()
    canonical = source.residual_automaton()
    result = source.syntactic_monoid()
    assert type(result) is frozenset
    assert all(type(action) is tuple for action in result)
    assert all(len(action) == len(canonical.states) for action in result)
    assert all(all(type(index) is int for index in action) for action in result)
    assert tuple(range(len(canonical.states))) in result

    names = tuple(f"q{index}" for index in range(len(canonical.states)))
    indices = {name: index for index, name in enumerate(names)}
    for symbol in canonical.input_symbols:
        letter = tuple(indices[canonical.transitions[name][symbol]] for name in names)
        assert letter in result
        assert all(_append_letter(action, letter) in result for action in result)


def test_noncommuting_letters_fix_composition_direction() -> None:
    source = ExtendedDFA(
        states={0, 1, 2}, input_symbols={"a", "b"},
        transitions={
            0: {"a": 1, "b": 0},
            1: {"a": 2, "b": 0},
            2: {"a": 0, "b": 0},
        },
        initial_state=0, final_states={0},
    )
    canonical = source.residual_automaton()
    assert canonical.transitions == {
        "q0": {"a": "q1", "b": "q0"},
        "q1": {"a": "q2", "b": "q0"},
        "q2": {"a": "q0", "b": "q0"},
    }
    action_a = (1, 2, 0)
    action_b = (0, 0, 0)
    action_ab = _append_letter(action_a, action_b)
    action_ba = _append_letter(action_b, action_a)
    assert action_ab == (0, 0, 0)
    assert action_ba == (1, 1, 1)
    assert action_ab != action_ba
    assert {action_a, action_b, action_ab, action_ba} <= source.syntactic_monoid()


@pytest.mark.parametrize("final", [False, True])
def test_one_state_empty_or_universal_language(final: bool) -> None:
    source = ExtendedDFA(
        states={None}, input_symbols={"a", "b"},
        transitions={None: {"a": None, "b": None}},
        initial_state=None, final_states={None} if final else set(),
    )
    assert source.syntactic_monoid() == frozenset({(0,)})


def test_empty_alphabet_has_only_identity() -> None:
    source = ExtendedDFA(
        states={"s"}, input_symbols=set(), transitions={"s": {}},
        initial_state="s", final_states={"s"},
    )
    assert source.syntactic_monoid() == frozenset({(0,)})


def test_epsilon_only_language_has_identity_and_sink_action() -> None:
    source = ExtendedDFA(
        states={"s"}, input_symbols={"a", "b"}, transitions={"s": {}},
        initial_state="s", final_states={"s"}, allow_partial=True,
    )
    assert source.syntactic_monoid() == frozenset({(0, 1), (1, 1)})


def test_partial_dfa_uses_total_empty_residual() -> None:
    source = _single_a()
    canonical = source.residual_automaton()
    assert canonical.is_complete()
    result = source.syntactic_monoid()
    assert result == frozenset({(0, 1, 2), (1, 2, 2), (2, 2, 2)})


def test_partial_empty_language_normalizes_to_one_state() -> None:
    source = ExtendedDFA(
        states={"s"}, input_symbols={"a"}, transitions={"s": {}},
        initial_state="s", final_states=set(), allow_partial=True,
    )
    assert source.syntactic_monoid() == frozenset({(0,)})


def test_inaccessible_and_equivalent_states_do_not_enlarge_language_monoid() -> None:
    minimal = ExtendedDFA(
        states={"only"}, input_symbols={"a"},
        transitions={"only": {"a": "only"}},
        initial_state="only", final_states={"only"},
    )
    inaccessible = ExtendedDFA(
        states={"start", "x", "y"}, input_symbols={"a"},
        transitions={
            "start": {"a": "start"}, "x": {"a": "y"}, "y": {"a": "y"},
        },
        initial_state="start", final_states={"start", "x", "y"},
    )
    duplicate = ExtendedDFA(
        states={"p", "q"}, input_symbols={"a"},
        transitions={"p": {"a": "q"}, "q": {"a": "p"}},
        initial_state="p", final_states={"p", "q"},
    )
    assert minimal.syntactic_monoid() == inaccessible.syntactic_monoid()
    assert minimal.syntactic_monoid() == duplicate.syntactic_monoid()
    assert len(duplicate.residual_automaton().states) == 1


def test_complete_and_partial_presentations_of_same_language_agree() -> None:
    partial = _single_a()
    complete = partial.complete()
    assert partial.is_equivalent(complete)
    assert partial.syntactic_monoid() == complete.syntactic_monoid()


def test_numeric_q_indices_beyond_q9() -> None:
    states = set(range(11))
    source = ExtendedDFA(
        states=states, input_symbols={"a"},
        transitions={state: {"a": (state + 1) % 11} for state in states},
        initial_state=0, final_states={0},
    )
    result = source.syntactic_monoid()
    assert len(result) == 11
    assert tuple(range(11)) in result
    assert tuple((index + 1) % 11 for index in range(11)) in result


def test_repeated_calls_and_source_immutability() -> None:
    source = _single_a()
    before = deepcopy(source.input_parameters), source.allow_partial
    first = source.syntactic_monoid()
    assert first == source.syntactic_monoid()
    assert (source.input_parameters, source.allow_partial) == before
    with pytest.raises(AttributeError):
        first.add((0,))  # type: ignore[attr-defined]


def test_dfa_only_public_scope() -> None:
    assert ExtendedDFA.syntactic_monoid.__qualname__.startswith("SyntacticMonoidMixin.")
    assert not hasattr(ExtendedNFA, "syntactic_monoid")
    assert not hasattr(ExtendedGNFA, "syntactic_monoid")
