"""Mathematical and structural contracts for strongly connected components."""

from copy import deepcopy
from typing import FrozenSet
from unittest.mock import patch

import pytest
from automata.fa.fa import FAStateT

from automata_extensions.fa import ExtendedDFA, ExtendedFA, ExtendedGNFA, ExtendedNFA


def _dfa(
    states: set[FAStateT], edges: list[tuple[FAStateT, FAStateT]],
    initial: FAStateT,
) -> ExtendedDFA:
    """Build a partial DFA whose distinct symbols realize the given edges."""
    symbols = {f"a{i}" for i in range(len(edges))}
    transitions: dict[FAStateT, dict[str, FAStateT]] = {
        state: {} for state in states
    }
    for i, (source, target) in enumerate(edges):
        transitions[source][f"a{i}"] = target
    return ExtendedDFA(
        states=states,
        input_symbols=symbols,
        transitions=transitions,
        initial_state=initial,
        final_states=set(),
        allow_partial=True,
    )


def _assert_partition(
    automaton: ExtendedFA, expected: set[FrozenSet[FAStateT]]
) -> None:
    """Check the partition without relying on Tarjan's discovery order."""
    components = automaton.strongly_connected_components()
    assert type(components) is list
    assert all(type(component) is frozenset for component in components)
    assert all(components)
    assert len(components) == len(expected)
    assert set(components) == expected
    seen: set[FAStateT] = set()
    for component in components:
        assert not (seen & component)
        seen.update(component)
    assert seen == automaton.states


@pytest.mark.parametrize("with_loop", [False, True])
@pytest.mark.parametrize("state", ["q", None])
def test_singleton_is_a_component_with_or_without_loop(
    state: FAStateT, with_loop: bool
) -> None:
    edges = [(state, state)] if with_loop else []
    _assert_partition(_dfa({state}, edges, state), {frozenset({state})})


def test_chain_has_only_singletons() -> None:
    automaton = _dfa({0, 1, 2}, [(0, 1), (1, 2)], 0)
    _assert_partition(
        automaton, {frozenset({0}), frozenset({1}), frozenset({2})}
    )


def test_simple_cycle_is_one_component() -> None:
    automaton = _dfa({0, 1, 2}, [(0, 1), (1, 2), (2, 0)], 0)
    _assert_partition(automaton, {frozenset({0, 1, 2})})
    for state in automaton.states:
        assert set(automaton.dfs(state)) == automaton.states


def test_one_way_edge_between_cycles_does_not_merge_them() -> None:
    automaton = _dfa(
        {0, 1, 2, 3},
        [(0, 1), (1, 0), (1, 2), (2, 3), (3, 2)],
        0,
    )
    _assert_partition(automaton, {frozenset({0, 1}), frozenset({2, 3})})
    assert 2 in automaton.dfs(0)
    assert 0 not in automaton.dfs(2)


def test_disconnected_cycles_and_unreachable_states_are_included() -> None:
    automaton = _dfa(
        {0, 1, 2, 3, 4},
        [(0, 1), (1, 0), (2, 3), (3, 2)],
        0,
    )
    _assert_partition(
        automaton,
        {frozenset({0, 1}), frozenset({2, 3}), frozenset({4})},
    )
    assert {2, 3, 4}.isdisjoint(automaton.dfs())


def test_mixed_singletons_cycle_self_loop_and_parallel_edges() -> None:
    automaton = _dfa(
        {"start", "a", "b", "tail", "idle"},
        [
            ("start", "a"), ("a", "b"), ("b", "a"),
            ("a", "b"), ("b", "tail"), ("tail", "tail"),
        ],
        "start",
    )
    _assert_partition(
        automaton,
        {
            frozenset({"start"}), frozenset({"a", "b"}),
            frozenset({"tail"}), frozenset({"idle"}),
        },
    )


def test_heterogeneous_unorderable_states_need_no_sort() -> None:
    states = {None, "one", 2, (3,)}
    automaton = _dfa(
        states,
        [(None, "one"), ("one", None), (2, (3,))],
        None,
    )
    _assert_partition(
        automaton,
        {frozenset({None, "one"}), frozenset({2}), frozenset({(3,)})},
    )


def test_nfa_multiple_destinations_and_epsilon_edges() -> None:
    nfa = ExtendedNFA(
        states={"s", "a", "b", "isolated"},
        input_symbols={"x"},
        transitions={
            "s": {"x": {"a", "b"}},
            "a": {"": {"s"}},
            "b": {"x": {"b"}},
        },
        initial_state="s",
        final_states=set(),
    )
    _assert_partition(
        nfa,
        {frozenset({"s", "a"}), frozenset({"b"}),
         frozenset({"isolated"})},
    )


def test_nfa_epsilon_only_cycle_and_none_state() -> None:
    nfa = ExtendedNFA(
        states={None, 1, "other"},
        input_symbols=set(),
        transitions={None: {"": {1}}, 1: {"": {None}}},
        initial_state=None,
        final_states=set(),
    )
    _assert_partition(nfa, {frozenset({None, 1}), frozenset({"other"})})


def test_gnfa_ignores_none_labels_but_keeps_epsilon_edges() -> None:
    states = {"start", "a", "b", "end", "isolated"}
    labels = {
        ("start", "a"): "",
        ("a", "b"): "a",
        ("b", "a"): "",
        ("b", "end"): "a",
    }
    gnfa = ExtendedGNFA(
        states=states,
        input_symbols={"a"},
        transitions={
            source: {
                target: labels.get((source, target))
                for target in states - {"start"}
            }
            for source in states - {"end"}
        },
        initial_state="start",
        final_state="end",
    )
    _assert_partition(
        gnfa,
        {frozenset({"start"}), frozenset({"a", "b"}),
         frozenset({"end"}), frozenset({"isolated"})},
    )


@pytest.mark.parametrize("kind", ["dfa", "nfa", "gnfa"])
def test_source_unchanged_and_common_graph_scanned_once(kind: str) -> None:
    if kind == "dfa":
        automaton: ExtendedFA = _dfa({0, 1}, [(0, 1), (1, 0)], 0)
    elif kind == "nfa":
        automaton = ExtendedNFA(
            states={0, 1}, input_symbols={"a"},
            transitions={0: {"a": {1}}, 1: {"": {0}}},
            initial_state=0, final_states={1},
        )
    else:
        automaton = ExtendedGNFA(
            states={0, 1}, input_symbols={"a"},
            transitions={0: {1: "a"}},
            initial_state=0, final_state=1,
        )

    before = (
        deepcopy(automaton.states), deepcopy(automaton.transitions),
        deepcopy(automaton.final_states), automaton.initial_state,
    )
    with patch.object(
        type(automaton), "iter_transitions", wraps=automaton.iter_transitions
    ) as scan:
        first = automaton.strongly_connected_components()
    assert scan.call_count == 1
    assert (
        automaton.states, automaton.transitions,
        automaton.final_states, automaton.initial_state,
    ) == before
    second = automaton.strongly_connected_components()
    assert second == first
    assert second is not first


def test_public_classes_inherit_one_common_scc_implementation() -> None:
    for cls in (ExtendedDFA, ExtendedNFA, ExtendedGNFA):
        assert hasattr(cls, "strongly_connected_components")
        assert (
            cls.strongly_connected_components
            is ExtendedFA.strongly_connected_components
        )
