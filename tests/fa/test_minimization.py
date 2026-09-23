"""DFA distinguishable-state table filling (requirement #29 only)."""

from copy import deepcopy
from itertools import combinations

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
         "is_minimal", "minimize")
    )


def test_source_compatibility_three_singleton_classes() -> None:
    """The mature three-state cycle has three Myhill–Nerode classes."""
    d = ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a"},
        transitions={"0": {"a": "1"}, "1": {"a": "2"}, "2": {"a": "0"}},
        initial_state="0", final_states={"2"},
    )
    assert set(d.equivalence_classes()) == {
        frozenset({"0"}), frozenset({"1"}), frozenset({"2"}),
    }


def test_equivalent_states_share_a_class() -> None:
    d = ExtendedDFA(
        states={"initial", "left", "right"}, input_symbols={"a"},
        transitions={
            "initial": {"a": "left"},
            "left": {"a": "left"}, "right": {"a": "right"},
        },
        initial_state="initial", final_states={"left", "right"},
    )
    assert set(d.equivalence_classes()) == {
        frozenset({"initial"}), frozenset({"left", "right"}),
    }


def test_no_distinguishable_pairs_yield_one_class() -> None:
    d = ExtendedDFA(
        states={"p", "q", "r"}, input_symbols={"a"},
        transitions={
            "p": {"a": "q"}, "q": {"a": "r"}, "r": {"a": "p"},
        },
        initial_state="p", final_states={"p", "q", "r"},
    )
    assert d.distinguishable_states() == set()
    assert d.equivalence_classes() == [frozenset(d.states)]


def test_partition_properties_match_distinguishability_relation() -> None:
    d = ExtendedDFA(
        states={"start", "p", "q", "final", "dead"}, input_symbols={"a"},
        transitions={
            "start": {"a": "p"}, "p": {"a": "final"},
            "q": {"a": "final"}, "final": {"a": "final"},
            "dead": {"a": "dead"},
        },
        initial_state="start", final_states={"final"},
    )
    classes = d.equivalence_classes()
    marked = d.distinguishable_states()
    assert type(classes) is list
    assert all(type(group) is frozenset and group for group in classes)
    assert frozenset().union(*classes) == d.states
    assert sum(len(group) for group in classes) == len(d.states)
    assert any({"p", "q"}.issubset(group) for group in classes)
    for p, q in combinations(d.states, 2):
        same_class = any(p in group and q in group for group in classes)
        assert same_class is (frozenset((p, q)) not in marked)


def test_unreachable_states_are_partitioned_too() -> None:
    d = ExtendedDFA(
        states={"initial", "unreachable_final", "unreachable_dead"},
        input_symbols={"a"},
        transitions={
            "initial": {"a": "initial"},
            "unreachable_final": {"a": "unreachable_final"},
            "unreachable_dead": {"a": "unreachable_dead"},
        },
        initial_state="initial", final_states={"unreachable_final"},
    )
    assert set(d.equivalence_classes()) == {
        frozenset({"initial", "unreachable_dead"}),
        frozenset({"unreachable_final"}),
    }


def test_partial_dfa_equivalent_missing_transitions_share_a_class() -> None:
    d = ExtendedDFA(
        states={"p", "q", "final"}, input_symbols={"a", "b"},
        transitions={"p": {}, "q": {}, "final": {"a": "final"}},
        initial_state="p", final_states={"final"}, allow_partial=True,
    )
    assert set(d.equivalence_classes()) == {
        frozenset({"p", "q"}), frozenset({"final"}),
    }


def test_heterogeneous_states_and_immutability() -> None:
    d = ExtendedDFA(
        states={None, 1, ("final",)}, input_symbols={"a"},
        transitions={
            None: {}, 1: {}, ("final",): {"a": ("final",)},
        },
        initial_state=None, final_states={("final",)}, allow_partial=True,
    )
    before = deepcopy(d.input_parameters)
    assert set(d.equivalence_classes()) == {
        frozenset({None, 1}), frozenset({("final",)}),
    }
    assert d.input_parameters == before
    assert ExtendedDFA.equivalence_classes is MinimizationMixin.equivalence_classes
    assert not hasattr(d, "is_minimal")
    assert not hasattr(d, "minimize")
