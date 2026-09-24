"""State morphisms, symbol projections and non-congruent quotients."""

from copy import deepcopy

import pytest

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.fa_mixins.morphism import MorphismMixin
from tests.fa.test_state_elimination import _mature_dfa


def _partial_dfa() -> ExtendedDFA:
    return ExtendedDFA(
        states={"s", "f"}, input_symbols={"a", "b"},
        transitions={"s": {"a": "f"}, "f": {}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )


def _epsilon_nfa() -> ExtendedNFA:
    return ExtendedNFA(
        states={"s", "m", "f"}, input_symbols={"a", "b"},
        transitions={
            "s": {"": {"m"}, "a": {"f"}},
            "m": {"a": {"f"}, "b": {"f"}},
            "f": {"b": {"f"}},
        },
        initial_state="s", final_states={"f"},
    )


def test_mature_source_compatibility_all_three_examples() -> None:
    d = _mature_dfa()
    assert d.is_morphism_to(d, {"0": "0", "1": "1", "2": "2"}) is True
    assert d.project({"a": "x", "b": None}).accepts_input("xxx") is True
    assert sorted(d.quotient_by({"0": "0", "1": "0", "2": "2"}).states) == [
        "0", "2",
    ]


def test_mature_noncongruent_quotient_preserves_both_a_destinations() -> None:
    d = _mature_dfa()
    mapping = {"0": "0", "1": "0", "2": "2"}
    quotient = d.quotient_by(mapping)
    assert type(quotient) is ExtendedNFA
    assert quotient.initial_state == "0"
    assert quotient.final_states == {"0"}
    assert quotient.transitions["0"]["a"] == {"0", "2"}
    assert quotient.transitions["0"]["b"] == {"0"}
    assert quotient.transitions["2"]["a"] == {"0"}
    assert quotient.transitions["2"]["b"] == {"2"}
    assert d.is_morphism_to(quotient, mapping) is True


def test_mature_projection_structure_and_language() -> None:
    d = _mature_dfa()
    projected = d.project({"a": "x", "b": None})
    assert type(projected) is ExtendedNFA
    assert projected.states == d.states
    assert projected.initial_state == d.initial_state
    assert projected.final_states == d.final_states
    assert projected.input_symbols == {"x"}
    assert projected.transitions["0"]["x"] == {"1"}
    assert projected.transitions["0"][""] == {"0"}
    for word, accepted in (("", True), ("x", False), ("xx", False),
                           ("xxx", True), ("xxxxxx", True)):
        assert projected.accepts_input(word) is accepted


@pytest.mark.parametrize("mapping", [
    {"s": "s"},
    {"s": "s", "f": "f", "extra": "extra"},
    {"s": "s", "f": "absent"},
])
def test_morphism_invalid_state_maps_return_false(mapping: dict[str, str]) -> None:
    dfa = _partial_dfa()
    assert dfa.is_morphism_to(dfa, mapping) is False


def test_morphism_initial_final_and_alphabet_policies() -> None:
    source = _partial_dfa()
    swapped = {"s": "f", "f": "s"}
    assert source.is_morphism_to(source, swapped) is False

    nonfinal_target = ExtendedDFA(
        states=source.states, input_symbols=source.input_symbols,
        transitions=source.transitions, initial_state=source.initial_state,
        final_states=set(), allow_partial=True,
    )
    identity = {"s": "s", "f": "f"}
    assert source.is_morphism_to(nonfinal_target, identity) is False
    assert nonfinal_target.is_morphism_to(source, identity) is True

    different_alphabet = ExtendedDFA(
        states=source.states, input_symbols={"a"},
        transitions={"s": {"a": "f"}, "f": {}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    assert source.is_morphism_to(different_alphabet, identity) is False


def test_morphism_extra_target_edges_non_surjectivity_and_partial_source() -> None:
    source = _partial_dfa()
    target = ExtendedDFA(
        states={"s", "f", "unused"}, input_symbols={"a", "b"},
        transitions={
            "s": {"a": "f", "b": "unused"},
            "f": {"a": "f", "b": "f"},
            "unused": {"a": "unused", "b": "unused"},
        },
        initial_state="s", final_states={"f", "unused"},
    )
    assert source.is_morphism_to(target, {"s": "s", "f": "f"}) is True
    assert target.is_morphism_to(source, {"s": "s", "f": "f", "unused": "s"}) is False


def test_morphism_existing_source_edge_missing_in_target_is_false() -> None:
    source = _partial_dfa()
    target = ExtendedDFA(
        states={"s", "f"}, input_symbols={"a", "b"},
        transitions={"s": {}, "f": {}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    assert source.is_morphism_to(target, {"s": "s", "f": "f"}) is False


def test_morphism_dfa_nfa_and_nfa_dfa_nfa_combinations() -> None:
    dfa = ExtendedDFA(
        states={"s", "f"}, input_symbols={"a"},
        transitions={"s": {"a": "f"}, "f": {"a": "f"}},
        initial_state="s", final_states={"f"},
    )
    nfa = ExtendedNFA(
        states={"s", "f", "extra"}, input_symbols={"a"},
        transitions={"s": {"a": {"f", "extra"}},
                     "f": {"a": {"f"}}, "extra": {"a": {"extra"}}},
        initial_state="s", final_states={"f", "extra"},
    )
    assert dfa.is_morphism_to(dfa, {"s": "s", "f": "f"}) is True
    assert dfa.is_morphism_to(nfa, {"s": "s", "f": "f"}) is True
    assert nfa.is_morphism_to(nfa, {state: state for state in nfa.states}) is True
    assert nfa.is_morphism_to(dfa, {"s": "s", "f": "f", "extra": "f"}) is True


def test_morphism_nfa_epsilon_edge_must_be_preserved() -> None:
    source = _epsilon_nfa()
    identity = {state: state for state in source.states}
    assert source.is_morphism_to(source, identity) is True
    without_epsilon = ExtendedNFA(
        states=source.states, input_symbols=source.input_symbols,
        transitions={
            "s": {"a": {"f"}},
            "m": {"a": {"f"}, "b": {"f"}},
            "f": {"b": {"f"}},
        },
        initial_state="s", final_states={"f"},
    )
    assert source.is_morphism_to(without_epsilon, identity) is False
    assert without_epsilon.is_morphism_to(source, identity) is True


def test_morphism_sources_targets_and_mapping_are_immutable() -> None:
    source = _epsilon_nfa()
    target = _epsilon_nfa()
    mapping = {state: state for state in source.states}
    before = deepcopy(source.input_parameters), deepcopy(target.input_parameters), mapping.copy()
    assert source.is_morphism_to(target, mapping) is True
    assert (source.input_parameters, target.input_parameters, mapping) == before


def test_project_identity_renaming_and_symbol_collision() -> None:
    source = _partial_dfa()
    identity = source.project({"a": "a", "b": "b"})
    renamed = source.project({"a": "x", "b": "y"})
    collided = source.project({"a": "x", "b": "x"})
    assert all(type(result) is ExtendedNFA for result in (identity, renamed, collided))
    assert identity.input_symbols == {"a", "b"}
    assert identity.accepts_input("a") is True
    assert renamed.input_symbols == {"x", "y"}
    assert renamed.accepts_input("x") is True
    assert collided.input_symbols == {"x"}
    assert collided.accepts_input("x") is True


def test_project_collision_unions_distinct_destinations() -> None:
    source = ExtendedDFA(
        states={"s", "left", "right"}, input_symbols={"a", "b"},
        transitions={"s": {"a": "left", "b": "right"},
                     "left": {}, "right": {}},
        initial_state="s", final_states={"right"}, allow_partial=True,
    )
    result = source.project({"a": "x", "b": "x"})
    assert result.transitions["s"]["x"] == {"left", "right"}
    assert result.accepts_input("x") is True


def test_project_erasure_and_all_symbols_erased() -> None:
    source = _partial_dfa()
    result = source.project({"a": None, "b": None})
    assert result.input_symbols == set()
    assert result.transitions["s"][""] == {"f"}
    assert result.accepts_input("") is True
    assert result.states == source.states


def test_project_nfa_preserves_existing_epsilon_and_parallel_edges() -> None:
    source = _epsilon_nfa()
    result = source.project({"a": "x", "b": None})
    assert type(result) is ExtendedNFA
    assert result.input_symbols == {"x"}
    assert result.transitions["s"][""] == {"m"}
    assert result.transitions["s"]["x"] == {"f"}
    assert result.transitions["m"][""] == {"f"}
    assert result.accepts_input("") is True


@pytest.mark.parametrize("mapping", [
    {"a": "x"},
    {"a": "x", "b": None, "c": "z"},
    {"a": "long", "b": None},
    {"a": "", "b": None},
])
def test_project_rejects_invalid_symbol_maps(mapping: dict[str, str | None]) -> None:
    with pytest.raises(ValueError):
        _partial_dfa().project(mapping)


def test_project_source_and_mapping_immutable_and_result_composable() -> None:
    source = _epsilon_nfa()
    mapping = {"a": "x", "b": None}
    before = deepcopy(source.input_parameters), mapping.copy()
    result = source.project(mapping)
    assert result is not source
    assert (source.input_parameters, mapping) == before
    assert type(result.determinize()) is ExtendedDFA


def test_quotient_identity_map_and_arbitrary_hashable_labels() -> None:
    source = _partial_dfa()
    identity = source.quotient_by({"s": "s", "f": "f"})
    mapped = source.quotient_by({"s": (0, "start"), "f": 1})
    assert type(identity) is ExtendedNFA
    assert identity.states == source.states
    assert identity.accepts_input("a") is True
    assert mapped.states == {(0, "start"), 1}
    assert mapped.initial_state == (0, "start")
    assert mapped.final_states == {1}
    assert mapped.transitions[(0, "start")]["a"] == {1}


def test_quotient_any_final_fibre_and_initial_image() -> None:
    source = ExtendedDFA(
        states={"s", "f", "dead"}, input_symbols={"a"},
        transitions={"s": {"a": "f"}, "f": {"a": "f"},
                     "dead": {"a": "dead"}},
        initial_state="s", final_states={"f"},
    )
    mapping = {"s": "merged", "f": "merged", "dead": "other"}
    result = source.quotient_by(mapping)
    assert result.states == {"merged", "other"}
    assert result.initial_state == "merged"
    assert result.final_states == {"merged"}
    assert source.is_morphism_to(result, mapping) is True


def test_quotient_nfa_preserves_epsilon_and_merges_destinations() -> None:
    source = _epsilon_nfa()
    mapping = {"s": "start", "m": "start", "f": "final"}
    result = source.quotient_by(mapping)
    assert type(result) is ExtendedNFA
    assert result.transitions["start"][""] == {"start"}
    assert result.transitions["start"]["a"] == {"final"}
    assert result.transitions["start"]["b"] == {"final"}
    assert source.is_morphism_to(result, mapping) is True


@pytest.mark.parametrize("mapping", [
    {"s": "merged"},
    {"s": "merged", "f": "merged", "extra": "extra"},
    {"s": [], "f": "valid"},
])
def test_quotient_rejects_invalid_state_maps(mapping: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        _partial_dfa().quotient_by(mapping)


def test_quotient_source_and_mapping_immutable_and_result_composable() -> None:
    source = _epsilon_nfa()
    mapping = {"s": "m", "m": "m", "f": "f"}
    before = deepcopy(source.input_parameters), mapping.copy()
    result = source.quotient_by(mapping)
    assert result is not source
    assert (source.input_parameters, mapping) == before
    assert type(result.determinize()) is ExtendedDFA


def test_mixin_placement_and_gnfa_exclusion() -> None:
    assert MorphismMixin in ExtendedDFA.__mro__
    assert MorphismMixin in ExtendedNFA.__mro__
    assert MorphismMixin not in ExtendedGNFA.__mro__
    for method in ("is_morphism_to", "project", "quotient_by"):
        assert hasattr(ExtendedDFA, method)
        assert hasattr(ExtendedNFA, method)
        assert not hasattr(ExtendedGNFA, method)
