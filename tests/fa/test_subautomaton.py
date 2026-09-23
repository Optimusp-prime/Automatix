"""Exact-state induced subautomata for the three Extended FA types."""

from copy import deepcopy
from typing import Iterator

import pytest
from automata.base.exceptions import InvalidStateError

from automata_extensions.fa import ExtendedDFA, ExtendedFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.fa_mixins.subautomaton import SubautomatonMixin


@pytest.fixture(params=["dfa", "nfa", "gnfa"])
def automaton(request: pytest.FixtureRequest) -> ExtendedFA:
    """A graph with one removable internal state and a retained final."""
    if request.param == "dfa":
        return ExtendedDFA(
            states={"s", "x", "f"}, input_symbols={"a", "b"},
            transitions={
                "s": {"a": "x", "b": "f"},
                "x": {"a": "f", "b": "x"},
                "f": {"a": "f", "b": "f"},
            },
            initial_state="s", final_states={"f"},
        )
    if request.param == "nfa":
        return ExtendedNFA(
            states={"s", "x", "f"}, input_symbols={"a", "b"},
            transitions={
                "s": {"a": {"x", "f"}, "": {"x"}},
                "x": {"b": {"f"}},
            },
            initial_state="s", final_states={"f"},
        )
    return ExtendedGNFA(
        states={"s", "x", "f"}, input_symbols={"a", "b"},
        transitions={
            "s": {"x": "a", "f": "b"},
            "x": {"x": None, "f": "a*"},
        },
        initial_state="s", final_state="f",
    )


def test_full_set_returns_fresh_same_extended_type(
    automaton: ExtendedFA,
) -> None:
    result = automaton.induced_subautomaton(automaton.states)
    assert result is not automaton
    assert type(result) is type(automaton)
    assert result.states == frozenset(automaton.states)
    assert result.transitions == automaton.transitions
    assert result.input_symbols == automaton.input_symbols
    assert result.final_states == automaton.final_states
    assert SubautomatonMixin in type(result).__mro__


def test_subset_is_exact_and_composable(automaton: ExtendedFA) -> None:
    requested = frozenset({"s", "f"})
    result = automaton.induced_subautomaton(requested)
    assert result is not automaton
    assert type(result) is type(automaton)
    assert result.states == requested
    assert result.initial_state == "s"
    assert result.final_states == frozenset({"f"})
    assert result.input_symbols == automaton.input_symbols
    assert result.dfs() == ["s", "f"]
    assert result.accessible_states() == requested
    assert result.reachable_states("f") == frozenset({"f"})
    assert result.is_empty() is False


def test_unknown_state_is_rejected(automaton: ExtendedFA) -> None:
    with pytest.raises(InvalidStateError, match="unknown states"):
        automaton.induced_subautomaton({"s", "f", "unknown"})


@pytest.mark.parametrize("requested", [set(), {"x", "f"}])
def test_empty_or_missing_initial_is_rejected(
    automaton: ExtendedFA, requested: set[str]
) -> None:
    with pytest.raises(InvalidStateError, match="initial state"):
        automaton.induced_subautomaton(requested)


def test_unhashable_state_is_rejected(automaton: ExtendedFA) -> None:
    with pytest.raises(InvalidStateError, match="hashable"):
        automaton.induced_subautomaton(["s", ["not a state"]])


def test_generator_is_consumed_once(automaton: ExtendedFA) -> None:
    yielded: list[str] = []

    def requested_states() -> Iterator[str]:
        for state in ("s", "f"):
            yielded.append(state)
            yield state

    result = automaton.induced_subautomaton(requested_states())
    assert yielded == ["s", "f"]
    assert result.states == frozenset({"s", "f"})


def test_dfa_filters_both_transition_endpoints_and_becomes_partial() -> None:
    dfa = ExtendedDFA(
        states={"s", "keep", "drop"}, input_symbols={"0", "1"},
        transitions={
            "s": {"0": "keep", "1": "drop"},
            "keep": {"0": "keep", "1": "drop"},
            "drop": {"0": "keep", "1": "drop"},
        },
        initial_state="s", final_states={"keep", "drop"},
    )
    result = dfa.induced_subautomaton({"s", "keep"})
    assert type(result) is ExtendedDFA
    assert result.states == frozenset({"s", "keep"})
    assert result.transitions == {"s": {"0": "keep"}, "keep": {"0": "keep"}}
    assert result.final_states == frozenset({"keep"})
    assert dfa.allow_partial is False
    assert result.allow_partial is True
    assert result.accepts("0") is True
    assert result.accepts("1") is False


