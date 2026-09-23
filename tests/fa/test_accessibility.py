"""Contracts for accessibility from the initial state across all FA types."""

from copy import deepcopy
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


@pytest.mark.parametrize(
    ("state", "expected"),
    [("f", True), ("s", False), ("a", False),
     ("b", False), ("absent", False)],
)
def test_is_coaccessible_membership(
    automaton: ExtendedFA, state: FAStateT, expected: bool,
) -> None:
    """An isolated final is coaccessible; a reachable cycle is not."""
    result = automaton.is_coaccessible(state)
    assert type(result) is bool
    assert result is expected
    assert result is (state in automaton.coaccessible_states())


def test_is_coaccessible_differs_from_accessibility() -> None:
    """Initial reachability and a path to a final are independent."""
    dfa = ExtendedDFA(
        states={"s", "dead", "unseen", "f"},
        input_symbols={"a"},
        transitions={
            "s": {"a": "dead"}, "dead": {"a": "dead"},
            "unseen": {"a": "f"}, "f": {},
        },
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    assert dfa.is_coaccessible("f") is True
    assert dfa.is_coaccessible("unseen") is True
    assert dfa.is_accessible("unseen") is False
    assert dfa.is_coaccessible("s") is False
    assert dfa.is_coaccessible("dead") is False
    assert dfa.is_accessible("dead") is True


@pytest.mark.parametrize("has_exit", [False, True])
def test_is_coaccessible_cycle_exit(has_exit: bool) -> None:
    """Cycle membership depends on a path to the final, not a loop."""
    dfa = ExtendedDFA(
        states={0, 1, 2}, input_symbols={"a", "b"},
        transitions={0: {"a": 1},
                     1: {"a": 0, "b": 2} if has_exit else {"a": 0},
                     2: {}},
        initial_state=0, final_states={2}, allow_partial=True,
    )
    assert dfa.is_coaccessible(0) is has_exit
    assert dfa.is_coaccessible(1) is has_exit
    assert dfa.is_coaccessible(2) is True


def test_is_coaccessible_nfa_epsilon_and_multiple_targets() -> None:
    """Epsilon edges and multiple targets affect set membership."""
    nfa = ExtendedNFA(
        states={0, 1, 2, 3}, input_symbols={"a"},
        transitions={0: {"a": {1, 3}}, 1: {"": {2}},
                     3: {"a": {3}}},
        initial_state=0, final_states={2},
    )
    for state, expected in [(0, True), (1, True), (2, True), (3, False)]:
        assert nfa.is_coaccessible(state) is expected
        assert nfa.is_coaccessible(state) is (
            state in nfa.coaccessible_states()
        )


@pytest.mark.parametrize("label", [None, "", "a*"])
def test_is_coaccessible_gnfa_and_valid_none(label: str | None) -> None:
    """A None final is valid; only an actual GNFA edge reaches it."""
    gnfa = ExtendedGNFA(
        states={"s", None}, input_symbols={"a"},
        transitions={"s": {None: label}},
        initial_state="s", final_state=None,
    )
    assert gnfa.is_coaccessible(None) is True
    assert gnfa.is_coaccessible("s") is (label is not None)
    assert gnfa.is_coaccessible("absent") is False


def test_is_coaccessible_empty_final_set() -> None:
    """With no accepting state, even the initial state fails the predicate."""
    dfa = ExtendedDFA(
        states={None}, input_symbols=set(), transitions={None: {}},
        initial_state=None, final_states=set(),
    )
    assert dfa.is_coaccessible(None) is False


def test_is_coaccessible_unhashable_matches_existing_predicate(
    automaton: ExtendedFA,
) -> None:
    """Both predicates retain frozenset's native TypeError for a list."""
    with pytest.raises(TypeError):
        automaton.is_accessible(["f"])
    with pytest.raises(TypeError):
        automaton.is_coaccessible(["f"])


def test_is_coaccessible_delegates_once(automaton: ExtendedFA) -> None:
    """The predicate calls the verified set query once per invocation."""
    original = type(automaton).coaccessible_states
    with patch.object(
        type(automaton), "coaccessible_states", autospec=True,
    ) as query:
        query.side_effect = original
        assert automaton.is_coaccessible("f") is True
    query.assert_called_once_with(automaton)


def test_is_coaccessible_preserves_source(automaton: ExtendedFA) -> None:
    """Repeated boolean queries leave all instance attributes unchanged."""
    attributes = set(vars(automaton))
    for cls in type(automaton).__mro__:
        slots = getattr(cls, "__slots__", ())
        attributes.update([slots] if isinstance(slots, str) else slots)
    attributes -= {"__dict__", "__weakref__"}
    before = deepcopy({name: getattr(automaton, name) for name in attributes})
    dictionary_before = deepcopy(vars(automaton))
    for _ in range(2):
        assert automaton.is_coaccessible("f") is True
        assert automaton.is_coaccessible("s") is False
    assert {name: getattr(automaton, name) for name in attributes} == before
    assert vars(automaton) == dictionary_before


def test_useful_states_separates_all_four_state_categories() -> None:
    """The three sets differ, and a state in neither set is excluded."""
    dfa = ExtendedDFA(
        states={"s", "path", "f", "dead", "unseen", "neither"},
        input_symbols={"a", "b"},
        transitions={
            "s": {"a": "path", "b": "dead"},
            "path": {"a": "f"}, "f": {},
            "dead": {"a": "dead"},
            "unseen": {"a": "f"}, "neither": {},
        },
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    accessible = dfa.accessible_states()
    coaccessible = dfa.coaccessible_states()
    useful = dfa.useful_states()
    assert accessible == {"s", "path", "f", "dead"}
    assert coaccessible == {"s", "path", "f", "unseen"}
    assert useful == {"s", "path", "f"}
    assert useful == accessible & coaccessible
    assert len({accessible, coaccessible, useful}) == 3
    assert type(useful) is frozenset


@pytest.mark.parametrize("has_exit", [False, True])
def test_useful_states_cycle_with_or_without_final_exit(
    has_exit: bool,
) -> None:
    """A reachable cycle contributes only if it can lead to a final."""
    dfa = ExtendedDFA(
        states={0, 1, 2}, input_symbols={"a", "b"},
        transitions={
            0: {"a": 1},
            1: {"a": 0, "b": 2} if has_exit else {"a": 0},
            2: {},
        },
        initial_state=0, final_states={2}, allow_partial=True,
    )
    assert dfa.useful_states() == ({0, 1, 2} if has_exit else set())


def test_useful_states_empty_when_final_is_inaccessible(
    automaton: ExtendedFA,
) -> None:
    """An isolated final and the initial state may both be non-useful."""
    assert automaton.initial_state in automaton.accessible_states()
    assert "f" in automaton.coaccessible_states()
    assert "f" not in automaton.accessible_states()
    assert automaton.useful_states() == frozenset()
    assert type(automaton.useful_states()) is frozenset


@pytest.mark.parametrize("kind", ["dfa", "nfa"])
def test_useful_states_empty_without_final_states(kind: str) -> None:
    """No accepting state yields an empty useful set in DFA and NFA."""
    cls = ExtendedDFA if kind == "dfa" else ExtendedNFA
    automaton = cls(
        states={"s"}, input_symbols=set(), transitions={"s": {}},
        initial_state="s", final_states=set(),
    )
    assert automaton.useful_states() == frozenset()


@pytest.mark.parametrize("kind", ["dfa", "nfa"])
@pytest.mark.parametrize("state", [0, None])
def test_useful_states_single_initial_final(
    kind: str, state: FAStateT,
) -> None:
    """The zero-length path makes an accepting singleton useful."""
    cls = ExtendedDFA if kind == "dfa" else ExtendedNFA
    automaton = cls(
        states={state}, input_symbols=set(), transitions={state: {}},
        initial_state=state, final_states={state},
    )
    assert automaton.useful_states() == frozenset({state})


def test_useful_states_nfa_epsilon_with_heterogeneous_states() -> None:
    """Epsilon paths compose with accessibility without sorting states."""
    final = (1, "final")
    nfa = ExtendedNFA(
        states={None, 7, final, "dead", "unseen"},
        input_symbols={"a"},
        transitions={
            None: {"": {7, "dead"}},
            7: {"": {final}},
            "dead": {"a": {"dead"}},
            "unseen": {"a": {final}},
        },
        initial_state=None, final_states={final},
    )
    result = nfa.useful_states()
    assert result == {None, 7, final}
    assert result == nfa.accessible_states() & nfa.coaccessible_states()
    assert type(result) is frozenset


@pytest.mark.parametrize("label", [None, "", "a*"])
def test_useful_states_gnfa_present_and_absent_edges(
    label: str | None,
) -> None:
    """GNFA epsilon is an edge; a None label is no path to its final."""
    gnfa = ExtendedGNFA(
        states={"s", None}, input_symbols={"a"},
        transitions={"s": {None: label}},
        initial_state="s", final_state=None,
    )
    expected: set[FAStateT] = set() if label is None else {"s", None}
    assert gnfa.useful_states() == expected
    assert gnfa.useful_states() == (
        gnfa.accessible_states() & gnfa.coaccessible_states()
    )


def test_useful_states_delegates_once_to_each_set_query(
    automaton: ExtendedFA,
) -> None:
    """Composition asks each verified set query once without new traversal."""
    original_accessible = type(automaton).accessible_states
    original_coaccessible = type(automaton).coaccessible_states
    with (
        patch.object(
            type(automaton), "accessible_states", autospec=True,
        ) as accessible,
        patch.object(
            type(automaton), "coaccessible_states", autospec=True,
        ) as coaccessible,
    ):
        accessible.side_effect = original_accessible
        coaccessible.side_effect = original_coaccessible
        assert automaton.useful_states() == frozenset()
    accessible.assert_called_once_with(automaton)
    coaccessible.assert_called_once_with(automaton)


def test_useful_states_preserves_source_and_inputs(
    automaton: ExtendedFA,
) -> None:
    """Intersection returns a frozen set without changing instance state."""
    attributes = set(vars(automaton))
    for cls in type(automaton).__mro__:
        slots = getattr(cls, "__slots__", ())
        attributes.update([slots] if isinstance(slots, str) else slots)
    attributes -= {"__dict__", "__weakref__"}
    before = deepcopy({name: getattr(automaton, name) for name in attributes})
    dictionary_before = deepcopy(vars(automaton))
    accessible = automaton.accessible_states()
    coaccessible = automaton.coaccessible_states()

    for _ in range(2):
        result = automaton.useful_states()
        assert type(result) is frozenset
        assert result == accessible & coaccessible

    assert accessible == automaton.accessible_states()
    assert coaccessible == automaton.coaccessible_states()
    assert {name: getattr(automaton, name) for name in attributes} == before
    assert vars(automaton) == dictionary_before


@pytest.fixture(params=["dfa", "nfa", "gnfa"])
def trim_candidate(
    request: pytest.FixtureRequest,
) -> ExtendedDFA | ExtendedNFA | ExtendedGNFA:
    """A nonempty accepting path with one reachable non-useful state."""
    states = {"s", "f", "dead"}
    if request.param == "dfa":
        return ExtendedDFA(
            states=states, input_symbols={"a", "b"},
            transitions={
                "s": {"a": "f", "b": "dead"},
                "f": {"a": "f", "b": "dead"},
                "dead": {"a": "dead", "b": "dead"},
            },
            initial_state="s", final_states={"f"},
        )
    if request.param == "nfa":
        return ExtendedNFA(
            states=states, input_symbols={"a"},
            transitions={"s": {"": {"f", "dead"}},
                         "dead": {"a": {"dead"}}},
            initial_state="s", final_states={"f"},
        )
    return ExtendedGNFA(
        states=states, input_symbols={"a"},
        transitions={
            "s": {"f": "a", "dead": "a"},
            "dead": {"f": None, "dead": "a"},
        },
        initial_state="s", final_state="f",
    )


@pytest.mark.parametrize("kind", ["dfa", "nfa", "gnfa"])
def test_is_trim_all_states_useful(kind: str) -> None:
    """A direct accepting path leaves no irrelevant state."""
    if kind == "dfa":
        automaton: ExtendedDFA | ExtendedNFA | ExtendedGNFA = ExtendedDFA(
            states={"s", "f"}, input_symbols={"a"},
            transitions={"s": {"a": "f"}, "f": {"a": "f"}},
            initial_state="s", final_states={"f"},
        )
    elif kind == "nfa":
        automaton = ExtendedNFA(
            states={"s", "f"}, input_symbols={"a"},
            transitions={"s": {"": {"f"}}},
            initial_state="s", final_states={"f"},
        )
    else:
        automaton = ExtendedGNFA(
            states={"s", "f"}, input_symbols={"a"},
            transitions={"s": {"f": "a"}},
            initial_state="s", final_state="f",
        )
    assert automaton.is_trim() is True
    assert type(automaton.is_trim()) is bool
    assert automaton.is_trim() is (
        automaton.states == automaton.useful_states()
    )


def test_is_trim_excludes_each_kind_of_nonuseful_state() -> None:
    """Accessible-only, coaccessible-only, and neither all fail trimness."""
    dfa = ExtendedDFA(
        states={"s", "f", "dead", "unseen", "neither"},
        input_symbols={"a", "b"},
        transitions={
            "s": {"a": "f", "b": "dead"},
            "f": {}, "dead": {"a": "dead"},
            "unseen": {"a": "f"}, "neither": {},
        },
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    assert dfa.accessible_states() == {"s", "f", "dead"}
    assert dfa.coaccessible_states() == {"s", "f", "unseen"}
    assert dfa.useful_states() == {"s", "f"}
    assert dfa.is_trim() is False


@pytest.mark.parametrize("kind", ["dfa", "nfa"])
@pytest.mark.parametrize("final", [False, True])
@pytest.mark.parametrize("state", [0, None])
def test_is_trim_singleton(
    kind: str, final: bool, state: FAStateT,
) -> None:
    """The zero-length path helps only an accepting singleton."""
    cls = ExtendedDFA if kind == "dfa" else ExtendedNFA
    automaton = cls(
        states={state}, input_symbols=set(), transitions={state: {}},
        initial_state=state, final_states={state} if final else set(),
    )
    assert automaton.is_trim() is final
    assert type(automaton.is_trim()) is bool


@pytest.mark.parametrize("has_exit", [False, True])
def test_is_trim_cycle_needs_final_exit(has_exit: bool) -> None:
    """A reachable cycle is useful only with a path to the final."""
    dfa = ExtendedDFA(
        states={0, 1, 2}, input_symbols={"a", "b"},
        transitions={0: {"a": 1},
                     1: {"a": 0, "b": 2} if has_exit else {"a": 0},
                     2: {}},
        initial_state=0, final_states={2}, allow_partial=True,
    )
    assert dfa.is_trim() is has_exit


def test_is_trim_partially_defined_dfa() -> None:
    """Missing symbol edges do not prevent a partial DFA being trim."""
    dfa = ExtendedDFA(
        states={"s", "f"}, input_symbols={"a", "b"},
        transitions={"s": {"a": "f"}, "f": {}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    assert dfa.is_trim() is True


@pytest.mark.parametrize("with_dead", [False, True])
def test_is_trim_nfa_epsilon_heterogeneous_none(with_dead: bool) -> None:
    """None and unorderable states work through epsilon transitions."""
    final = (1, "f")
    states: set[FAStateT] = {None, 7, final}
    transitions: dict[FAStateT, dict[str, set[FAStateT]]] = {
        None: {"": {7}}, 7: {"a": {final}},
    }
    if with_dead:
        states.add("dead")
        transitions[None][""].add("dead")
        transitions["dead"] = {"a": {"dead"}}
    nfa = ExtendedNFA(
        states=states, input_symbols={"a"}, transitions=transitions,
        initial_state=None, final_states={final},
    )
    assert nfa.is_trim() is (not with_dead)
    assert nfa.is_trim() is (nfa.states == nfa.useful_states())


@pytest.mark.parametrize("label", [None, "", "a*"])
def test_is_trim_gnfa_none_final_state(label: str | None) -> None:
    """A None-valued state is valid; a None-labelled cell is not an edge."""
    gnfa = ExtendedGNFA(
        states={"s", None}, input_symbols={"a"},
        transitions={"s": {None: label}},
        initial_state="s", final_state=None,
    )
    assert gnfa.is_trim() is (label is not None)


def test_is_trim_of_nonempty_trim_result(
    trim_candidate: ExtendedDFA | ExtendedNFA | ExtendedGNFA,
) -> None:
    """A nonempty-language trim result has only useful states."""
    assert trim_candidate.is_trim() is False
    trimmed = trim_candidate.trim()
    assert trimmed.useful_states() == trimmed.states == {"s", "f"}
    assert trimmed.is_trim() is True


def test_is_trim_of_empty_trim_result(automaton: ExtendedFA) -> None:
    """Mandatory structural states remain non-useful for empty language."""
    assert isinstance(automaton, (ExtendedDFA, ExtendedNFA, ExtendedGNFA))
    assert automaton.useful_states() == frozenset()
    trimmed = automaton.trim()
    assert trimmed.states
    assert trimmed.useful_states() == frozenset()
    assert trimmed.is_trim() is False
    assert trimmed.is_trim() is (
        trimmed.states == trimmed.useful_states()
    )


def test_is_trim_delegates_once(
    trim_candidate: ExtendedDFA | ExtendedNFA | ExtendedGNFA,
) -> None:
    """Use the existing set query once without a local traversal."""
    original = type(trim_candidate).useful_states
    with patch.object(
        type(trim_candidate), "useful_states", autospec=True,
    ) as query:
        query.side_effect = original
        assert trim_candidate.is_trim() is False
    query.assert_called_once_with(trim_candidate)


def test_is_trim_preserves_source(
    trim_candidate: ExtendedDFA | ExtendedNFA | ExtendedGNFA,
) -> None:
    """Repeated predicate calls leave all instance attributes untouched."""
    attributes = set(vars(trim_candidate))
    for cls in type(trim_candidate).__mro__:
        slots = getattr(cls, "__slots__", ())
        attributes.update([slots] if isinstance(slots, str) else slots)
    attributes -= {"__dict__", "__weakref__"}
    before = deepcopy({
        name: getattr(trim_candidate, name) for name in attributes
    })
    dictionary_before = deepcopy(vars(trim_candidate))
    for _ in range(2):
        assert trim_candidate.is_trim() is False
    assert {
        name: getattr(trim_candidate, name) for name in attributes
    } == before
    assert vars(trim_candidate) == dictionary_before


def test_reachable_from_initial_matches_accessible_states(
    automaton: ExtendedFA,
) -> None:
    """The initial-state specialization agrees across DFA, NFA and GNFA."""
    result = automaton.reachable_states(automaton.initial_state)
    assert type(result) is frozenset
    assert result == automaton.accessible_states()
    assert result == frozenset({"s", "a", "b"})
    assert len(result) == len(automaton.dfs(automaton.initial_state))


def test_reachable_from_isolated_final_includes_start(
    automaton: ExtendedFA,
) -> None:
    """A zero-edge path includes a state unreachable from the initial one."""
    assert "f" not in automaton.accessible_states()
    assert automaton.reachable_states("f") == frozenset({"f"})


@pytest.mark.parametrize(
    ("start", "expected"),
    [("q0", {"q0", "q1", "q2"}), ("q1", {"q1", "q2"}), ("q2", {"q2"})],
)
def test_reachable_dfa_chain_from_each_state(
    start: str, expected: set[str]
) -> None:
    dfa = ExtendedDFA(
        states={"q0", "q1", "q2", "isolated"},
        input_symbols={"a"},
        transitions={"q0": {"a": "q1"}, "q1": {"a": "q2"},
                     "q2": {}, "isolated": {}},
        initial_state="q0", final_states={"q2"}, allow_partial=True,
    )
    result = dfa.reachable_states(start)
    assert result == frozenset(expected)
    assert start in result
    assert "isolated" not in result


def test_reachable_dfa_branching_self_loop_and_cycle() -> None:
    dfa = ExtendedDFA(
        states={"s", "a", "b", "other"}, input_symbols={"0", "1"},
        transitions={
            "s": {"0": "a", "1": "other"},
            "a": {"0": "a", "1": "b"},
            "b": {"0": "a"},
            "other": {},
        },
        initial_state="s", final_states={"b"}, allow_partial=True,
    )
    assert dfa.reachable_states("a") == frozenset({"a", "b"})
    assert dfa.reachable_states("other") == frozenset({"other"})
    assert dfa.reachable_states("s") == dfa.states


def test_reachable_in_component_inaccessible_from_initial() -> None:
    dfa = ExtendedDFA(
        states={"q0", "q1", "x", "y"}, input_symbols={"a"},
        transitions={
            "q0": {"a": "q1"}, "q1": {},
            "x": {"a": "y"}, "y": {"a": "x"},
        },
        initial_state="q0", final_states={"q1"}, allow_partial=True,
    )
    assert dfa.accessible_states() == frozenset({"q0", "q1"})
    assert dfa.reachable_states("x") == frozenset({"x", "y"})


@pytest.mark.parametrize("invalid", ["missing", ["unhashable"]])
def test_reachable_invalid_state_matches_dfs(
    automaton: ExtendedFA, invalid: FAStateT
) -> None:
    with pytest.raises(InvalidStateError):
        automaton.dfs(invalid)
    with pytest.raises(InvalidStateError):
        automaton.reachable_states(invalid)


def test_reachable_nfa_multiple_destinations_and_epsilon_cycle() -> None:
    nfa = ExtendedNFA(
        states={0, 1, 2, 3, 4}, input_symbols={"a"},
        transitions={
            0: {"a": {1, 2}},
            1: {"": {3}},
            2: {"": {3}},
            3: {"a": {1}},
        },
        initial_state=0, final_states={3},
    )
    assert nfa.reachable_states(0) == frozenset({0, 1, 2, 3})
    assert nfa.reachable_states(2) == frozenset({1, 2, 3})
    assert nfa.reachable_states(1) == frozenset({1, 3})
    assert 4 not in nfa.reachable_states(0)


@pytest.mark.parametrize(
    ("label", "expected"),
    [(None, {"s"}), ("", {"s", "f"}), ("a*", {"s", "f"})],
)
def test_reachable_gnfa_respects_absent_and_present_edges(
    label: str | None, expected: set[str]
) -> None:
    gnfa = ExtendedGNFA(
        states={"s", "f"}, input_symbols={"a"},
        transitions={"s": {"f": label}},
        initial_state="s", final_state="f",
    )
    assert gnfa.reachable_states("s") == frozenset(expected)
    assert gnfa.reachable_states("f") == frozenset({"f"})


def test_reachable_none_and_heterogeneous_states() -> None:
    pair = (1, "x")
    frozen = frozenset({2})
    nfa = ExtendedNFA(
        states={"initial", None, 7, pair, frozen}, input_symbols={"a"},
        transitions={"initial": {}, None: {"a": {7, frozen}}, 7: {"": {pair}},
                     frozen: {"": {pair}}},
        initial_state="initial", final_states={pair},
    )
    result = nfa.reachable_states(None)
    assert type(result) is frozenset
    assert result == frozenset({None, 7, pair, frozen})
    assert "initial" not in result
    assert result == frozenset(nfa.dfs(None))


def test_reachable_states_preserves_source(automaton: ExtendedFA) -> None:
    states = deepcopy(automaton.states)
    transitions = deepcopy(automaton.transitions)
    final_states = deepcopy(automaton.final_states)
    input_symbols = deepcopy(automaton.input_symbols)
    for start in (automaton.initial_state, "a", "f"):
        automaton.reachable_states(start)
    assert automaton.states == states
    assert automaton.transitions == transitions
    assert automaton.final_states == final_states
    assert automaton.input_symbols == input_symbols
