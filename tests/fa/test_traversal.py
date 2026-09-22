"""DFS contracts across upstream representations, without arbitrary sorting."""

from copy import deepcopy
import sys
from unittest.mock import patch

import pytest
from automata.base.exceptions import InvalidStateError
from automata.fa.fa import FAStateT

from automata_extensions.fa import (
    ExtendedDFA,
    ExtendedFA,
    ExtendedGNFA,
    ExtendedNFA,
)


@pytest.fixture(params=[False, True], ids=["iterative", "recursive"])
def recursive(request: pytest.FixtureRequest) -> bool:
    """Exercise each contract with both DFS implementations."""
    return bool(request.param)


@pytest.fixture(params=["dfa", "nfa", "gnfa"])
def automaton(request: pytest.FixtureRequest) -> ExtendedFA:
    """Provide a branching graph, cycle and isolated state in each FA."""
    states = frozenset({"s", "a", "b", "c", "f", "unreachable"})
    if request.param == "dfa":
        return ExtendedDFA(
            states=states,
            input_symbols=frozenset({"0", "1"}),
            initial_state="s",
            transitions={
                "s": {"0": "a", "1": "b"},
                "a": {"0": "c"},
                "b": {"0": "f"},
                "c": {"0": "a", "1": "f"},
                "f": {},
                "unreachable": {"0": "unreachable"},
            },
            final_states=frozenset({"f"}),
            allow_partial=True,
        )
    if request.param == "nfa":
        return ExtendedNFA(
            states=states,
            input_symbols=frozenset({"0", "1"}),
            initial_state="s",
            transitions={
                "s": {"0": {"a", "b"}},
                "a": {"": {"c"}},
                "b": {"0": {"f"}},
                "c": {"0": {"a"}, "": {"f"}},
                "unreachable": {"0": {"unreachable"}},
            },
            final_states=frozenset({"f"}),
        )
    transitions: dict[str, dict[str, str | None]] = {
        state: {target: None for target in states if target != "s"}
        for state in states
        if state != "f"
    }
    transitions["s"].update({"a": "0", "b": "1"})
    transitions["a"]["c"] = ""
    transitions["b"]["f"] = "0|1"
    transitions["c"].update({"a": "0", "f": ""})
    transitions["unreachable"]["unreachable"] = "1*"
    return ExtendedGNFA(
        states=states,
        input_symbols=frozenset({"0", "1"}),
        initial_state="s",
        transitions=transitions,
        final_state="f",
    )


def test_discovery_is_depth_first(
    automaton: ExtendedFA, recursive: bool
) -> None:
    """Finish descendants before siblings, irrespective of sibling order."""
    result = automaton.dfs(recursive=recursive)
    assert isinstance(result, list)
    assert result[0] == automaton.initial_state
    assert set(result) == {"s", "a", "b", "c", "f"}
    assert len(result) == len(set(result))
    assert result in (
        ["s", "a", "c", "f", "b"],
        ["s", "b", "f", "a", "c"],
    )


def test_explicit_start(automaton: ExtendedFA, recursive: bool) -> None:
    """Starting inside a cycle must not include its ancestors."""
    assert automaton.dfs("a", recursive=recursive) == ["a", "c", "f"]
    assert automaton.dfs("unreachable", recursive=recursive) == ["unreachable"]


def test_terminal_start(automaton: ExtendedFA, recursive: bool) -> None:
    """Include the start even when it has no outgoing transitions."""
    assert automaton.dfs("f", recursive=recursive) == ["f"]


@pytest.mark.parametrize("invalid", ["absent", None, ["unhashable"]])
def test_invalid_start(
    automaton: ExtendedFA, recursive: bool, invalid: FAStateT
) -> None:
    """Invalid starts consistently raise the upstream exception."""
    with pytest.raises(InvalidStateError, match="not a valid start state"):
        automaton.dfs(invalid, recursive=recursive)


def test_variants_agree_for_same_stream(automaton: ExtendedFA) -> None:
    """The two variants follow the same neighbor iteration order."""
    assert automaton.dfs() == automaton.dfs(recursive=True)


def test_automaton_unchanged(automaton: ExtendedFA, recursive: bool) -> None:
    """Check slots, transitions, existing caches and newly added attributes."""
    attributes = set(vars(automaton))
    for cls in type(automaton).__mro__:
        slots = getattr(cls, "__slots__", ())
        attributes.update([slots] if isinstance(slots, str) else slots)
    attributes -= {"__dict__", "__weakref__"}
    before = deepcopy({name: getattr(automaton, name) for name in attributes})
    dictionary_before = deepcopy(vars(automaton))
    first = automaton.dfs(recursive=recursive)
    second = automaton.dfs(recursive=recursive)
    assert {name: getattr(automaton, name) for name in attributes} == before
    assert vars(automaton) == dictionary_before
    assert first == second
    assert first is not second
    first.clear()
    assert automaton.dfs(recursive=recursive) == second


def test_transitions_scanned_once(
    automaton: ExtendedFA, recursive: bool
) -> None:
    """Guard against rebuilding adjacency for every visited vertex."""
    original = type(automaton).iter_transitions
    with patch.object(
        type(automaton), "iter_transitions", autospec=True
    ) as scan:
        scan.side_effect = original
        result = automaton.dfs(recursive=recursive)
    assert len(result) == 5
    scan.assert_called_once_with(automaton)


