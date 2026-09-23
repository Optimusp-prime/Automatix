"""Lazy reachable-pair construction for DFA synchronized products."""

from copy import deepcopy
from collections.abc import Mapping
from typing import cast

import pytest
from automata.base.exceptions import SymbolMismatchError
from automata.fa.dfa import DFA
from automata.fa.fa import FAStateT

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.dfa_mixins.product import ProductMixin


def _pair_transitions(
    dfa: ExtendedDFA,
) -> Mapping[FAStateT, Mapping[str, FAStateT]]:
    """Widen upstream's string-key annotation for generic tuple states."""
    return cast(Mapping[FAStateT, Mapping[str, FAStateT]], dfa.transitions)


def _three_state_cycle() -> ExtendedDFA:
    return ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a"},
        transitions={
            "0": {"a": "1"}, "1": {"a": "2"}, "2": {"a": "0"},
        },
        initial_state="0", final_states={"2"},
    )


def _branching_operands() -> tuple[ExtendedDFA, ExtendedDFA]:
    left = ExtendedDFA(
        states={"q0", "q1"}, input_symbols={"a", "b"},
        transitions={
            "q0": {"a": "q1", "b": "q0"},
            "q1": {"a": "q1", "b": "q0"},
        },
        initial_state="q0", final_states={"q1"},
    )
    right = ExtendedDFA(
        states={"p0", "p1"}, input_symbols={"a", "b"},
        transitions={
            "p0": {"a": "p0", "b": "p1"},
            "p1": {"a": "p1", "b": "p1"},
        },
        initial_state="p0", final_states={"p1"},
    )
    return left, right


def test_source_compatibility_self_product_has_three_diagonal_pairs() -> None:
    """Reproduce the mature product(d, is_final=...) example."""
    d = _three_state_cycle()
    result = d.product(d, is_final=lambda s1, s2: s1 == s2)
    assert sorted(result.states) == [("0", "0"), ("1", "1"), ("2", "2")]
    assert result.final_states == result.states
    assert result.initial_state == ("0", "0")
    assert len(result.states) == 3 < len(d.states) * len(d.states)


def test_synchronized_transitions_and_custom_final_predicate() -> None:
    left, right = _branching_operands()
    result = left.product(
        right, is_final=lambda q, p: q == "q1" and p == "p1"
    )
    assert type(result) is ExtendedDFA
    assert result.initial_state == ("q0", "p0")
    assert result.states == {
        ("q0", "p0"), ("q1", "p0"),
        ("q0", "p1"), ("q1", "p1"),
    }
    assert all(isinstance(pair, tuple) and len(pair) == 2
               for pair in result.states)
    assert _pair_transitions(result)[("q0", "p0")] == {
        "a": ("q1", "p0"), "b": ("q0", "p1"),
    }
    assert _pair_transitions(result)[("q1", "p1")] == {
        "a": ("q1", "p1"), "b": ("q0", "p1"),
    }
    assert result.final_states == {("q1", "p1")}
    assert result.is_complete() is True


@pytest.mark.parametrize("decision", [False, True])
def test_constant_final_predicate_applies_to_every_reachable_pair(
    decision: bool,
) -> None:
    d = _three_state_cycle()
    result = d.product(d, is_final=lambda _a, _b: decision)
    assert result.final_states == (result.states if decision else frozenset())


def test_lazy_product_omits_unreachable_cross_pairs() -> None:
    left = ExtendedDFA(
        states={"a", "b", "dead"}, input_symbols={"x"},
        transitions={
            "a": {"x": "b"}, "b": {"x": "a"},
            "dead": {"x": "dead"},
        },
        initial_state="a", final_states={"b"},
    )
    right = ExtendedDFA(
        states={0, 1, 2}, input_symbols={"x"},
        transitions={0: {"x": 1}, 1: {"x": 0}, 2: {"x": 2}},
        initial_state=0, final_states={1},
    )
    result = left.product(right, is_final=lambda q, p: q == "b" and p == 1)
    assert result.states == {("a", 0), ("b", 1)}
    assert len(result.states) == 2 < len(left.states) * len(right.states)
    assert ("dead", 2) not in result.states
    assert _pair_transitions(result)[("b", 1)]["x"] == ("a", 0)


