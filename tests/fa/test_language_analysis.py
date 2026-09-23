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
    assert ExtendedDFA.is_finite is ExtendedFA.is_finite
    assert ExtendedNFA.is_finite is ExtendedFA.is_finite
    assert ExtendedGNFA.is_finite is not ExtendedFA.is_finite


def _dfa_for_finiteness(
    states: set[FAStateT],
    edges: list[tuple[FAStateT, str, FAStateT]],
    final_states: set[FAStateT],
) -> ExtendedDFA:
    """Build a partial DFA from explicitly labeled graph edges."""
    transitions: dict[FAStateT, dict[str, FAStateT]] = {
        state: {} for state in states
    }
    for source, symbol, target in edges:
        transitions[source][symbol] = target
    return ExtendedDFA(
        states=states,
        input_symbols={symbol for _, symbol, _ in edges},
        transitions=transitions,
        initial_state="s",
        final_states=final_states,
        allow_partial=True,
    )


@pytest.mark.parametrize(
    ("states", "edges", "finals", "expected"),
    [
        ({"s", "f"}, [("s", "a", "f")], {"f"}, True),
        ({"s"}, [], {"s"}, True),
        ({"s", "f"}, [("s", "a", "s"), ("s", "b", "f")], {"f"}, False),
        (
            {"s", "f", "d1", "d2"},
            [
                ("s", "a", "f"), ("s", "b", "d1"),
                ("d1", "a", "d2"), ("d2", "a", "d1"),
            ],
            {"f"}, True,
        ),
        (
            {"s", "f", "x", "y"},
            [
                ("s", "a", "f"), ("x", "a", "y"),
                ("y", "a", "x"), ("y", "b", "f"),
            ],
            {"f"}, True,
        ),
        (
            {"s", "f", "x", "y"},
            [("s", "a", "f"), ("x", "a", "y"), ("y", "a", "x")],
            {"f"}, True,
        ),
        (
            {"s", "f", "d", "x"},
            [
                ("s", "a", "f"), ("s", "b", "d"),
                ("f", "a", "f"), ("d", "a", "d"), ("x", "a", "x"),
            ],
            {"f"}, False,
        ),
        ({"s", "f"}, [("s", "a", "s")], {"f"}, True),
    ],
    ids=[
        "acyclic", "accepting-initial-no-cycle", "useful-self-loop",
        "reachable-dead-cycle-with-finite-acceptance",
        "coaccessible-unreachable-cycle", "completely-unreachable-cycle",
        "one-useful-among-multiple-cycles", "empty-language",
    ],
)
def test_dfa_finiteness_depends_on_useful_cycles(
    states: set[FAStateT],
    edges: list[tuple[FAStateT, str, FAStateT]],
    finals: set[FAStateT],
    expected: bool,
) -> None:
    dfa = _dfa_for_finiteness(states, edges, finals)
    result = dfa.is_finite()
    assert type(result) is bool
    assert result is expected
    assert result is dfa.isfinite()


def test_global_cycle_in_dead_branch_does_not_make_language_infinite() -> None:
    dfa = _dfa_for_finiteness(
        {"s", "f", "d1", "d2"},
        [
            ("s", "a", "f"), ("s", "b", "d1"),
            ("d1", "a", "d2"), ("d2", "a", "d1"),
        ],
        {"f"},
    )
    assert dfa.has_cycle() is True
    assert dfa.useful_states() == {"s", "f"}
    assert dfa.is_finite() is True


def test_nfa_consuming_cycle_makes_language_infinite() -> None:
    nfa = ExtendedNFA(
        states={"s", "f"}, input_symbols={"a"},
        transitions={"s": {"a": {"f"}}, "f": {"a": {"f"}}},
        initial_state="s", final_states={"f"},
    )
    assert nfa.useful_states() == {"s", "f"}
    assert nfa.is_finite() is False


def test_useful_epsilon_only_cycle_recognizes_finite_language() -> None:
    nfa = ExtendedNFA(
        states={"q"}, input_symbols={"a"},
        transitions={"q": {"": {"q"}}},
        initial_state="q", final_states={"q"},
    )
    assert nfa.has_cycle() is True
    assert nfa.useful_states() == {"q"}
    assert nfa.accepts_input("") is True
    assert nfa.accepts_input("a") is False
    assert nfa.is_finite() is True


