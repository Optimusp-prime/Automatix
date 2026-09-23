"""Language-emptiness decisions from reachable accepting states."""

from copy import deepcopy
from unittest.mock import patch

import pytest
from automata.fa.fa import FAStateT

from automata_extensions.fa import ExtendedDFA, ExtendedFA, ExtendedGNFA, ExtendedNFA


def _sample_automaton(
    kind: str, final_reachable: bool
) -> ExtendedDFA | ExtendedNFA | ExtendedGNFA:
    """Construct an accepting path or a nonaccepting cycle for each FA type."""
    states = {"s", "a", "f"}
    if kind == "dfa":
        return ExtendedDFA(
            states=states,
            input_symbols={"x"},
            transitions={
                "s": {"x": "a"},
                "a": {"x": "f" if final_reachable else "a"},
                "f": {},
            },
            initial_state="s",
            final_states={"f"},
            allow_partial=True,
        )
    if kind == "nfa":
        return ExtendedNFA(
            states=states,
            input_symbols={"x"},
            transitions={
                "s": {"": {"a"}},
                "a": {"x": {"f" if final_reachable else "a"}},
            },
            initial_state="s",
            final_states={"f"},
        )
    return ExtendedGNFA(
        states=states,
        input_symbols={"x"},
        transitions={
            "s": {"a": "", "f": None},
            "a": {"a": "x", "f": "x" if final_reachable else None},
        },
        initial_state="s",
        final_state="f",
    )


@pytest.mark.parametrize("kind", ["dfa", "nfa"])
@pytest.mark.parametrize("initial_final", [False, True])
def test_singleton_language_emptiness_and_accepting_initial(
    kind: str, initial_final: bool
) -> None:
    """An accepting initial state recognizes epsilon without any edge."""
    if kind == "dfa":
        automaton: ExtendedFA = ExtendedDFA(
            states={"q"}, input_symbols=set(), transitions={"q": {}},
            initial_state="q",
            final_states={"q"} if initial_final else set(),
        )
    else:
        automaton = ExtendedNFA(
            states={"q"}, input_symbols=set(), transitions={"q": {}},
            initial_state="q",
            final_states={"q"} if initial_final else set(),
        )
    assert automaton.is_empty() is (not initial_final)


def test_dfa_final_reachable_in_one_step() -> None:
    dfa = ExtendedDFA(
        states={"s", "f"}, input_symbols={"x"},
        transitions={"s": {"x": "f"}, "f": {}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    assert dfa.is_empty() is False


@pytest.mark.parametrize("kind", ["dfa", "nfa", "gnfa"])
@pytest.mark.parametrize("final_reachable", [False, True])
def test_reachable_final_criterion_across_fa_types(
    kind: str, final_reachable: bool
) -> None:
    """A nonfinal cycle is irrelevant; an accepting path is decisive."""
    automaton = _sample_automaton(kind, final_reachable)
    assert automaton.final_states == {"f"}
    assert automaton.is_empty() is (not final_reachable)
    assert automaton.is_empty() is automaton.accessible_states().isdisjoint(
        automaton.final_states
    )


@pytest.mark.parametrize("kind", ["dfa", "nfa"])
def test_no_final_states_is_empty(kind: str) -> None:
    if kind == "dfa":
        automaton: ExtendedFA = ExtendedDFA(
            states={0, 1}, input_symbols={"x"},
            transitions={0: {"x": 1}, 1: {"x": 0}},
            initial_state=0, final_states=set(),
        )
    else:
        automaton = ExtendedNFA(
            states={0, 1}, input_symbols={"x"},
            transitions={0: {"": {1}}, 1: {"x": {0}}},
            initial_state=0, final_states=set(),
        )
    assert automaton.is_empty() is True


def test_accessible_accepting_cycle_is_nonempty() -> None:
    dfa = ExtendedDFA(
        states={"s", "a", "f"}, input_symbols={"x", "y"},
        transitions={
            "s": {"x": "a", "y": "s"},
            "a": {"x": "s", "y": "f"},
            "f": {"x": "f", "y": "f"},
        },
        initial_state="s", final_states={"f"},
    )
    assert dfa.has_cycle() is True
    assert dfa.is_empty() is False


def test_nfa_epsilon_directly_reaches_final() -> None:
    nfa = ExtendedNFA(
        states={"s", "f"}, input_symbols=set(),
        transitions={"s": {"": {"f"}}},
        initial_state="s", final_states={"f"},
    )
    assert nfa.is_empty() is False


@pytest.mark.parametrize("accepting_none", [False, True])
def test_none_and_heterogeneous_state_names(accepting_none: bool) -> None:
    final: FAStateT = None if accepting_none else (3,)
    dfa = ExtendedDFA(
        states={None, "a", 2, (3,)}, input_symbols={"x"},
        transitions={None: {"x": "a"}, "a": {"x": 2}, 2: {}, (3,): {}},
        initial_state=None, final_states={final}, allow_partial=True,
    )
    assert dfa.is_empty() is (not accepting_none)


@pytest.mark.parametrize("kind", ["dfa", "nfa", "gnfa"])
def test_trimmed_empty_language_keeps_states_but_is_empty(kind: str) -> None:
    original = _sample_automaton(kind, final_reachable=False)
    assert original.useful_states() == frozenset()
    trimmed = original.trim()
    assert trimmed is not original
    assert trimmed.states
    assert trimmed.useful_states() == frozenset()
    assert trimmed.is_empty() is True


@pytest.mark.parametrize("kind", ["dfa", "nfa", "gnfa"])
def test_query_is_bool_immutable_and_delegates_once(kind: str) -> None:
    automaton = _sample_automaton(kind, final_reachable=True)
    before = (
        deepcopy(automaton.states), deepcopy(automaton.transitions),
        deepcopy(automaton.final_states), automaton.initial_state,
    )
    with patch.object(
        type(automaton), "accessible_states",
        wraps=automaton.accessible_states,
    ) as reachable:
        result = automaton.is_empty()
    assert type(result) is bool
    assert result is False
    assert reachable.call_count == 1
    assert (
        automaton.states, automaton.transitions,
        automaton.final_states, automaton.initial_state,
    ) == before


def test_extension_does_not_delegate_to_upstream_isempty() -> None:
    dfa = _sample_automaton("dfa", final_reachable=False)
    with patch.object(
        ExtendedDFA, "isempty",
        side_effect=AssertionError("do not delegate to upstream isempty"),
    ):
        assert dfa.is_empty() is True


def test_public_classes_inherit_one_common_method() -> None:
    for cls in (ExtendedDFA, ExtendedNFA, ExtendedGNFA):
        assert cls.is_empty is ExtendedFA.is_empty
        assert not hasattr(cls, "is_finite")
