"""Additional mature graph-neighborhood and SCC compatibility APIs."""

from copy import deepcopy

import pytest
from automata.base.exceptions import InvalidStateError

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from tests.fa.test_state_elimination import _mature_dfa


def test_mature_direct_neighbors_and_connectivity() -> None:
    d = _mature_dfa()
    assert (
        d.predecessors_graph("1"), d.successors_graph("1")
    ) == (frozenset({"0", "1"}), frozenset({"1", "2"}))
    assert set(d.strongly_connected_components()) == {
        frozenset({"0", "1", "2"})
    }
    assert d.is_strongly_connected() is True


def test_successors_collapse_parallel_edges_and_include_loop() -> None:
    d = ExtendedDFA(
        states={"s", "q", "end"}, input_symbols={"a", "b", "c"},
        transitions={"s": {"a": "q", "b": "q", "c": "s"},
                     "q": {"a": "end"}, "end": {}},
        initial_state="s", final_states={"end"}, allow_partial=True,
    )
    before = deepcopy(d.input_parameters)
    assert d.successors_graph("s") == frozenset({"s", "q"})
    assert d.successors_graph("end") == frozenset()
    assert d.is_strongly_connected() is False
    assert d.input_parameters == before


def test_nfa_epsilon_and_gnfa_absent_cells() -> None:
    n = ExtendedNFA(
        states={"s", "p", "f"}, input_symbols={"a"},
        transitions={"s": {"": {"p"}, "a": {"p", "f"}},
                     "p": {"a": {"f"}}},
        initial_state="s", final_states={"f"},
    )
    g = ExtendedGNFA(
        states={"s", "x", "f"}, input_symbols={"a"},
        transitions={"s": {"x": "a", "f": None},
                     "x": {"x": None, "f": "a"}},
        initial_state="s", final_state="f",
    )
    assert n.successors_graph("s") == frozenset({"p", "f"})
    assert n.successors_graph("f") == frozenset()
    assert g.successors_graph("s") == frozenset({"x"})
    assert g.successors_graph("x") == frozenset({"f"})
    assert not n.is_strongly_connected()
    assert not g.is_strongly_connected()


def test_none_state_and_invalid_state_policy() -> None:
    d = ExtendedDFA(
        states={None}, input_symbols={"a"}, transitions={None: {"a": None}},
        initial_state=None, final_states={None},
    )
    assert d.successors_graph(None) == frozenset({None})
    assert d.is_strongly_connected() is True
    with pytest.raises(InvalidStateError):
        d.successors_graph("absent")
    with pytest.raises(InvalidStateError):
        d.successors_graph([])


def test_singleton_without_edge_is_strongly_connected() -> None:
    n = ExtendedNFA(
        states={"q"}, input_symbols=set(), transitions={"q": {}},
        initial_state="q", final_states=set(),
    )
    assert n.is_strongly_connected() is True
