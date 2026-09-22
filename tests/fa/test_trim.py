"""Restriction to useful states while preserving concrete automata."""

from copy import deepcopy

import pytest

from automata.fa.fa import FAStateT

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA


TrimAutomaton = ExtendedDFA | ExtendedNFA | ExtendedGNFA


def _sample_automaton(kind: str) -> TrimAutomaton:
    """Provide useful, dead, unreachable, and irrelevant states."""
    states = {"s", "path", "f", "dead", "unseen", "neither"}
    if kind == "dfa":
        return ExtendedDFA(
            states=states,
            input_symbols={"a", "b"},
            transitions={
                "s": {"a": "path", "b": "dead"},
                "path": {"a": "path", "b": "f"},
                "f": {"a": "f", "b": "dead"},
                "dead": {"a": "dead", "b": "dead"},
                "unseen": {"a": "f", "b": "dead"},
                "neither": {"a": "neither", "b": "neither"},
            },
            initial_state="s",
            final_states={"f"},
        )
    if kind == "nfa":
        return ExtendedNFA(
            states=states,
            input_symbols={"a", "b"},
            transitions={
                "s": {"": {"path", "dead"}},
                "path": {"a": {"path"}, "b": {"f"}},
                "f": {"b": {"dead"}},
                "dead": {"a": {"dead"}},
                "unseen": {"a": {"f"}},
                "neither": {"a": {"neither"}},
            },
            initial_state="s",
            final_states={"f"},
        )

    labels = {
        ("s", "path"): "a",
        ("s", "dead"): "b",
        ("path", "path"): "a",
        ("path", "f"): "b",
        ("dead", "dead"): "a",
        ("unseen", "f"): "a",
        ("neither", "neither"): "a",
    }
    return ExtendedGNFA(
        states=states,
        input_symbols={"a", "b"},
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


@pytest.fixture(params=["dfa", "nfa", "gnfa"])
def automaton(request: pytest.FixtureRequest) -> TrimAutomaton:
    """Parameterize shared trim contracts across the concrete FA types."""
    return _sample_automaton(request.param)


def test_trim_restricts_states_and_incident_transitions(
    automaton: TrimAutomaton,
) -> None:
    """Discard every state outside the intersection and all incident edges."""
    assert automaton.accessible_states() == {"s", "path", "f", "dead"}
    assert automaton.coaccessible_states() == {"s", "path", "f", "unseen"}
    kept = automaton.useful_states()
    assert kept == {"s", "path", "f"}

    trimmed = automaton.trim()
    assert type(trimmed) is type(automaton)
    assert trimmed is not automaton
    assert trimmed.states == kept
    assert trimmed.initial_state == automaton.initial_state
    assert trimmed.final_states == {"f"}
    assert trimmed.input_symbols == automaton.input_symbols
    assert trimmed.useful_states() == trimmed.states
    for source, target, _label in trimmed.iter_transitions():
        assert source in kept
        assert target in kept
    for source, paths in trimmed.transitions.items():
        assert source in kept
        if isinstance(trimmed, ExtendedDFA):
            assert all(target in kept for target in paths.values())
        elif isinstance(trimmed, ExtendedNFA):
            assert all(
                target in kept
                for targets in paths.values()
                for target in targets
            )
        else:
            assert all(target in kept for target in paths)


def test_trim_preserves_extension_methods_and_composes(
    automaton: TrimAutomaton,
) -> None:
    """The result retains traversal and accessibility behavior."""
    trimmed = automaton.trim()
    assert trimmed.dfs()[0] == "s"
    assert trimmed.bfs()[0] == "s"
    assert trimmed.accessible_states() == trimmed.states
    assert trimmed.coaccessible_states() == trimmed.states
    assert trimmed.useful_states() == trimmed.states
    again = trimmed.trim()
    assert type(again) is type(trimmed)
    assert again is not trimmed
    assert again.states == trimmed.states


def test_trim_preserves_source_exactly(automaton: TrimAutomaton) -> None:
    """A new automaton is built without altering slots or instance state."""
    attributes = set(vars(automaton))
    for cls in type(automaton).__mro__:
        slots = getattr(cls, "__slots__", ())
        attributes.update([slots] if isinstance(slots, str) else slots)
    attributes -= {"__dict__", "__weakref__"}
    before = deepcopy({name: getattr(automaton, name) for name in attributes})
    dictionary_before = deepcopy(vars(automaton))

    trimmed = automaton.trim()

    assert trimmed is not automaton
    assert {name: getattr(automaton, name) for name in attributes} == before
    assert vars(automaton) == dictionary_before


@pytest.mark.parametrize("word", ["", "a", "ab", "aab", "b", "abb", "aaab"])
@pytest.mark.parametrize("kind", ["dfa", "nfa"])
def test_trim_preserves_word_acceptance(kind: str, word: str) -> None:
    """Representative words retain their acceptance after restriction."""
    source: ExtendedDFA | ExtendedNFA
    if kind == "dfa":
        source = ExtendedDFA(
            states={"s", "f", "dead"}, input_symbols={"a", "b"},
            transitions={
                "s": {"a": "f", "b": "dead"},
                "f": {"a": "f", "b": "dead"},
                "dead": {"a": "dead", "b": "dead"},
            },
            initial_state="s", final_states={"f"},
        )
    else:
        source = ExtendedNFA(
            states={"s", "f", "dead"}, input_symbols={"a", "b"},
            transitions={
                "s": {"": {"f", "dead"}},
                "f": {"a": {"f"}},
                "dead": {"b": {"dead"}},
            },
            initial_state="s", final_states={"f"},
        )
    assert source.trim().accepts_input(word) is source.accepts_input(word)


def test_trim_complete_dfa_becomes_partial_when_edges_are_removed() -> None:
    """Dropping a dead sink must enable upstream partial-DFA validation."""
    dfa = ExtendedDFA(
        states={"s", "f", "dead"}, input_symbols={"a", "b"},
        transitions={
            "s": {"a": "f", "b": "dead"},
            "f": {"a": "f", "b": "dead"},
            "dead": {"a": "dead", "b": "dead"},
        },
        initial_state="s", final_states={"f"},
    )
    result = dfa.trim()
    assert dfa.allow_partial is False
    assert result.allow_partial is True
    assert result.transitions == {"s": {"a": "f"}, "f": {"a": "f"}}


@pytest.mark.parametrize("allow_partial", [False, True])
def test_trim_already_trim_dfa_keeps_partial_option(
    allow_partial: bool,
) -> None:
    """A DFA with only useful states keeps its construction option."""
    dfa = ExtendedDFA(
        states={"s", "f"}, input_symbols={"a"},
        transitions={"s": {"a": "f"},
                     "f": {} if allow_partial else {"a": "f"}},
        initial_state="s", final_states={"f"},
        allow_partial=allow_partial,
    )
    result = dfa.trim()
    assert result is not dfa
    assert type(result) is ExtendedDFA
    assert result.states == dfa.states
    assert result.transitions == dfa.transitions
    assert result.allow_partial is allow_partial


def test_trim_partially_defined_dfa_removes_dead_edge() -> None:
    """An already partial DFA stays partial when a dead branch is cut."""
    dfa = ExtendedDFA(
        states={"s", "f", "dead"}, input_symbols={"a", "b"},
        transitions={"s": {"a": "f", "b": "dead"},
                     "f": {}, "dead": {"b": "dead"}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    result = dfa.trim()
    assert result.states == {"s", "f"}
    assert result.transitions == {"s": {"a": "f"}, "f": {}}
    assert result.allow_partial is True


@pytest.mark.parametrize("kind", ["nfa", "gnfa"])
def test_trim_already_trim_nfa_or_gnfa(kind: str) -> None:
    """A two-state accepting path is retained in a fresh object."""
    if kind == "nfa":
        automaton: ExtendedNFA | ExtendedGNFA = ExtendedNFA(
            states={"s", "f"}, input_symbols={"a"},
            transitions={"s": {"a": {"f"}}},
            initial_state="s", final_states={"f"},
        )
    else:
        automaton = ExtendedGNFA(
            states={"s", "f"}, input_symbols={"a"},
            transitions={"s": {"f": "a"}},
            initial_state="s", final_state="f",
        )
    result = automaton.trim()
    assert result is not automaton
    assert type(result) is type(automaton)
    assert result.states == automaton.states == automaton.useful_states()
    assert result.transitions == automaton.transitions


def test_trim_nfa_epsilon_filters_removed_destinations() -> None:
    """Keep epsilon from s to path while removing the dead branch."""
    nfa = _sample_automaton("nfa")
    assert isinstance(nfa, ExtendedNFA)
    result = nfa.trim()
    assert result.transitions["s"][""] == {"path"}
    assert "dead" not in result.transitions["s"][""]
    assert result.final_states == {"f"}


def test_trim_gnfa_retains_required_none_slots() -> None:
    """GNFA table cells with absent edges remain valid after restriction."""
    gnfa = _sample_automaton("gnfa")
    assert isinstance(gnfa, ExtendedGNFA)
    result = gnfa.trim()
    assert result.transitions["s"]["f"] is None
    assert result.transitions["s"]["path"] == "a"
    assert result.transitions["path"]["f"] == "b"
    assert set(result.transitions) == {"s", "path"}
    assert result.to_regex() == gnfa.to_regex()


@pytest.mark.parametrize("allow_partial", [False, True])
def test_trim_empty_language_dfa(allow_partial: bool) -> None:
    """A one-state nonfinal DFA represents empty language, preserving mode."""
    dfa = ExtendedDFA(
        states={"s", "dead"}, input_symbols={"a", "b"},
        transitions={
            "s": {} if allow_partial else {"a": "dead", "b": "dead"},
            "dead": {} if allow_partial else {"a": "dead", "b": "dead"},
        },
        initial_state="s", final_states=set(),
        allow_partial=allow_partial,
    )
    result = dfa.trim()
    assert type(result) is ExtendedDFA
    assert result is not dfa
    assert dfa.useful_states() == result.useful_states() == frozenset()
    assert result.states == {"s"}
    assert result.final_states == set()
    assert result.allow_partial is allow_partial
    assert result.transitions == (
        {"s": {}} if allow_partial else {"s": {"a": "s", "b": "s"}}
    )
    for word in ("", "a", "b", "abba"):
        assert result.accepts_input(word) is dfa.accepts_input(word) is False
    assert type(result.trim()) is ExtendedDFA


def test_trim_empty_language_nfa_with_none_initial() -> None:
    """Keep only the initial None state with no final or transition."""
    nfa = ExtendedNFA(
        states={None, 7, "f"}, input_symbols={"a"},
        transitions={None: {"": {7}}, 7: {"a": {7}}},
        initial_state=None, final_states={"f"},
    )
    result = nfa.trim()
    assert type(result) is ExtendedNFA
    assert result is not nfa
    assert result.states == {None}
    assert result.final_states == set()
    assert result.transitions == {None: {}}
    assert result.useful_states() == frozenset()


def test_trim_empty_language_nfa_preserves_word_acceptance() -> None:
    """A readable empty-language NFA still rejects representative words."""
    nfa = ExtendedNFA(
        states={"s", "dead", "f"}, input_symbols={"a"},
        transitions={"s": {"": {"dead"}}, "dead": {"a": {"dead"}}},
        initial_state="s", final_states={"f"},
    )
    result = nfa.trim()
    assert type(result) is ExtendedNFA
    assert result.states == {"s"}
    assert result.final_states == set()
    for word in ("", "a", "aa"):
        assert result.accepts_input(word) is nfa.accepts_input(word) is False


def test_trim_empty_language_gnfa() -> None:
    """GNFA retains disconnected initial/final states with an absent edge."""
    gnfa = ExtendedGNFA(
        states={"s", "dead", "f"}, input_symbols={"a"},
        transitions={
            "s": {"dead": "a", "f": None},
            "dead": {"dead": "a", "f": None},
        },
        initial_state="s", final_state="f",
    )
    result = gnfa.trim()
    assert type(result) is ExtendedGNFA
    assert result is not gnfa
    assert result.states == {"s", "f"}
    assert result.transitions == {"s": {"f": None}}
    assert result.final_state == "f"
    assert result.final_states == {"f"}
    assert result.useful_states() == frozenset()
    assert result.to_regex() is None


def test_trim_heterogeneous_nfa_states() -> None:
    """A None start and tuple final survive alongside epsilon edges."""
    final: FAStateT = (1, "f")
    nfa = ExtendedNFA(
        states={None, 7, final, "dead"}, input_symbols={"a"},
        transitions={
            None: {"": {7, "dead"}},
            7: {"a": {final}},
            "dead": {"a": {"dead"}},
        },
        initial_state=None, final_states={final},
    )
    result = nfa.trim()
    assert result.states == {None, 7, final}
    assert result.transitions[None][""] == {7}
    assert result.useful_states() == result.states


def test_trim_gnfa_with_none_final_state() -> None:
    """None remains a valid state name when it denotes the accepting state."""
    gnfa = ExtendedGNFA(
        states={"s", None, "dead"}, input_symbols={"a"},
        transitions={
            "s": {None: "a", "dead": None},
            "dead": {None: None, "dead": "a"},
        },
        initial_state="s", final_state=None,
    )
    result = gnfa.trim()
    assert type(result) is ExtendedGNFA
    assert result.states == {"s", None}
    assert result.final_state is None
    assert result.useful_states() == result.states
