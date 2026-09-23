"""Structural DFA isomorphism, distinct from language equivalence."""

from copy import deepcopy

from automata.fa.dfa import DFA

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.dfa_mixins.isomorphism import IsomorphismMixin


def _cycle() -> ExtendedDFA:
    return ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a"},
        transitions={"0": {"a": "1"}, "1": {"a": "2"}, "2": {"a": "0"}},
        initial_state="0", final_states={"2"},
    )


def _renamed_cycle() -> ExtendedDFA:
    return ExtendedDFA(
        states={10, 20, 30}, input_symbols={"a"},
        transitions={10: {"a": 20}, 20: {"a": 30}, 30: {"a": 10}},
        initial_state=10, final_states={30},
    )


def test_source_compatibility_renamed_structure_and_reflexivity() -> None:
    """Analog of the mature example; extension minimize awaits #32."""
    d = _cycle()
    renamed = _renamed_cycle()
    assert d.is_isomorphic_to(d) is True
    assert d.is_isomorphic_to(renamed) is True
    assert renamed.is_isomorphic_to(d) is True
    assert type(d.is_isomorphic_to(renamed)) is bool


def test_same_language_does_not_imply_isomorphism() -> None:
    one = ExtendedDFA(
        states={"q"}, input_symbols={"a"},
        transitions={"q": {"a": "q"}}, initial_state="q",
        final_states={"q"},
    )
    two = ExtendedDFA(
        states={"p", "r"}, input_symbols={"a"},
        transitions={"p": {"a": "r"}, "r": {"a": "r"}},
        initial_state="p", final_states={"p", "r"},
    )
    assert one.is_equivalent(two) is True
    assert one.is_isomorphic_to(two) is False


def test_finality_and_initial_structure_are_preserved() -> None:
    source = ExtendedDFA(
        states={"s", "f"}, input_symbols={"a"},
        transitions={"s": {"a": "f"}, "f": {"a": "f"}},
        initial_state="s", final_states={"f"},
    )
    wrong_initial_finality = ExtendedDFA(
        states={0, 1}, input_symbols={"a"},
        transitions={0: {"a": 0}, 1: {"a": 1}},
        initial_state=0, final_states={0},
    )
    wrong_initial_edges = ExtendedDFA(
        states={0, 1}, input_symbols={"a"},
        transitions={0: {"a": 0}, 1: {"a": 1}},
        initial_state=0, final_states={1},
    )
    no_finals = ExtendedDFA(
        states={0, 1}, input_symbols={"a"},
        transitions={0: {"a": 1}, 1: {"a": 1}},
        initial_state=0, final_states=set(),
    )
    assert source.is_isomorphic_to(wrong_initial_finality) is False
    assert source.is_isomorphic_to(wrong_initial_edges) is False
    assert source.is_isomorphic_to(no_finals) is False


def test_labeled_edges_and_alphabet_must_match() -> None:
    left = ExtendedDFA(
        states={"x", "y"}, input_symbols={"a", "b"},
        transitions={
            "x": {"a": "x", "b": "y"},
            "y": {"a": "y", "b": "y"},
        },
        initial_state="x", final_states={"y"},
    )
    swapped_edges = ExtendedDFA(
        states={0, 1}, input_symbols={"a", "b"},
        transitions={0: {"a": 1, "b": 0}, 1: {"a": 1, "b": 1}},
        initial_state=0, final_states={1},
    )
    other_alphabet = ExtendedDFA(
        states={0, 1}, input_symbols={"a"},
        transitions={0: {"a": 0}, 1: {"a": 1}},
        initial_state=0, final_states={1},
    )
    assert left.is_isomorphic_to(swapped_edges) is False
    assert left.is_isomorphic_to(other_alphabet) is False