def test_epsilon_cycle_with_consuming_edge_inside_scc_is_infinite() -> None:
    """A consuming cross edge can belong to an SCC without being a back edge."""
    nfa = ExtendedNFA(
        states={"s", "a", "b"}, input_symbols={"x"},
        transitions={
            "s": {"": {"a"}, "x": {"b"}},
            "a": {"": {"s"}},
            "b": {"": {"a"}},
        },
        initial_state="s", final_states={"a"},
    )
    assert nfa.useful_states() == nfa.states
    assert nfa.is_finite() is False


def test_consuming_edge_outside_epsilon_scc_does_not_repeat() -> None:
    nfa = ExtendedNFA(
        states={"s", "a", "f"}, input_symbols={"x"},
        transitions={
            "s": {"": {"a"}, "x": {"f"}},
            "a": {"": {"s"}},
        },
        initial_state="s", final_states={"f"},
    )
    assert nfa.has_cycle() is True
    assert nfa.is_finite() is True


def test_nfa_epsilon_cycle_with_consuming_exit_to_final_is_finite() -> None:
    nfa = ExtendedNFA(
        states={"s", "a", "f"}, input_symbols={"x"},
        transitions={
            "s": {"": {"a"}},
            "a": {"": {"s"}, "x": {"f"}},
        },
        initial_state="s", final_states={"f"},
    )
    assert nfa.is_finite() is True


@pytest.mark.parametrize("kind", ["dfa", "nfa"])
@pytest.mark.parametrize("final_reachable", [False, True])
def test_finiteness_of_empty_and_nonempty_trim_results(
    kind: str, final_reachable: bool
) -> None:
    original = _sample_automaton(kind, final_reachable)
    trimmed = original.trim()
    assert trimmed is not original
    assert trimmed.is_finite() is True
    if not final_reachable:
        assert trimmed.is_empty() is True
        assert trimmed.states


def test_none_and_heterogeneous_nfa_states() -> None:
    nfa = ExtendedNFA(
        states={None, "a", 2}, input_symbols={"x"},
        transitions={
            None: {"": {"a"}},
            "a": {"x": {2}},
            2: {"": {"a"}},
        },
        initial_state=None, final_states={2},
    )
    assert nfa.is_finite() is False


@pytest.mark.parametrize("label", ["a", "a*", ""])
def test_gnfa_finiteness_is_explicitly_unsupported(label: str) -> None:
    gnfa = ExtendedGNFA(
        states={"s", "f"}, input_symbols={"a"},
        transitions={"s": {"f": label}},
        initial_state="s", final_state="f",
    )
    with pytest.raises(NotImplementedError, match="GNFA regex labels"):
        gnfa.is_finite()


@pytest.mark.parametrize("kind", ["dfa", "nfa", "gnfa"])
def test_finiteness_query_never_mutates_source(kind: str) -> None:
    automaton = _sample_automaton(kind, final_reachable=True)
    before = (
        deepcopy(automaton.states), deepcopy(automaton.transitions),
        deepcopy(automaton.final_states), automaton.initial_state,
    )
    if kind == "gnfa":
        with pytest.raises(NotImplementedError):
            automaton.is_finite()
    else:
        assert type(automaton.is_finite()) is bool
    assert (
        automaton.states, automaton.transitions,
        automaton.final_states, automaton.initial_state,
    ) == before


def test_finiteness_does_not_delegate_to_trim_or_upstream_isfinite() -> None:
    dfa = _dfa_for_finiteness(
        {"s", "f"}, [("s", "a", "f")], {"f"}
    )
    with (
        patch.object(ExtendedDFA, "trim", side_effect=AssertionError),
        patch.object(ExtendedDFA, "isfinite", side_effect=AssertionError),
        patch.object(ExtendedDFA, "has_cycle", side_effect=AssertionError),
    ):
        assert dfa.is_finite() is True
