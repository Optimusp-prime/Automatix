"""Language inclusion tests via complement, lazy product and emptiness."""

from copy import deepcopy

import pytest
from automata.base.exceptions import SymbolMismatchError

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.dfa_mixins.inclusion import InclusionMixin


def _three_state_cycle() -> ExtendedDFA:
    return ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a"},
        transitions={
            "0": {"a": "1"}, "1": {"a": "2"}, "2": {"a": "0"},
        },
        initial_state="0", final_states={"2"},
    )


def _all_words() -> ExtendedDFA:
    return ExtendedDFA(
        states={"all"}, input_symbols={"a"},
        transitions={"all": {"a": "all"}},
        initial_state="all", final_states={"all"},
    )


def _nonempty_words() -> ExtendedDFA:
    return ExtendedDFA(
        states={"initial", "seen"}, input_symbols={"a"},
        transitions={"initial": {"a": "seen"}, "seen": {"a": "seen"}},
        initial_state="initial", final_states={"seen"},
    )


def test_source_compatibility_inclusion_is_reflexive() -> None:
    """Directly preserve the mature d.is_included_in(d) example."""
    d = _three_state_cycle()
    assert d.is_included_in(d) is True
    assert type(d.is_included_in(d)) is bool


def test_strict_inclusion_and_reverse_counterexample() -> None:
    smaller = _nonempty_words()
    larger = _all_words()
    assert smaller.is_included_in(larger) is True
    assert larger.is_included_in(smaller) is False
    assert larger.accepts("") is True
    assert smaller.accepts("") is False


def test_empty_language_is_included_in_every_language() -> None:
    empty = ExtendedDFA(
        states={"empty"}, input_symbols={"a"},
        transitions={"empty": {"a": "empty"}},
        initial_state="empty", final_states=set(),
    )
    assert empty.is_included_in(_all_words()) is True
    assert _nonempty_words().is_included_in(empty) is False


def test_counterexample_can_require_several_symbols() -> None:
    left = ExtendedDFA(
        states={"q0", "q1", "q2", "q3"}, input_symbols={"a"},
        transitions={
            "q0": {"a": "q1"}, "q1": {"a": "q2"},
            "q2": {"a": "q3"}, "q3": {"a": "q3"},
        },
        initial_state="q0", final_states={"q3"},
    )
    right = ExtendedDFA(
        states={"p0", "p1", "p2", "p3"}, input_symbols={"a"},
        transitions={
            "p0": {"a": "p1"}, "p1": {"a": "p2"},
            "p2": {"a": "p3"}, "p3": {"a": "p3"},
        },
        initial_state="p0", final_states={"p0", "p1", "p2"},
    )
    for word in ("", "a", "aa"):
        assert not (left.accepts(word) and not right.accepts(word))
    assert left.accepts("aaa") is True
    assert right.accepts("aaa") is False
    assert left.is_included_in(right) is False


def test_partial_right_missing_transition_decides_inclusion() -> None:
    left = ExtendedDFA(
        states={"l0", "lf"}, input_symbols={"a", "b"},
        transitions={
            "l0": {"a": "l0", "b": "lf"},
            "lf": {"a": "lf", "b": "lf"},
        },
        initial_state="l0", final_states={"lf"},
    )
    right = ExtendedDFA(
        states={"r"}, input_symbols={"a", "b"},
        transitions={"r": {"a": "r"}},
        initial_state="r", final_states={"r"}, allow_partial=True,
    )
    assert left.accepts("b") is True
    assert right.accepts("b") is False
    assert left.is_included_in(right) is False


def test_partial_left_missing_transition_does_not_create_witness() -> None:
    left = ExtendedDFA(
        states={"l"}, input_symbols={"a", "b"},
        transitions={"l": {"a": "l"}},
        initial_state="l", final_states={"l"}, allow_partial=True,
    )
    right = ExtendedDFA(
        states={"r"}, input_symbols={"a", "b"},
        transitions={"r": {"a": "r", "b": "r"}},
        initial_state="r", final_states={"r"},
    )
    assert left.is_included_in(right) is True


def test_different_alphabets_raise_product_symbol_mismatch() -> None:
    other = ExtendedDFA(
        states={"p"}, input_symbols={"b"},
        transitions={"p": {"b": "p"}},
        initial_state="p", final_states={"p"},
    )
    with pytest.raises(SymbolMismatchError):
        _all_words().is_included_in(other)


def test_none_and_heterogeneous_states() -> None:
    left = ExtendedDFA(
        states={None, 1}, input_symbols={"a"},
        transitions={None: {"a": 1}, 1: {"a": 1}},
        initial_state=None, final_states={1},
    )
    right = ExtendedDFA(
        states={"start", 2}, input_symbols={"a"},
        transitions={"start": {"a": 2}, 2: {"a": 2}},
        initial_state="start", final_states={"start", 2},
    )
    assert left.is_included_in(right) is True
    assert right.is_included_in(left) is False


