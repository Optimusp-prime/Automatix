"""Contracts for accessibility from the initial state across all FA types."""

from copy import deepcopy
from unittest.mock import patch

import pytest
from automata.fa.fa import FAStateT

from automata_extensions.fa import (
    ExtendedDFA,
    ExtendedFA,
    ExtendedGNFA,
    ExtendedNFA,
)


@pytest.fixture(params=["dfa", "nfa", "gnfa"])
def automaton(request: pytest.FixtureRequest) -> ExtendedFA:
    """Reach a nonfinal cycle while the sole final state stays isolated."""
    states = frozenset({"s", "a", "b", "f"})
    if request.param == "dfa":
        return ExtendedDFA(
            states=states,
            input_symbols={"0", "1"},
            transitions={
                "s": {"0": "a", "1": "b"},
                "a": {"0": "b", "1": "a"},
                "b": {"0": "a", "1": "b"},
                "f": {"0": "f", "1": "f"},
            },
            initial_state="s",
            final_states={"f"},
        )
    if request.param == "nfa":
        return ExtendedNFA(
            states=states,
            input_symbols={"0"},
            transitions={
                "s": {"": {"a"}},
                "a": {"0": {"a", "b"}},
                "b": {"": {"s"}},
            },
            initial_state="s",
            final_states={"f"},
        )
    return ExtendedGNFA(
        states=states,
        input_symbols={"0"},
        transitions={
            "s": {"a": "", "b": None, "f": None},
            "a": {"a": "0", "b": "0", "f": None},
            "b": {"a": "0", "b": None, "f": None},
        },
        initial_state="s",
        final_state="f",
    )


def test_accessibility_is_reachability_not_finality(
    automaton: ExtendedFA,
) -> None:
    """An accessible nonfinal state need not have a path to a final state."""
    result = automaton.accessible_states()
    assert isinstance(result, frozenset)
    assert result == {"s", "a", "b"}
    assert automaton.initial_state in result
    assert "f" not in result
    assert len(result) == 3
    assert not (result & automaton.final_states)


def test_accessible_states_agree_with_traversals(
    automaton: ExtendedFA,
) -> None:
    """Both verified traversals induce the same mathematical state set."""
    result = automaton.accessible_states()
    assert result == set(automaton.dfs())
    assert result == set(automaton.bfs())


@pytest.mark.parametrize("partial", [False, True])
@pytest.mark.parametrize("unreachable", [False, True])
def test_dfa_all_reachable_or_disconnected(
    partial: bool, unreachable: bool
) -> None:
    """Complete and partial DFAs use the same accessibility semantics."""
    states = {0, 1, 2}
    transitions = {0: {"a": 1}, 1: {"a": 2}, 2: {} if partial else {"a": 0}}
    if unreachable:
        states.add(3)
        transitions[3] = {} if partial else {"a": 3}
    dfa = ExtendedDFA(
        states=states,
        input_symbols={"a"},
        transitions=transitions,
        initial_state=0,
        final_states={2},
        allow_partial=partial,
    )
    assert dfa.accessible_states() == {0, 1, 2}


@pytest.mark.parametrize("initial", [0, None])
@pytest.mark.parametrize("with_loop", [False, True])
def test_initial_state_is_accessible_by_zero_length_path(
    initial: FAStateT, with_loop: bool
) -> None:
    """A singleton is accessible even without edges or accepting states."""
    dfa = ExtendedDFA(
        states={initial},
        input_symbols={"a"} if with_loop else set(),
        transitions={initial: {"a": initial} if with_loop else {}},
        initial_state=initial,
        final_states=set(),
    )
    assert dfa.accessible_states() == frozenset({initial})


def test_nfa_epsilon_only_path() -> None:
    """States reachable solely through epsilon edges are accessible."""
    nfa = ExtendedNFA(
        states={0, 1, 2, 3},
        input_symbols=set(),
        transitions={0: {"": {1}}, 1: {"": {0, 2}}},
        initial_state=0,
        final_states={2},
    )
    assert nfa.accessible_states() == {0, 1, 2}


@pytest.mark.parametrize("label", [None, "", "a*"])
def test_gnfa_present_and_absent_edges(label: str | None) -> None:
    """Only actual GNFA edges can make the final state accessible."""
    gnfa = ExtendedGNFA(
        states={"s", "f"},
        input_symbols={"a"},
        transitions={"s": {"f": label}},
        initial_state="s",
        final_state="f",
    )
    expected = {"s"} if label is None else {"s", "f"}
    assert gnfa.accessible_states() == expected


def test_heterogeneous_states_and_multiple_destinations() -> None:
    """Preserve unorderable states and None, without duplicate targets."""
    number, frozen, pair = 7, frozenset({2}), (1, "x")
    nfa = ExtendedNFA(
        states={None, number, frozen, pair, "isolated"},
        input_symbols={"a", "b"},
        transitions={
            None: {"a": {number, frozen}, "b": {number}},
            number: {"": {pair}},
            frozen: {"": {pair}},
        },
        initial_state=None,
        final_states={pair},
    )
    result = nfa.accessible_states()
    assert result == {None, number, frozen, pair}
    assert len(result) == 4


def test_result_independent_of_discovery_order() -> None:
    """Different real DFS discovery orders must produce equal sets."""
    left_first = ExtendedDFA(
        states={"s", "left", "right"},
        input_symbols={"a", "b"},
        transitions={
            "s": {"a": "left", "b": "right"},
            "left": {},
            "right": {},
        },
        initial_state="s",
        final_states=set(),
        allow_partial=True,
    )
    right_first = ExtendedDFA(
        states={"s", "left", "right"},
        input_symbols={"a", "b"},
        transitions={
            "s": {"b": "right", "a": "left"},
            "left": {},
            "right": {},
        },
        initial_state="s",
        final_states=set(),
        allow_partial=True,
    )
    assert left_first.dfs() != right_first.dfs()
    assert left_first.accessible_states() == right_first.accessible_states()
    assert left_first.accessible_states() == {"s", "left", "right"}


def test_source_and_result_immutability(automaton: ExtendedFA) -> None:
    """Inspect all slots and caches, and keep set operations independent."""
    attributes = set(vars(automaton))
    for cls in type(automaton).__mro__:
        slots = getattr(cls, "__slots__", ())
        attributes.update([slots] if isinstance(slots, str) else slots)
    attributes -= {"__dict__", "__weakref__"}
    before = deepcopy({name: getattr(automaton, name) for name in attributes})
    dictionary_before = deepcopy(vars(automaton))

    result = automaton.accessible_states()
    assert isinstance(result, frozenset)
    assert not hasattr(result, "add")
    assert result | {"new"} == {"s", "a", "b", "new"}
    assert result - {"a"} == {"s", "b"}
    assert result & {"a", "f"} == {"a"}
    assert result == automaton.accessible_states() == {"s", "a", "b"}
    assert {name: getattr(automaton, name) for name in attributes} == before
    assert vars(automaton) == dictionary_before


def test_single_delegated_traversal(automaton: ExtendedFA) -> None:
    """Prevent a new local traversal or a second adjacency construction."""
    original_dfs = type(automaton).dfs
    original_scan = type(automaton).iter_transitions
    with (
        patch.object(type(automaton), "dfs", autospec=True) as traversal,
        patch.object(
            type(automaton), "iter_transitions", autospec=True
        ) as scan,
    ):
        traversal.side_effect = original_dfs
        scan.side_effect = original_scan
        result = automaton.accessible_states()
    assert result == {"s", "a", "b"}
    traversal.assert_called_once_with(automaton)
    scan.assert_called_once_with(automaton)