@pytest.mark.parametrize("initial_final", [False, True])
def test_dfa_singleton_keeps_self_loop_and_finality(initial_final: bool) -> None:
    dfa = ExtendedDFA(
        states={"s", "out"}, input_symbols={"a", "b"},
        transitions={"s": {"a": "s", "b": "out"},
                     "out": {"a": "out", "b": "out"}},
        initial_state="s",
        final_states={"s", "out"} if initial_final else {"out"},
    )
    result = dfa.induced_subautomaton({"s"})
    assert result.states == frozenset({"s"})
    assert result.transitions == {"s": {"a": "s"}}
    assert result.final_states == (frozenset({"s"}) if initial_final else frozenset())
    assert result.allow_partial is True


def test_nfa_filters_destinations_and_epsilon_without_closure() -> None:
    nfa = ExtendedNFA(
        states={"s", "keep", "drop", "f"}, input_symbols={"a"},
        transitions={
            "s": {"a": {"keep", "drop"}, "": {"keep", "drop"}},
            "keep": {"": {"f", "drop"}},
            "drop": {"a": {"f"}},
        },
        initial_state="s", final_states={"f", "drop"},
    )
    result = nfa.induced_subautomaton({"s", "keep", "f"})
    assert type(result) is ExtendedNFA
    assert result.transitions == {
        "s": {"a": {"keep"}, "": {"keep"}},
        "keep": {"": {"f"}},
    }
    assert result.final_states == frozenset({"f"})
    assert result.dfs() == ["s", "keep", "f"]


def test_nfa_empty_destination_set_remains_valid() -> None:
    nfa = ExtendedNFA(
        states={"s", "out"}, input_symbols={"a"},
        transitions={"s": {"a": {"out"}, "": {"out"}}},
        initial_state="s", final_states={"out"},
    )
    result = nfa.induced_subautomaton({"s"})
    assert result.states == frozenset({"s"})
    assert result.transitions == {"s": {"a": frozenset(), "": frozenset()}}
    assert result.final_states == frozenset()
    assert result.is_empty() is True


def test_gnfa_rebuilds_dense_table_and_preserves_internal_labels() -> None:
    gnfa = ExtendedGNFA(
        states={"s", "x", "y", "f"}, input_symbols={"a", "b"},
        transitions={
            "s": {"x": "a", "y": None, "f": None},
            "x": {"x": "a*", "y": "b", "f": "a|b"},
            "y": {"x": "a", "y": None, "f": "b"},
        },
        initial_state="s", final_state="f",
    )
    result = gnfa.induced_subautomaton({"s", "x", "f"})
    assert type(result) is ExtendedGNFA
    assert result.states == frozenset({"s", "x", "f"})
    assert result.transitions == {
        "s": {"x": "a", "f": None},
        "x": {"x": "a*", "f": "a|b"},
    }
    assert result.final_state == "f"
    assert result.final_states == frozenset({"f"})


def test_gnfa_missing_final_state_is_rejected() -> None:
    automaton = ExtendedGNFA(
        states={"s", "x", "f"}, input_symbols={"a"},
        transitions={"s": {"x": "a", "f": None},
                     "x": {"x": None, "f": "a"}},
        initial_state="s", final_state="f",
    )
    with pytest.raises(InvalidStateError, match="GNFA final state"):
        automaton.induced_subautomaton({"s", "x"})


def test_none_and_heterogeneous_states_are_preserved() -> None:
    pair = (1, "x")
    dfa = ExtendedDFA(
        states={None, 7, pair}, input_symbols={"a"},
        transitions={None: {"a": 7}, 7: {"a": pair}, pair: {"a": pair}},
        initial_state=None, final_states={pair},
    )
    result = dfa.induced_subautomaton((None, 7))
    assert type(result) is ExtendedDFA
    assert result.states == frozenset({None, 7})
    assert result.initial_state is None
    assert set(result.iter_transitions()) == {(None, 7, "a")}
    assert result.final_states == frozenset()
    assert result.allow_partial is True


def test_trim_empty_special_case_does_not_leak_into_induction() -> None:
    dfa = ExtendedDFA(
        states={"s", "dead"}, input_symbols={"a"},
        transitions={"s": {"a": "dead"}, "dead": {"a": "dead"}},
        initial_state="s", final_states=set(),
    )
    assert dfa.useful_states() == frozenset()
    assert dfa.trim().states == frozenset({"s"})
    with pytest.raises(InvalidStateError):
        dfa.induced_subautomaton(set())
    assert dfa.induced_subautomaton({"s"}).states == frozenset({"s"})


def test_induction_never_mutates_source(automaton: ExtendedFA) -> None:
    original = (
        deepcopy(automaton.states),
        deepcopy(automaton.transitions),
        deepcopy(automaton.final_states),
        deepcopy(automaton.input_symbols),
    )
    result = automaton.induced_subautomaton({"s", "f"})
    assert result is not automaton
    assert (
        automaton.states,
        automaton.transitions,
        automaton.final_states,
        automaton.input_symbols,
    ) == original
