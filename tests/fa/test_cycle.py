"""Global directed-cycle detection across concrete finite automata."""

from copy import deepcopy
from unittest.mock import patch

import pytest
from automata.base.exceptions import InvalidStateError
from automata.fa.fa import FAStateT

from automata_extensions.fa import ExtendedDFA, ExtendedFA, ExtendedGNFA, ExtendedNFA


def _dfa(
    states: set[FAStateT],
    edges: list[tuple[FAStateT, FAStateT]],
    initial: FAStateT,
) -> ExtendedDFA:
    """Realize each requested graph edge with a distinct DFA symbol."""
    transitions: dict[FAStateT, dict[str, FAStateT]] = {
        state: {} for state in states
    }
    for i, (source, target) in enumerate(edges):
        transitions[source][f"a{i}"] = target
    return ExtendedDFA(
        states=states,
        input_symbols={f"a{i}" for i in range(len(edges))},
        transitions=transitions,
        initial_state=initial,
        final_states=set(),
        allow_partial=True,
    )


@pytest.mark.parametrize(
    ("states", "edges", "initial", "expected"),
    [
        ({"q"}, [], "q", False),
        ({"q"}, [("q", "q")], "q", True),
        ({0, 1, 2}, [(0, 1), (1, 2)], 0, False),
        ({0, 1}, [(0, 1), (1, 0)], 0, True),
        ({0, 1, 2}, [(0, 1), (1, 2), (2, 0)], 0, True),
        (
            {"s", "a", "b", "c"},
            [("s", "a"), ("s", "b"), ("a", "c"), ("b", "c")],
            "s",
            False,
        ),
        ({0, 1, 2, 3}, [(0, 1), (2, 3), (3, 2)], 0, True),
        ({0, 1, 2, 3}, [(0, 1), (2, 3)], 0, False),
        ({0, 1, 2, 3}, [(0, 1), (1, 0), (2, 3)], 0, True),
        ({0, 1, 2}, [(0, 1), (0, 2), (1, 2)], 0, False),
    ],
    ids=[
        "singleton-no-edge",
        "self-loop",
        "chain",
        "two-cycle",
        "three-cycle",
        "diamond-black-cross-edge",
        "inaccessible-cycle",
        "disconnected-acyclic",
        "initial-cycle-with-disconnected-component",
        "dag-with-forward-edge",
    ],
)
def test_dfa_graphs(
    states: set[FAStateT],
    edges: list[tuple[FAStateT, FAStateT]],
    initial: FAStateT,
    expected: bool,
) -> None:
    """Only a back edge, not a completed-state edge, establishes a cycle."""
    automaton = _dfa(states, edges, initial)
    result = automaton.has_cycle()
    assert type(result) is bool
    assert result is expected


@pytest.mark.parametrize("cyclic", [False, True])
def test_nfa_multiple_destinations(cyclic: bool) -> None:
    """A nondeterministic branch is not itself a cycle."""
    nfa = ExtendedNFA(
        states={"s", "a", "b"},
        input_symbols={"x"},
        transitions={
            "s": {"x": {"a", "b"}},
            "a": {"x": {"b"}},
            "b": {"x": {"s"}} if cyclic else {},
        },
        initial_state="s",
        final_states=set(),
    )
    assert nfa.has_cycle() is cyclic


def test_nfa_epsilon_cycle() -> None:
    nfa = ExtendedNFA(
        states={"s", "a", "b"},
        input_symbols=set(),
        transitions={"s": {"": {"a"}}, "a": {"": {"s"}}},
        initial_state="s",
        final_states=set(),
    )
    assert nfa.has_cycle() is True


@pytest.mark.parametrize("cyclic", [False, True])
def test_gnfa_none_slots_are_not_edges(cyclic: bool) -> None:
    """Only non-None labels, including epsilon, contribute graph edges."""
    states = {"s", "a", "b", "f"}
    labels = {
        ("s", "a"): "",
        ("a", "b"): "x",
        ("b", "a"): "x" if cyclic else None,
    }
    gnfa = ExtendedGNFA(
        states=states,
        input_symbols={"x"},
        transitions={
            source: {
                target: labels.get((source, target))
                for target in states - {"s"}
            }
            for source in states - {"f"}
        },
        initial_state="s",
        final_state="f",
    )
    assert gnfa.has_cycle() is cyclic


