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


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("s", True),
        ("a", True),
        ("b", True),
        ("f", False),
        ("absent", False),
        (None, False),
    ],
)
def test_is_accessible_membership_contract(
    automaton: ExtendedFA, state: FAStateT, expected: bool
) -> None:
    """Check membership for initial, cyclic, epsilon and absent states."""
    result = automaton.is_accessible(state)
    assert result is expected
    assert result is (state in automaton.accessible_states())


@pytest.mark.parametrize("initial", [0, None])
def test_is_accessible_singleton(initial: FAStateT) -> None:
    """The zero-length path makes even a None singleton accessible."""
    dfa = ExtendedDFA(
        states={initial},
        input_symbols=set(),
        transitions={initial: {}},
        initial_state=initial,
        final_states=set(),
    )
    assert dfa.is_accessible(initial) is True
    assert dfa.is_accessible("absent") is False


@pytest.mark.parametrize("reach_none", [False, True])
def test_is_accessible_partial_dfa_mixed_states(reach_none: bool) -> None:
    """None can be a real reachable or unreachable state in a partial DFA."""
    frozen = frozenset({2})
    dfa = ExtendedDFA(
        states={"s", 7, frozen, None, "isolated"},
        input_symbols={"a"},
        transitions={
            "s": {"a": 7},
            7: {"a": frozen},
            frozen: {"a": None} if reach_none else {},
            None: {},
            "isolated": {},
        },
        initial_state="s",
        final_states={"isolated"},
        allow_partial=True,
    )
    assert dfa.is_accessible(7) is True
    assert dfa.is_accessible(frozen) is True
    assert dfa.is_accessible(None) is reach_none
    assert dfa.is_accessible("isolated") is False
    assert dfa.is_accessible((1, "absent")) is False
    for state in dfa.states:
        assert dfa.is_accessible(state) is (state in dfa.accessible_states())


def test_is_accessible_preserves_source_and_set(automaton: ExtendedFA) -> None:
    """Boolean queries leave attributes, caches and the computed set intact."""
    attributes = set(vars(automaton))
    for cls in type(automaton).__mro__:
        slots = getattr(cls, "__slots__", ())
        attributes.update([slots] if isinstance(slots, str) else slots)
    attributes -= {"__dict__", "__weakref__"}
    before = deepcopy({name: getattr(automaton, name) for name in attributes})
    dictionary_before = deepcopy(vars(automaton))
    states_before = automaton.accessible_states()

    for _ in range(2):
        assert automaton.is_accessible("a") is True
        assert automaton.is_accessible("f") is False
        assert automaton.is_accessible("absent") is False

    assert states_before == automaton.accessible_states() == {"s", "a", "b"}
    assert {name: getattr(automaton, name) for name in attributes} == before
    assert vars(automaton) == dictionary_before


def test_is_accessible_delegates_once(automaton: ExtendedFA) -> None:
    """Use the existing set query once without a second local traversal."""
    original = type(automaton).accessible_states
    with patch.object(
        type(automaton), "accessible_states", autospec=True
    ) as query:
        query.side_effect = original
        assert automaton.is_accessible("a") is True
    query.assert_called_once_with(automaton)


def test_is_accessible_rejects_list_membership(automaton: ExtendedFA) -> None:
    """Unsupported membership keys retain the native TypeError behavior."""
    with pytest.raises(TypeError):
        automaton.is_accessible(["a"])


@pytest.mark.parametrize("partial", [False, True])
def test_coaccessible_chain(partial: bool) -> None:
    """A final with no outgoing edge still reaches itself in zero steps."""
    dfa = ExtendedDFA(
        states={0, 1, 2}, input_symbols={"a"},
        transitions={0: {"a": 1}, 1: {"a": 2},
                     2: {} if partial else {"a": 2}},
        initial_state=0, final_states={2}, allow_partial=partial,
    )
    assert dfa.coaccessible_states() == frozenset({0, 1, 2})


