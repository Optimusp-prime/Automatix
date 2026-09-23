"""Direct predecessor queries on the common transition graph."""

from copy import deepcopy

import pytest
from automata.base.exceptions import InvalidStateError
from automata.fa.dfa import DFA
from automata.fa.fa import FAStateT

from automata_extensions.fa import ExtendedDFA, ExtendedFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.fa_mixins.graph import GraphMixin


@pytest.fixture(params=["dfa", "nfa", "gnfa"])
def automaton(request: pytest.FixtureRequest) -> ExtendedFA:
    """A valid two-state graph with one incoming edge to its final state."""
    if request.param == "dfa":
        return ExtendedDFA(
            states={"s", "f"}, input_symbols={"a"},
            transitions={"s": {"a": "f"}, "f": {}},
            initial_state="s", final_states={"f"}, allow_partial=True,
        )
    if request.param == "nfa":
        return ExtendedNFA(
            states={"s", "f"}, input_symbols={"a"},
            transitions={"s": {"a": {"f"}}},
            initial_state="s", final_states={"f"},
        )
    return ExtendedGNFA(
        states={"s", "f"}, input_symbols={"a"},
        transitions={"s": {"f": "a"}},
        initial_state="s", final_state="f",
    )


def test_one_direct_predecessor_and_no_incoming_edge(
    automaton: ExtendedFA,
) -> None:
    result = automaton.predecessors_graph("f")
    assert type(result) is frozenset
    assert result == frozenset({"s"})
    assert automaton.predecessors_graph("s") == frozenset()


def test_dfa_multiple_predecessors_excludes_indirect_ancestor() -> None:
    dfa = ExtendedDFA(
        states={"q0", "q1", "q2", "q3"}, input_symbols={"a", "b"},
        transitions={
            "q0": {"a": "q2"},
            "q1": {"b": "q2"},
            "q2": {},
            "q3": {"a": "q1"},
        },
        initial_state="q0", final_states={"q2"}, allow_partial=True,
    )
    assert dfa.predecessors_graph("q2") == frozenset({"q0", "q1"})
    assert "q3" not in dfa.predecessors_graph("q2")
    assert dfa.predecessors_graph("q1") == frozenset({"q3"})
    assert "q1" not in dfa.accessible_states()


def test_parallel_dfa_edges_and_self_loop_are_unique_states() -> None:
    dfa = ExtendedDFA(
        states={"s", "q"}, input_symbols={"a", "b"},
        transitions={"s": {"a": "q", "b": "q"}, "q": {"a": "q"}},
        initial_state="s", final_states={"q"}, allow_partial=True,
    )
    result = dfa.predecessors_graph("q")
    assert result == frozenset({"s", "q"})
    assert len(result) == 2


@pytest.mark.parametrize("with_loop", [False, True])
def test_singleton_with_or_without_self_loop(with_loop: bool) -> None:
    dfa = ExtendedDFA(
        states={"q"}, input_symbols={"a"} if with_loop else set(),
        transitions={"q": {"a": "q"} if with_loop else {}},
        initial_state="q", final_states={"q"},
    )
    expected = frozenset({"q"}) if with_loop else frozenset()
    assert dfa.predecessors_graph("q") == expected


def test_cycle_returns_only_immediate_incoming_neighbor() -> None:
    dfa = ExtendedDFA(
        states={0, 1, 2}, input_symbols={"a"},
        transitions={0: {"a": 1}, 1: {"a": 2}, 2: {"a": 0}},
        initial_state=0, final_states={2},
    )
    assert dfa.predecessors_graph(0) == frozenset({2})
    assert dfa.predecessors_graph(2) == frozenset({1})


def test_nfa_multiple_destinations_and_epsilon_edges() -> None:
    nfa = ExtendedNFA(
        states={"s", "p", "q", "f"}, input_symbols={"a"},
        transitions={
            "s": {"a": {"p", "q"}},
            "p": {"": {"q", "f"}},
            "q": {"a": {"f"}},
        },
        initial_state="s", final_states={"f"},
    )
    assert nfa.predecessors_graph("q") == frozenset({"s", "p"})
    assert nfa.predecessors_graph("f") == frozenset({"p", "q"})
    assert "s" not in nfa.predecessors_graph("f")


@pytest.mark.parametrize("label", [None, "", "a*"])
def test_gnfa_absent_and_present_edges(label: str | None) -> None:
    gnfa = ExtendedGNFA(
        states={"s", "x", "f"}, input_symbols={"a"},
        transitions={
            "s": {"x": label, "f": None},
            "x": {"x": None, "f": "a"},
        },
        initial_state="s", final_state="f",
    )
    assert gnfa.predecessors_graph("x") == (
        frozenset() if label is None else frozenset({"s"})
    )
    assert gnfa.predecessors_graph("f") == frozenset({"x"})


@pytest.mark.parametrize("invalid", ["absent", ["unhashable"]])
def test_invalid_state_matches_common_graph_contract(
    automaton: ExtendedFA, invalid: FAStateT
) -> None:
    with pytest.raises(InvalidStateError):
        automaton.dfs(invalid)
    with pytest.raises(InvalidStateError):
        automaton.predecessors_graph(invalid)


def test_none_and_heterogeneous_state_predecessors() -> None:
    pair = (1, "x")
    frozen = frozenset({2})
    nfa = ExtendedNFA(
        states={"start", None, 7, pair, frozen}, input_symbols={"a"},
        transitions={
            "start": {},
            7: {"a": {None}},
            frozen: {"": {None}},
            None: {"a": {pair}},
        },
        initial_state="start", final_states={pair},
    )
    assert nfa.predecessors_graph(None) == frozenset({7, frozen})
    assert nfa.predecessors_graph(pair) == frozenset({None})
    assert nfa.predecessors_graph("start") == frozenset()


def test_upstream_word_predecessors_is_not_shadowed() -> None:
    dfa = ExtendedDFA(
        states={"s", "f"}, input_symbols={"a", "b"},
        transitions={"s": {"a": "f"}, "f": {}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    assert ExtendedDFA.predecessors is DFA.predecessors
    assert all(isinstance(word, str) for word in dfa.predecessors("b"))
    assert dfa.predecessors_graph("f") == frozenset({"s"})


def test_graph_mixin_is_common_and_source_is_unchanged(
    automaton: ExtendedFA,
) -> None:
    assert GraphMixin in type(automaton).__mro__
    original = (
        deepcopy(automaton.states),
        deepcopy(automaton.transitions),
        deepcopy(automaton.final_states),
        deepcopy(automaton.input_symbols),
    )
    for state in automaton.states:
        automaton.predecessors_graph(state)
    assert (
        automaton.states,
        automaton.transitions,
        automaton.final_states,
        automaton.input_symbols,
    ) == original
