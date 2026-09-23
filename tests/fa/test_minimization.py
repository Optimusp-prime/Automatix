"""DFA distinguishable-state table filling (requirement #29 only)."""

from copy import deepcopy
from itertools import combinations
from typing import Mapping, cast

from automata.fa.fa import FAStateT

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
        ("pair_table", "pair_table_str", "print_pair_table")
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


def _three_state_cycle() -> ExtendedDFA:
    return ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a"},
        transitions={"0": {"a": "1"}, "1": {"a": "2"}, "2": {"a": "0"}},
        initial_state="0", final_states={"2"},
    )


def _redundant_dfa() -> ExtendedDFA:
    return ExtendedDFA(
        states={"start", "left", "right", "unreachable"},
        input_symbols={"a", "b"},
        transitions={
            "start": {"a": "left", "b": "right"},
            "left": {"a": "left", "b": "left"},
            "right": {"a": "right", "b": "right"},
            "unreachable": {"a": "unreachable", "b": "unreachable"},
        },
        initial_state="start", final_states={"left", "right"},
    )


def test_source_compatibility_minimality_and_both_naming_modes() -> None:
    d = _three_state_cycle()
    assert d.is_minimal() is True
    default = d.minimize()
    named = d.minimize(keep_original_names=True)
    assert sorted(map(str, default.states)) == [
        "frozenset({'0'})", "frozenset({'1'})", "frozenset({'2'})",
    ]
    assert sorted(named.states) == ["0", "1", "2"]
    assert default is not d and named is not d
    assert default.is_minimal() is True
    assert named.is_minimal() is True
    assert d.is_equivalent(default) is True
    assert d.is_equivalent(named) is True


def test_inaccessible_singleton_class_prevents_minimality() -> None:
    d = ExtendedDFA(
        states={"0", "1", "2", "unreachable"}, input_symbols={"a"},
        transitions={
            "0": {"a": "1"}, "1": {"a": "2"}, "2": {"a": "0"},
            "unreachable": {"a": "unreachable"},
        },
        initial_state="0", final_states={"2", "unreachable"},
    )
    assert all(len(group) == 1 for group in d.equivalence_classes())
    assert d.is_minimal() is False
    result = d.minimize()
    assert all("unreachable" not in group for group in result.states)
    assert result.is_minimal() is True
    assert d.is_equivalent(result) is True


def test_equivalent_accessible_states_are_merged_into_quotient() -> None:
    source = _redundant_dfa()
    before = deepcopy(source.input_parameters)
    assert source.is_minimal() is False
    result = source.minimize()
    merged = frozenset({"left", "right"})
    initial = frozenset({"start"})
    assert type(result) is ExtendedDFA
    assert result is not source
    assert result.states == {initial, merged}
    assert result.initial_state == initial
    assert result.final_states == {merged}
    transitions = cast(Mapping[FAStateT, Mapping[str, FAStateT]], result.transitions)
    assert transitions == {
        initial: {"a": merged, "b": merged},
        merged: {"a": merged, "b": merged},
    }
    assert result.is_minimal() is True
    assert source.is_equivalent(result) is True
    assert source.input_parameters == before
    assert result.complement().is_complete() is True


def test_representative_names_and_initial_state_policy() -> None:
    source = _redundant_dfa()
    result = source.minimize(keep_original_names=True)
    assert result.states == {"start", "left"} or result.states == {"start", "right"}
    assert result.initial_state == "start"
    assert result.final_states == result.states - {"start"}
    assert result.is_minimal() is True
    assert source.is_equivalent(result) is True


def test_partial_dfa_merges_states_without_exporting_analysis_trap() -> None:
    source = ExtendedDFA(
        states={"start", "left", "right"}, input_symbols={"a", "b"},
        transitions={
            "start": {"a": "left", "b": "right"},
            "left": {"a": "left"}, "right": {"a": "right"},
        },
        initial_state="start", final_states={"left", "right"},
        allow_partial=True,
    )
    result = source.minimize()
    named = source.minimize(keep_original_names=True)
    assert result.states == {
        frozenset({"start"}), frozenset({"left", "right"}),
    }
    assert all(group.issubset(source.states) for group in result.states)
    assert result.allow_partial is True
    assert source.is_equivalent(result) is True
    assert source.is_equivalent(named) is True
    assert result.is_minimal() is True
    assert named.is_minimal() is True


def test_partial_equivalent_states_with_different_missing_edges() -> None:
    source = ExtendedDFA(
        states={"start", "p", "q", "dead"}, input_symbols={"a", "b"},
        transitions={
            "start": {"a": "p", "b": "q"},
            "p": {"a": "p"},
            "q": {"a": "q", "b": "dead"},
            "dead": {"a": "dead", "b": "dead"},
        },
        initial_state="start", final_states={"p", "q"},
        allow_partial=True,
    )
    result = source.minimize()
    assert frozenset({"p", "q"}) in result.states
    assert frozenset({"dead"}) in result.states
    assert result.is_minimal() is True
    assert source.is_equivalent(result) is True


def test_none_and_heterogeneous_states_minimize_without_upstream_minify() -> None:
    source = ExtendedDFA(
        states={None, 1, ("final",), "extra"}, input_symbols={"a", "b"},
        transitions={
            None: {"a": 1, "b": ("final",)},
            1: {"a": 1, "b": ("final",)},
            ("final",): {"a": ("final",), "b": ("final",)},
            "extra": {"a": "extra", "b": "extra"},
        },
        initial_state=None, final_states={("final",)},
    )
    default = source.minimize()
    named = source.minimize(keep_original_names=True)
    assert default.initial_state == frozenset({None, 1})
    assert named.initial_state is None
    assert all("extra" not in group for group in default.states)
    assert default.is_minimal() is True
    assert named.is_minimal() is True
    assert source.is_equivalent(default) is True
    assert source.is_equivalent(named) is True


def test_minimality_predicate_is_exact_bool_and_handles_partial_dfa() -> None:
    d = ExtendedDFA(
        states={"q"}, input_symbols={"a", "b"},
        transitions={"q": {"a": "q"}}, initial_state="q",
        final_states={"q"}, allow_partial=True,
    )
    assert d.is_minimal() is True
    assert type(d.is_minimal()) is bool
    assert d.minimize().is_minimal() is True
