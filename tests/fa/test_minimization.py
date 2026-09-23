"""DFA distinguishable-state table filling (requirement #29 only)."""

from copy import deepcopy

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.dfa_mixins.minimization import MinimizationMixin


def test_source_compatibility_three_state_cycle() -> None:
    """The mature three-state example has exactly three marked pairs."""
    d = ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a"},
        transitions={"0": {"a": "1"}, "1": {"a": "2"}, "2": {"a": "0"}},
        initial_state="0", final_states={"2"},
    )
    assert d.distinguishable_states() == {
        frozenset({"1", "2"}),
        frozenset({"1", "0"}),
        frozenset({"0", "2"}),
    }


def test_final_and_nonfinal_states_are_marked_by_empty_word() -> None:
    d = ExtendedDFA(
        states={"final", "nonfinal"}, input_symbols={"a"},
        transitions={
            "final": {"a": "final"}, "nonfinal": {"a": "nonfinal"},
        },
        initial_state="final", final_states={"final"},
    )
    assert d.distinguishable_states() == {frozenset({"final", "nonfinal"})}


def test_one_symbol_and_multiple_rounds_propagate_marks() -> None:
    d = ExtendedDFA(
        states={"p", "q", "r", "dead", "final"}, input_symbols={"a"},
        transitions={
            "p": {"a": "r"}, "q": {"a": "dead"},
            "r": {"a": "final"}, "dead": {"a": "dead"},
            "final": {"a": "final"},
        },
        initial_state="p", final_states={"final"},
    )
    marked = d.distinguishable_states()
    assert frozenset({"r", "dead"}) in marked  # witness: a
    assert frozenset({"p", "q"}) in marked  # witness: aa
    assert frozenset({"q", "dead"}) not in marked
    assert frozenset({"p", "r"}) in marked


def test_no_pair_is_distinguishable_when_all_states_accept_every_word() -> None:
    d = ExtendedDFA(
        states={"p", "q", "r"}, input_symbols={"a", "b"},
        transitions={
            "p": {"a": "q", "b": "r"},
            "q": {"a": "p", "b": "r"},
            "r": {"a": "r", "b": "r"},
        },
        initial_state="p", final_states={"p", "q", "r"},
    )
    assert d.distinguishable_states() == set()


def test_unreachable_states_are_included_and_pairs_are_unordered() -> None:
    d = ExtendedDFA(
        states={"start", "unreachable_final", "unreachable_dead"},
        input_symbols={"a"},
        transitions={
            "start": {"a": "start"},
            "unreachable_final": {"a": "unreachable_final"},
            "unreachable_dead": {"a": "unreachable_dead"},
        },
        initial_state="start", final_states={"unreachable_final"},
    )
    result = d.distinguishable_states()
    assert result == {
        frozenset({"start", "unreachable_final"}),
        frozenset({"unreachable_dead", "unreachable_final"}),
    }
    assert type(result) is set
    assert all(type(pair) is frozenset and len(pair) == 2 for pair in result)


def test_partial_dfa_missing_edge_is_implicit_rejecting_trap() -> None:
    d = ExtendedDFA(
        states={"p", "q", "final"}, input_symbols={"a", "b"},
        transitions={
            "p": {"a": "final"}, "q": {}, "final": {"a": "final"},
        },
        initial_state="p", final_states={"final"}, allow_partial=True,
    )
    result = d.distinguishable_states()
    assert frozenset({"p", "q"}) in result
    assert all(pair.issubset(d.states) for pair in result)


def test_two_missing_transitions_do_not_distinguish_states() -> None:
    d = ExtendedDFA(
        states={"p", "q", "final"}, input_symbols={"a"},
        transitions={"p": {}, "q": {}, "final": {"a": "final"}},
        initial_state="p", final_states={"final"}, allow_partial=True,
    )
    assert frozenset({"p", "q"}) not in d.distinguishable_states()


def test_none_and_heterogeneous_states() -> None:
    d = ExtendedDFA(
        states={None, 1, ("final",)}, input_symbols={"a"},
        transitions={
            None: {"a": ("final",)}, 1: {},
            ("final",): {"a": ("final",)},
        },
        initial_state=None, final_states={("final",)}, allow_partial=True,
    )
    assert frozenset({None, 1}) in d.distinguishable_states()


def test_query_is_immutable_and_dfa_specific() -> None:
    d = ExtendedDFA(
        states={"p", "q"}, input_symbols={"a"},
        transitions={"p": {"a": "q"}, "q": {"a": "q"}},
        initial_state="p", final_states={"q"},
    )
    before = deepcopy(d.input_parameters)
    assert d.distinguishable_states() == {frozenset({"p", "q"})}
    assert d.input_parameters == before
    assert ExtendedDFA.distinguishable_states is MinimizationMixin.distinguishable_states
    assert MinimizationMixin in ExtendedDFA.__mro__
    assert MinimizationMixin not in ExtendedNFA.__mro__
    assert MinimizationMixin not in ExtendedGNFA.__mro__
    assert not any(
        hasattr(d, name) for name in
        ("pair_table", "pair_table_str", "print_pair_table",
         "equivalence_classes", "is_minimal", "minimize")
    )