def test_operands_are_immutable_and_composition_matches_formula() -> None:
    left, right = _nonempty_words(), _all_words()
    before_left = (deepcopy(left.states), deepcopy(left.transitions),
                   deepcopy(left.final_states), left.initial_state)
    before_right = (deepcopy(right.states), deepcopy(right.transitions),
                    deepcopy(right.final_states), right.initial_state)
    complement = right.complement()
    witness = left.product(
        complement,
        is_final=lambda l, r: l in left.final_states
        and r in complement.final_states,
    )
    assert left.is_included_in(right) is witness.is_empty()
    assert (left.states, left.transitions, left.final_states,
            left.initial_state) == before_left
    assert (right.states, right.transitions, right.final_states,
            right.initial_state) == before_right


def test_inclusion_mro_is_dfa_only() -> None:
    assert ExtendedDFA.is_included_in is InclusionMixin.is_included_in
    assert InclusionMixin in ExtendedDFA.__mro__
    for cls in (ExtendedNFA, ExtendedGNFA):
        assert InclusionMixin not in cls.__mro__


def test_source_compatibility_equivalence_is_reflexive() -> None:
    """Preserve the mature (d.is_included_in(d), d.is_equivalent(d)) example."""
    d = _three_state_cycle()
    assert (d.is_included_in(d), d.is_equivalent(d)) == (True, True)
    assert type(d.is_equivalent(d)) is bool


def test_different_structures_can_accept_the_same_language() -> None:
    left = _nonempty_words()
    right = ExtendedDFA(
        states={"x", "y", "unreachable"}, input_symbols={"a"},
        transitions={
            "x": {"a": "y"}, "y": {"a": "y"},
            "unreachable": {"a": "unreachable"},
        },
        initial_state="x", final_states={"y"},
    )
    assert left.states != right.states
    assert left.is_equivalent(right) is True
    assert right.is_equivalent(left) is True


def test_strict_inclusion_does_not_imply_equivalence() -> None:
    smaller, larger = _nonempty_words(), _all_words()
    assert smaller.is_included_in(larger) is True
    assert larger.is_included_in(smaller) is False
    assert smaller.is_equivalent(larger) is False
    assert larger.is_equivalent(smaller) is False


def test_empty_languages_are_equivalent_but_empty_and_nonempty_are_not() -> None:
    first = ExtendedDFA(
        states={"first"}, input_symbols={"a"},
        transitions={"first": {"a": "first"}},
        initial_state="first", final_states=set(),
    )
    second = ExtendedDFA(
        states={0, 1}, input_symbols={"a"},
        transitions={0: {"a": 1}, 1: {"a": 1}},
        initial_state=0, final_states=set(),
    )
    assert first.is_equivalent(second) is True
    assert first.is_equivalent(_nonempty_words()) is False


def test_partial_dfas_with_renamed_states_are_equivalent() -> None:
    left = ExtendedDFA(
        states={"start", "final"}, input_symbols={"a", "b"},
        transitions={"start": {"a": "final"}, "final": {"a": "final"}},
        initial_state="start", final_states={"final"}, allow_partial=True,
    )
    right = ExtendedDFA(
        states={0, 1}, input_symbols={"a", "b"},
        transitions={0: {"a": 1}, 1: {"a": 1}},
        initial_state=0, final_states={1}, allow_partial=True,
    )
    assert left.is_equivalent(right) is True
    assert right.is_equivalent(left) is True


def test_equivalence_propagates_alphabet_mismatch() -> None:
    other = ExtendedDFA(
        states={"p"}, input_symbols={"b"},
        transitions={"p": {"b": "p"}},
        initial_state="p", final_states={"p"},
    )
    with pytest.raises(SymbolMismatchError):
        _all_words().is_equivalent(other)


def test_equivalence_handles_none_and_heterogeneous_states() -> None:
    left = ExtendedDFA(
        states={None, 1}, input_symbols={"a"},
        transitions={None: {"a": 1}, 1: {"a": 1}},
        initial_state=None, final_states={1},
    )
    right = ExtendedDFA(
        states={"start", 2}, input_symbols={"a"},
        transitions={"start": {"a": 2}, 2: {"a": 2}},
        initial_state="start", final_states={2},
    )
    assert left.is_equivalent(right) is True


def test_equivalence_keeps_both_operands_unchanged() -> None:
    left, right = _nonempty_words(), _all_words()
    before_left = deepcopy(left.input_parameters)
    before_right = deepcopy(right.input_parameters)
    assert left.is_equivalent(right) is False
    assert left.input_parameters == before_left
    assert right.input_parameters == before_right


def test_equivalence_mro_is_dfa_only() -> None:
    assert ExtendedDFA.is_equivalent is InclusionMixin.is_equivalent
    for cls in (ExtendedNFA, ExtendedGNFA):
        assert InclusionMixin not in cls.__mro__