@pytest.mark.parametrize("cyclic", [False, True])
def test_none_and_heterogeneous_states(cyclic: bool) -> None:
    edges: list[tuple[FAStateT, FAStateT]] = [
        (None, "a"), ("a", 2), (2, (3,)),
    ]
    if cyclic:
        edges.append(((3,), None))
    automaton = _dfa({None, "a", 2, (3,)}, edges, None)
    assert automaton.has_cycle() is cyclic


@pytest.mark.parametrize("kind", ["dfa", "nfa", "gnfa"])
def test_query_does_not_mutate_or_cache(kind: str) -> None:
    if kind == "dfa":
        automaton: ExtendedFA = _dfa({0, 1}, [(0, 1), (1, 0)], 0)
    elif kind == "nfa":
        automaton = ExtendedNFA(
            states={0, 1}, input_symbols={"x"},
            transitions={0: {"x": {1}}, 1: {"": {0}}},
            initial_state=0, final_states=set(),
        )
    else:
        automaton = ExtendedGNFA(
            states={0, 1}, input_symbols={"x"},
            transitions={0: {1: "x"}},
            initial_state=0, final_state=1,
        )
    before = (
        deepcopy(automaton.states), deepcopy(automaton.transitions),
        deepcopy(automaton.final_states), automaton.initial_state,
    )
    with patch.object(
        type(automaton), "iter_transitions", wraps=automaton.iter_transitions
    ) as scan:
        first = automaton.has_cycle()
        second = automaton.has_cycle()
    assert type(first) is bool
    assert first is second
    assert scan.call_count == 2
    assert (
        automaton.states, automaton.transitions,
        automaton.final_states, automaton.initial_state,
    ) == before


def test_does_not_delegate_to_scc() -> None:
    automaton = _dfa({0, 1}, [(0, 1), (1, 0)], 0)
    with patch.object(
        ExtendedFA, "strongly_connected_components",
        side_effect=AssertionError("SCC must not be used for cycle detection"),
    ):
        assert automaton.has_cycle() is True


def test_public_classes_inherit_common_cycle_method() -> None:
    for cls in (ExtendedDFA, ExtendedNFA, ExtendedGNFA):
        assert cls.has_cycle is ExtendedFA.has_cycle
        assert cls.has_cycle_from is ExtendedFA.has_cycle_from


@pytest.mark.parametrize(
    ("states", "edges", "start", "expected"),
    [
        ({"q"}, [], "q", False),
        ({"q"}, [("q", "q")], "q", True),
        ({0, 1, 2}, [(0, 1), (1, 2)], 0, False),
        ({0, 1}, [(0, 1), (1, 0)], 0, True),
        ({0, 1, 2, 3}, [(0, 1), (1, 2), (2, 3), (3, 1)], 0, True),
        ({0, 1, 2, 3}, [(0, 1), (2, 3), (3, 2)], 0, False),
        ({0, 1, 2, 3}, [(0, 1), (2, 3), (3, 2)], 2, True),
        (
            {"s", "a", "b", "c"},
            [("s", "a"), ("s", "b"), ("a", "c"), ("b", "c")],
            "s",
            False,
        ),
    ],
    ids=[
        "isolated-start", "self-loop", "chain", "start-in-cycle",
        "reachable-later-cycle", "unreachable-cycle", "start-in-other-cycle",
        "black-edge-dag",
    ],
)
def test_has_cycle_from_dfa_subgraph(
    states: set[FAStateT],
    edges: list[tuple[FAStateT, FAStateT]],
    start: FAStateT,
    expected: bool,
) -> None:
    automaton = _dfa(states, edges, 0 if 0 in states else start)
    result = automaton.has_cycle_from(start)
    assert type(result) is bool
    assert result is expected
    if result:
        assert automaton.has_cycle() is True


def test_global_cycle_can_be_unreachable_from_a_start() -> None:
    automaton = _dfa(
        {"q0", "q1", "x", "y"},
        [("q0", "q1"), ("x", "y"), ("y", "x")],
        "q0",
    )
    assert automaton.has_cycle() is True
    assert automaton.has_cycle_from("q0") is False
    assert automaton.has_cycle_from("x") is True
    assert automaton.has_cycle_from("y") is True