def test_complete_dfa_branches(recursive: bool) -> None:
    """Each disjoint branch is completed before the next branch starts."""
    dfa = ExtendedDFA(
        states={"s", "l", "ll", "r", "rr"},
        input_symbols={"0", "1"},
        transitions={
            "s": {"0": "l", "1": "r"},
            "l": {"0": "ll", "1": "ll"},
            "ll": {"0": "l", "1": "ll"},
            "r": {"0": "rr", "1": "rr"},
            "rr": {"0": "r", "1": "rr"},
        },
        initial_state="s",
        final_states=set(),
    )
    assert dfa.dfs(recursive=recursive) in (
        ["s", "l", "ll", "r", "rr"],
        ["s", "r", "rr", "l", "ll"],
    )


def test_pending_sibling_can_be_discovered_deeper(recursive: bool) -> None:
    """Prematurely marking all pushed siblings must not break true DFS."""
    dfa = ExtendedDFA(
        states={"s", "a", "b", "leaf", "c"},
        input_symbols={"0", "1"},
        transitions={
            "s": {"0": "a", "1": "b"},
            "a": {"0": "b", "1": "c"},
            "b": {"0": "leaf"},
            "leaf": {},
            "c": {},
        },
        initial_state="s",
        final_states={"leaf"},
        allow_partial=True,
    )
    # Order here is the declared transition-stream order, not sorted states.
    assert dfa.dfs(recursive=recursive) == ["s", "a", "b", "leaf", "c"]


@pytest.mark.parametrize("with_loop", [False, True])
def test_single_state(recursive: bool, with_loop: bool) -> None:
    """A singleton with or without a self-loop is visited once."""
    dfa = ExtendedDFA(
        states={0},
        input_symbols={"a"} if with_loop else set(),
        transitions={0: {"a": 0} if with_loop else {}},
        initial_state=0,
        final_states=set(),
    )
    assert dfa.dfs(recursive=recursive) == [0]


def test_nfa_epsilon_only_path(recursive: bool) -> None:
    """Epsilon edges, cycles and omitted terminal mappings are graph edges."""
    nfa = ExtendedNFA(
        states={0, 1, 2, 3},
        input_symbols=set(),
        transitions={0: {"": {1}}, 1: {"": {0, 2}}},
        initial_state=0,
        final_states={2},
    )
    assert nfa.dfs(recursive=recursive) == [0, 1, 2]


def test_nfa_mixed_states_and_parallel_edges(recursive: bool) -> None:
    """Unorderable state types and repeated targets require no sorting."""
    root, number, frozen, pair = "root", 7, frozenset({2}), (1, "x")
    nfa = ExtendedNFA(
        states={root, number, frozen, pair},
        input_symbols={"a", "b"},
        transitions={
            root: {"a": {number, frozen}, "b": {number}},
            number: {"": {pair}},
            frozen: {"": {pair}},
        },
        initial_state=root,
        final_states={pair},
    )
    result = nfa.dfs(recursive=recursive)
    assert result in (
        [root, number, pair, frozen],
        [root, frozen, pair, number],
    )


def test_nfa_empty_target_set(recursive: bool) -> None:
    """An empty target set creates no edge."""
    nfa = ExtendedNFA(
        states={"s", "f"},
        input_symbols={"a"},
        transitions={"s": {"a": set()}},
        initial_state="s",
        final_states={"f"},
    )
    assert nfa.dfs(recursive=recursive) == ["s"]


@pytest.mark.parametrize("label", [None, "", "a*"])
def test_gnfa_label_semantics(recursive: bool, label: str | None) -> None:
    """None is no edge, whereas epsilon and regex labels are real edges."""
    gnfa = ExtendedGNFA(
        states={"s", "f"},
        input_symbols={"a"},
        transitions={"s": {"f": label}},
        initial_state="s",
        final_state="f",
    )
    expected = ["s"] if label is None else ["s", "f"]
    assert gnfa.dfs(recursive=recursive) == expected


def test_none_is_an_explicit_state(recursive: bool) -> None:
    """The private default sentinel leaves None available as a real state."""
    dfa = ExtendedDFA(
        states={"s", None, "f"},
        input_symbols={"a"},
        transitions={"s": {"a": None}, None: {"a": "f"}, "f": {}},
        initial_state="s",
        final_states={"f"},
        allow_partial=True,
    )
    assert dfa.dfs(recursive=recursive) == ["s", None, "f"]
    assert dfa.dfs(None, recursive=recursive) == [None, "f"]


def test_none_initial_state(recursive: bool) -> None:
    """An omitted start also works when the initial state itself is None."""
    dfa = ExtendedDFA(
        states={None},
        input_symbols=set(),
        transitions={None: {}},
        initial_state=None,
        final_states=set(),
    )
    assert dfa.dfs(recursive=recursive) == [None]


def test_unhashable_set_equal_to_a_state(recursive: bool) -> None:
    """Reject unhashable sets even when equal to a frozenset state."""
    state = frozenset({1})
    dfa = ExtendedDFA(
        states={state},
        input_symbols=set(),
        transitions={state: {}},
        initial_state=state,
        final_states=set(),
    )
    with pytest.raises(InvalidStateError):
        dfa.dfs({1}, recursive=recursive)


def test_default_is_iterative_and_recursive_is_real() -> None:
    """A deep chain distinguishes stack traversal from genuine recursion."""
    limit = sys.getrecursionlimit()
    size = limit + 50
    dfa = ExtendedDFA(
        states=frozenset(range(size)),
        input_symbols={"a"},
        transitions={
            state: {"a": state + 1} if state + 1 < size else {}
            for state in range(size)
        },
        initial_state=0,
        final_states={size - 1},
        allow_partial=True,
    )
    assert dfa.dfs() == list(range(size))
    with pytest.raises(RecursionError):
        dfa.dfs(recursive=True)
    assert sys.getrecursionlimit() == limit
    assert dfa.dfs() == list(range(size))