def test_coaccessible_multiple_finals_and_distinct_accessibility() -> None:
    """Reverse exploration includes disconnected paths to either final."""
    dfa = ExtendedDFA(
        states={"s", "dead", "u", "f", "v", "g"},
        input_symbols={"a", "b"},
        transitions={
            "s": {"a": "dead", "b": "f"}, "dead": {"a": "dead"},
            "u": {"a": "f"}, "f": {}, "v": {"a": "g"}, "g": {},
        },
        initial_state="s", final_states={"f", "g"}, allow_partial=True,
    )
    assert dfa.accessible_states() == {"s", "dead", "f"}
    assert dfa.coaccessible_states() == {"s", "u", "f", "v", "g"}
    assert dfa.accessible_states() != dfa.coaccessible_states()


@pytest.mark.parametrize("exit_to_final", [False, True])
def test_coaccessible_cycle(exit_to_final: bool) -> None:
    """A cycle is coaccessible exactly when it has an exit to a final."""
    dfa = ExtendedDFA(
        states={0, 1, 2}, input_symbols={"a", "b"},
        transitions={0: {"a": 1},
                     1: {"a": 0, "b": 2} if exit_to_final else {"a": 0},
                     2: {}},
        initial_state=0, final_states={2}, allow_partial=True,
    )
    assert dfa.coaccessible_states() == ({0, 1, 2} if exit_to_final else {2})


@pytest.mark.parametrize("kind", ["dfa", "nfa"])
@pytest.mark.parametrize("final", [False, True])
@pytest.mark.parametrize("state", [0, None])
def test_coaccessible_singleton_and_empty_finals(
    kind: str, final: bool, state: FAStateT,
) -> None:
    """DFA and NFA allow no accepting states, including a None singleton."""
    cls = ExtendedDFA if kind == "dfa" else ExtendedNFA
    automaton = cls(
        states={state}, input_symbols=set(), transitions={state: {}},
        initial_state=state, final_states={state} if final else set(),
    )
    assert automaton.coaccessible_states() == ({state} if final else set())


@pytest.mark.parametrize("with_final", [False, True])
def test_coaccessible_nfa_epsilon_and_parallel_targets(
    with_final: bool,
) -> None:
    """Reverse epsilon paths and parallel edges retain heterogeneous states."""
    pair = (1, "x")
    nfa = ExtendedNFA(
        states={None, 7, pair, "dead"}, input_symbols={"a", "b"},
        transitions={
            None: {"a": {7, "dead"}, "b": {7}},
            7: {"": {pair}}, "dead": {"a": {"dead"}},
        },
        initial_state=None, final_states={pair} if with_final else set(),
    )
    result = nfa.coaccessible_states()
    assert type(result) is frozenset
    assert result == ({None, 7, pair} if with_final else set())
    assert len(result) == (3 if with_final else 0)


@pytest.mark.parametrize("label", [None, "", "a*"])
def test_coaccessible_gnfa_edge_semantics(label: str | None) -> None:
    """None labels are absent edges; None itself can be the final state."""
    gnfa = ExtendedGNFA(
        states={"s", None}, input_symbols={"a"},
        transitions={"s": {None: label}},
        initial_state="s", final_state=None,
    )
    expected: set[FAStateT] = {None} if label is None else {"s", None}
    assert gnfa.coaccessible_states() == expected


def test_coaccessible_immutable_single_scan(automaton: ExtendedFA) -> None:
    """Each fresh query scans once and preserves all slots and caches."""
    attributes = set(vars(automaton))
    for cls in type(automaton).__mro__:
        slots = getattr(cls, "__slots__", ())
        attributes.update([slots] if isinstance(slots, str) else slots)
    attributes -= {"__dict__", "__weakref__"}
    before = deepcopy({name: getattr(automaton, name) for name in attributes})
    dictionary_before = deepcopy(vars(automaton))
    original = type(automaton).iter_transitions
    for _ in range(2):
        with patch.object(
            type(automaton), "iter_transitions", autospec=True,
        ) as scan:
            scan.side_effect = original
            result = automaton.coaccessible_states()
        scan.assert_called_once_with(automaton)
        assert type(result) is frozenset
        assert result == {"f"}
        assert result != automaton.accessible_states()
    assert {name: getattr(automaton, name) for name in attributes} == before
    assert vars(automaton) == dictionary_before