def test_different_alphabets_follow_upstream_symbol_mismatch_policy() -> None:
    left = _three_state_cycle()
    right = ExtendedDFA(
        states={"p"}, input_symbols={"b"},
        transitions={"p": {"b": "p"}},
        initial_state="p", final_states=set(),
    )
    with pytest.raises(SymbolMismatchError):
        left.product(right, is_final=lambda _a, _b: False)


def test_partial_operands_use_upstream_implicit_traps_lazily() -> None:
    left = ExtendedDFA(
        states={"a0", "a1"}, input_symbols={"x", "y"},
        transitions={"a0": {"x": "a1"}, "a1": {"x": "a1"}},
        initial_state="a0", final_states={"a1"}, allow_partial=True,
    )
    right = ExtendedDFA(
        states={"b0", "b1"}, input_symbols={"x", "y"},
        transitions={"b0": {"y": "b1"}, "b1": {"y": "b1"}},
        initial_state="b0", final_states={"b1"}, allow_partial=True,
    )
    result = left.product(
        right, is_final=lambda a, b: a in left.final_states
        or b in right.final_states
    )
    assert result.states == {("a0", "b0"), ("a1", -1), (-1, "b1")}
    assert _pair_transitions(result)[("a0", "b0")] == {
        "x": ("a1", -1), "y": (-1, "b1"),
    }
    assert _pair_transitions(result)[("a1", -1)] == {"x": ("a1", -1)}
    assert _pair_transitions(result)[(-1, "b1")] == {"y": (-1, "b1")}
    assert result.final_states == {("a1", -1), (-1, "b1")}
    assert result.allow_partial is True


def test_none_and_heterogeneous_state_objects_remain_tuple_components() -> None:
    left = ExtendedDFA(
        states={None, 1}, input_symbols={"a"},
        transitions={None: {"a": 1}, 1: {"a": 1}},
        initial_state=None, final_states={1},
    )
    right = ExtendedDFA(
        states={"p", "q"}, input_symbols={"a"},
        transitions={"p": {"a": "q"}, "q": {"a": "q"}},
        initial_state="p", final_states={"q"},
    )
    result = left.product(right, is_final=lambda q, p: q == 1 and p == "q")
    assert result.initial_state == (None, "p")
    assert result.states == {(None, "p"), (1, "q")}
    assert result.final_states == {(1, "q")}


def test_product_preserves_both_sources_and_is_composable() -> None:
    left, right = _branching_operands()
    before_left = (deepcopy(left.states), deepcopy(left.transitions),
                   deepcopy(left.final_states))
    before_right = (deepcopy(right.states), deepcopy(right.transitions),
                    deepcopy(right.final_states))
    result = left.product(right, is_final=lambda q, p: q == "q1" or p == "p1")
    assert (left.states, left.transitions, left.final_states) == before_left
    assert (right.states, right.transitions, right.final_states) == before_right
    assert result is not left and result is not right
    assert result.reachable_states(result.initial_state) == result.states
    assert result.complete().is_complete() is True
    assert type(result.complement()) is ExtendedDFA


def test_raw_upstream_dfa_can_be_second_operand() -> None:
    left = _three_state_cycle()
    right = DFA(
        states={"p"}, input_symbols={"a"},
        transitions={"p": {"a": "p"}},
        initial_state="p", final_states={"p"},
    )
    result = left.product(right, is_final=lambda q, _p: q == "2")
    assert type(result) is ExtendedDFA
    assert result.states == {("0", "p"), ("1", "p"), ("2", "p")}
    assert result.final_states == {("2", "p")}


def test_mro_exposes_product_on_extended_dfa_only() -> None:
    assert ExtendedDFA.product is ProductMixin.product
    assert ProductMixin in ExtendedDFA.__mro__
    for cls in (ExtendedNFA, ExtendedGNFA):
        assert ProductMixin not in cls.__mro__