@pytest.mark.parametrize("cyclic", [False, True])
def test_has_cycle_from_nfa_multiple_destinations(cyclic: bool) -> None:
    nfa = ExtendedNFA(
        states={"s", "a", "b", "idle"},
        input_symbols={"x"},
        transitions={
            "s": {"x": {"a", "b"}},
            "a": {"x": {"b"}},
            "b": {"x": {"a"}} if cyclic else {},
        },
        initial_state="s",
        final_states=set(),
    )
    assert nfa.has_cycle_from("s") is cyclic
    assert nfa.has_cycle_from("idle") is False


def test_has_cycle_from_nfa_epsilon_path_to_cycle() -> None:
    nfa = ExtendedNFA(
        states={"s", "a", "b", "idle"},
        input_symbols=set(),
        transitions={
            "s": {"": {"a"}},
            "a": {"": {"b"}},
            "b": {"": {"a"}},
        },
        initial_state="s",
        final_states=set(),
    )
    assert nfa.has_cycle_from("s") is True
    assert nfa.has_cycle_from("idle") is False


@pytest.mark.parametrize("cyclic", [False, True])
def test_has_cycle_from_gnfa_respects_none_slots(cyclic: bool) -> None:
    states = {"s", "a", "b", "f"}
    labels = {
        ("s", "a"): "",
        ("a", "b"): "x",
        ("b", "a"): "x" if cyclic else None,
    }
    gnfa = ExtendedGNFA(
        states=states,
        input_symbols={"x"},
        transitions={
            source: {
                target: labels.get((source, target))
                for target in states - {"s"}
            }
            for source in states - {"f"}
        },
        initial_state="s",
        final_state="f",
    )
    assert gnfa.has_cycle_from("s") is cyclic
    assert gnfa.has_cycle_from("f") is False


@pytest.mark.parametrize("cyclic", [False, True])
def test_has_cycle_from_none_and_heterogeneous_states(cyclic: bool) -> None:
    edges: list[tuple[FAStateT, FAStateT]] = [
        ("s", None), (None, 2), (2, (3,)),
    ]
    if cyclic:
        edges.append(((3,), None))
    automaton = _dfa({"s", None, 2, (3,)}, edges, "s")
    assert automaton.has_cycle_from(None) is cyclic
    assert automaton.has_cycle_from("s") is cyclic


@pytest.mark.parametrize("invalid", ["missing", None, ["q"]])
def test_has_cycle_from_invalid_start_matches_dfs(invalid: FAStateT) -> None:
    automaton = _dfa({"q"}, [], "q")
    with pytest.raises(InvalidStateError):
        automaton.dfs(invalid)
    with pytest.raises(InvalidStateError):
        automaton.has_cycle_from(invalid)


@pytest.mark.parametrize("kind", ["dfa", "nfa", "gnfa"])
def test_has_cycle_from_does_not_mutate_or_cache(kind: str) -> None:
    if kind == "dfa":
        automaton: ExtendedFA = _dfa({0, 1}, [(0, 1), (1, 0)], 0)
    elif kind == "nfa":
        automaton = ExtendedNFA(
            states={0, 1}, input_symbols={"x"},
            transitions={0: {"x": {1}}, 1: {"": {0}}},
            initial_state=0, final_states=set(),
        )
    else:
        automaton = ExtendedGNFA(
            states={0, 1}, input_symbols={"x"},
            transitions={0: {1: "x"}},
            initial_state=0, final_state=1,
        )
    before = (
        deepcopy(automaton.states), deepcopy(automaton.transitions),
        deepcopy(automaton.final_states), automaton.initial_state,
    )
    with patch.object(
        type(automaton), "iter_transitions", wraps=automaton.iter_transitions
    ) as scan:
        first = automaton.has_cycle_from(0)
        second = automaton.has_cycle_from(0)
    assert type(first) is bool
    assert first is second
    assert scan.call_count == 2
    assert (
        automaton.states, automaton.transitions,
        automaton.final_states, automaton.initial_state,
    ) == before


def test_has_cycle_from_does_not_delegate_to_scc() -> None:
    automaton = _dfa({0, 1}, [(0, 1), (1, 0)], 0)
    with patch.object(
        ExtendedFA, "strongly_connected_components",
        side_effect=AssertionError("SCC must not be used for cycle detection"),
    ):
        assert automaton.has_cycle_from(0) is True