def test_partial_dfa_preserves_missing_edges_and_self_loops() -> None:
    left = ExtendedDFA(
        states={"start", "final"}, input_symbols={"a", "b"},
        transitions={
            "start": {"a": "final"}, "final": {"a": "final"},
        },
        initial_state="start", final_states={"final"}, allow_partial=True,
    )
    renamed = ExtendedDFA(
        states={None, (1, 2)}, input_symbols={"a", "b"},
        transitions={None: {"a": (1, 2)}, (1, 2): {"a": (1, 2)}},
        initial_state=None, final_states={(1, 2)}, allow_partial=True,
    )
    extra_edge = ExtendedDFA(
        states={0, 1}, input_symbols={"a", "b"},
        transitions={0: {"a": 1, "b": 1}, 1: {"a": 1}},
        initial_state=0, final_states={1}, allow_partial=True,
    )
    assert left.is_isomorphic_to(renamed) is True
    assert left.is_isomorphic_to(extra_edge) is False


def test_unreachable_states_participate_in_bijection() -> None:
    left = ExtendedDFA(
        states={"start", "x", "y"}, input_symbols={"a"},
        transitions={
            "start": {"a": "start"}, "x": {"a": "y"}, "y": {"a": "x"},
        },
        initial_state="start", final_states={"x", "y"},
    )
    renamed = ExtendedDFA(
        states={0, 1, 2}, input_symbols={"a"},
        transitions={0: {"a": 0}, 1: {"a": 2}, 2: {"a": 1}},
        initial_state=0, final_states={1, 2},
    )
    changed_unreachable = ExtendedDFA(
        states={0, 1, 2}, input_symbols={"a"},
        transitions={0: {"a": 0}, 1: {"a": 1}, 2: {"a": 2}},
        initial_state=0, final_states={1, 2},
    )
    assert left.is_isomorphic_to(renamed) is True
    assert left.is_isomorphic_to(changed_unreachable) is False


def test_unreachable_components_require_backtracking() -> None:
    left = ExtendedDFA(
        states={"s", "a", "b", "c", "d"}, input_symbols={"0", "1"},
        transitions={
            "s": {"0": "s", "1": "s"},
            "a": {"0": "b", "1": "a"},
            "b": {"0": "a", "1": "b"},
            "c": {"0": "d", "1": "c"},
            "d": {"0": "c", "1": "d"},
        },
        initial_state="s", final_states={"a", "b", "c", "d"},
    )
    other = ExtendedDFA(
        states={0, 1, 2, 3, 4}, input_symbols={"0", "1"},
        transitions={
            0: {"0": 0, "1": 0},
            1: {"0": 3, "1": 1},
            2: {"0": 4, "1": 2},
            3: {"0": 1, "1": 3},
            4: {"0": 2, "1": 4},
        },
        initial_state=0, final_states={1, 2, 3, 4},
    )
    assert left.is_isomorphic_to(other) is True


def test_backtracking_rejects_incompatible_unreachable_structure() -> None:
    left = ExtendedDFA(
        states={"s", "a", "b", "c"}, input_symbols={"0", "1"},
        transitions={
            "s": {"0": "s", "1": "s"},
            "a": {"0": "b", "1": "b"},
            "b": {"0": "c", "1": "c"},
            "c": {"0": "a", "1": "a"},
        },
        initial_state="s", final_states={"a", "b", "c"},
    )
    right = ExtendedDFA(
        states={0, 1, 2, 3}, input_symbols={"0", "1"},
        transitions={
            0: {"0": 0, "1": 0},
            1: {"0": 2, "1": 3},
            2: {"0": 3, "1": 1},
            3: {"0": 1, "1": 2},
        },
        initial_state=0, final_states={1, 2, 3},
    )
    assert left.is_isomorphic_to(right) is False


def test_both_operands_remain_immutable_and_scope_is_dfa_only() -> None:
    left, right = _cycle(), _renamed_cycle()
    left_before, right_before = deepcopy(left.input_parameters), deepcopy(right.input_parameters)
    assert left.is_isomorphic_to(right) is True
    assert left.input_parameters == left_before
    assert right.input_parameters == right_before
    assert ExtendedDFA.is_isomorphic_to is IsomorphismMixin.is_isomorphic_to
    assert IsomorphismMixin in ExtendedDFA.__mro__
    assert IsomorphismMixin not in ExtendedNFA.__mro__
    assert IsomorphismMixin not in ExtendedGNFA.__mro__
    assert isinstance(left, DFA)
