"""Language set operations on extended DFA and NFA classes."""

from copy import deepcopy

import pytest
from automata.base.exceptions import SymbolMismatchError
from automata.fa.dfa import DFA
from automata.fa.nfa import NFA

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.dfa_mixins.set_operations import DFASetOperationsMixin
from automata_extensions.fa.nfa_mixins.set_operations import NFASetOperationsMixin


def _reference_dfa() -> ExtendedDFA:
    """Three-state cycle compatible with the supplied mature examples."""
    return ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a"},
        transitions={
            "0": {"a": "1"}, "1": {"a": "2"}, "2": {"a": "0"},
        },
        initial_state="0", final_states={"0"},
    )


def _dfa_operands() -> tuple[ExtendedDFA, ExtendedDFA]:
    left = ExtendedDFA(
        states={"l0", "la", "unused"}, input_symbols={"a", "b"},
        transitions={
            "l0": {"a": "la", "b": "l0"},
            "la": {"a": "la", "b": "l0"},
            "unused": {"a": "unused", "b": "unused"},
        },
        initial_state="l0", final_states={"la"},
    )
    right = ExtendedDFA(
        states={"r0", "rb"}, input_symbols={"a", "b"},
        transitions={
            "r0": {"a": "r0", "b": "rb"},
            "rb": {"a": "rb", "b": "rb"},
        },
        initial_state="r0", final_states={"rb"},
    )
    return left, right


def _partial_operands() -> tuple[ExtendedDFA, ExtendedDFA]:
    left = ExtendedDFA(
        states={"l"}, input_symbols={"a", "b"},
        transitions={"l": {"a": "l"}}, initial_state="l",
        final_states={"l"}, allow_partial=True,
    )
    right = ExtendedDFA(
        states={"r"}, input_symbols={"a", "b"},
        transitions={"r": {"b": "r"}}, initial_state="r",
        final_states={"r"}, allow_partial=True,
    )
    return left, right


def test_source_compatibility_dfa_intersection() -> None:
    d = _reference_dfa()
    assert d.intersection(d) == d


def test_source_compatibility_dfa_difference() -> None:
    d = _reference_dfa()
    assert d.difference(d).is_empty() is True


def test_source_compatibility_dfa_union() -> None:
    d = _reference_dfa()
    assert d.union(d).accepts_input("aaa") is True


def test_source_compatibility_nfa_intersection() -> None:
    n1 = ExtendedNFA.from_regex("(a|b)*a", input_symbols={"a", "b"})
    n2 = ExtendedNFA.from_regex("(a|b)*b", input_symbols={"a", "b"})
    assert type(n1) is ExtendedNFA
    assert type(n2) is ExtendedNFA
    assert n1.intersection(n2).accepts_input("ab") is False


@pytest.mark.parametrize("word", ["", "a", "b", "ba", "ab", "bbb", "aab"])
def test_dfa_language_boolean_operations(word: str) -> None:
    left, right = _dfa_operands()
    union = left.union(right)
    intersection = left.intersection(right)
    difference = left.difference(right)
    assert union.accepts(word) is (left.accepts(word) or right.accepts(word))
    assert intersection.accepts(word) is (
        left.accepts(word) and right.accepts(word)
    )
    assert difference.accepts(word) is (
        left.accepts(word) and not right.accepts(word)
    )
    assert all(type(result) is ExtendedDFA for result in
               (union, intersection, difference))


def test_dfa_results_use_reachable_pairs_without_minification() -> None:
    left, right = _dfa_operands()
    result = left.union(right)
    assert result.initial_state == ("l0", "r0")
    assert ("unused", "r0") not in result.states
    assert result.states == {
        ("l0", "r0"), ("la", "r0"),
        ("l0", "rb"), ("la", "rb"),
    }
    assert result.final_states == {
        ("la", "r0"), ("l0", "rb"), ("la", "rb"),
    }
    assert type(result.trim().minimize()) is ExtendedDFA


def test_dfa_partial_operators_handle_missing_edges() -> None:
    left, right = _partial_operands()
    union = left.union(right)
    intersection = left.intersection(right)
    difference = left.difference(right)
    assert union.accepts("") is True
    assert union.accepts("a") is True
    assert union.accepts("b") is True
    assert union.accepts("ab") is False
    assert intersection.accepts("") is True
    assert intersection.accepts("a") is False
    assert intersection.accepts("b") is False
    assert difference.accepts("") is False
    assert difference.accepts("a") is True
    assert difference.accepts("b") is False
    assert difference.accepts("ab") is False
    assert intersection.is_empty() is False
    assert left.difference(left).is_empty() is True


def test_dfa_difference_with_empty_right_preserves_left_language() -> None:
    left, _ = _dfa_operands()
    empty = ExtendedDFA(
        states={"e"}, input_symbols={"a", "b"},
        transitions={"e": {"a": "e", "b": "e"}},
        initial_state="e", final_states=set(),
    )
    result = left.difference(empty)
    assert result.is_equivalent(left) is True
    assert result.accepts("a") is True
    assert result.accepts("") is False


@pytest.mark.parametrize("method", ["union", "intersection", "difference"])
def test_explicit_minification_uses_existing_extension_method(method: str) -> None:
    left, right = _dfa_operands()
    unminimized = getattr(left, method)(right)
    minimized = getattr(left, method)(right, minify=True, retain_names=True)
    assert type(minimized) is ExtendedDFA
    assert minimized.is_minimal() is True
    assert minimized.is_equivalent(unminimized) is True
    assert len(minimized.states) <= len(unminimized.states)


@pytest.mark.parametrize("method", ["union", "intersection", "difference"])
def test_dfa_mismatched_alphabets_raise(method: str) -> None:
    left, _ = _dfa_operands()
    other = ExtendedDFA(
        states={"q"}, input_symbols={"c"},
        transitions={"q": {"c": "q"}},
        initial_state="q", final_states={"q"},
    )
    with pytest.raises(SymbolMismatchError):
        getattr(left, method)(other)


def test_dfa_epsilon_none_heterogeneous_and_upstream_operand() -> None:
    left = ExtendedDFA(
        states={None, 1}, input_symbols={"a"},
        transitions={None: {"a": 1}, 1: {"a": 1}},
        initial_state=None, final_states={None},
    )
    right = DFA(
        states={"q"}, input_symbols={"a"},
        transitions={"q": {"a": "q"}}, initial_state="q",
        final_states=set(),
    )
    for result in (left.union(right), left.intersection(right),
                   left.difference(right)):
        assert type(result) is ExtendedDFA
        assert result.initial_state[0] is None
    assert left.union(right).accepts("") is True
    assert left.intersection(right).is_empty() is True
    assert left.difference(right).accepts("") is True


def test_dfa_operations_leave_both_operands_unchanged() -> None:
    left, right = _dfa_operands()
    before_left = deepcopy(left.input_parameters), left.allow_partial
    before_right = deepcopy(right.input_parameters), right.allow_partial
    for method in ("union", "intersection", "difference"):
        result = getattr(left, method)(right)
        assert result is not left and result is not right
    assert (left.input_parameters, left.allow_partial) == before_left
    assert (right.input_parameters, right.allow_partial) == before_right


def test_nfa_union_and_intersection_with_epsilon() -> None:
    left = ExtendedNFA(
        states={"l0", "l1"}, input_symbols={"a"},
        transitions={"l0": {"": {"l1"}}, "l1": {"a": {"l1"}}},
        initial_state="l0", final_states={"l1"},
    )
    right = ExtendedNFA(
        states={"r0", "r1", "rf"}, input_symbols={"a"},
        transitions={"r0": {"a": {"r1"}}, "r1": {"": {"rf"}}},
        initial_state="r0", final_states={"rf"},
    )
    union = left.union(right)
    intersection = left.intersection(right)
    assert type(union) is ExtendedNFA
    assert type(intersection) is ExtendedNFA
    assert union.accepts("") is True
    assert union.accepts("a") is True
    assert union.accepts("aa") is True
    assert intersection.accepts("") is False
    assert intersection.accepts("a") is True
    assert intersection.accepts("aa") is False
    assert type(union.determinize()) is ExtendedDFA


def test_nfa_mismatched_alphabets_use_upstream_union_policy() -> None:
    left = ExtendedNFA(
        states={"l"}, input_symbols={"a"}, transitions={"l": {"a": {"l"}}},
        initial_state="l", final_states={"l"},
    )
    right = ExtendedNFA(
        states={"r"}, input_symbols={"b"}, transitions={"r": {"b": {"r"}}},
        initial_state="r", final_states={"r"},
    )
    for result in (left.union(right), left.intersection(right)):
        assert result.input_symbols == {"a", "b"}
        assert type(result) is ExtendedNFA
    assert left.union(right).accepts("a") is True
    assert left.union(right).accepts("b") is True
    assert left.intersection(right).accepts("") is True
    assert left.intersection(right).accepts("a") is False


def test_nfa_operations_leave_both_operands_unchanged() -> None:
    left = ExtendedNFA.from_regex("a*", input_symbols={"a"})
    right = ExtendedNFA.from_regex("aa", input_symbols={"a"})
    before_left = deepcopy(left.input_parameters)
    before_right = deepcopy(right.input_parameters)
    assert left.union(right) is not left
    assert left.intersection(right) is not right
    assert left.input_parameters == before_left
    assert right.input_parameters == before_right


def test_mro_and_scope_of_named_operations() -> None:
    assert DFASetOperationsMixin in ExtendedDFA.__mro__
    assert NFASetOperationsMixin in ExtendedNFA.__mro__
    for method in ("union", "intersection", "difference"):
        assert getattr(ExtendedDFA, method) is getattr(DFASetOperationsMixin, method)
    for method in ("union", "intersection"):
        assert getattr(ExtendedNFA, method) is getattr(NFASetOperationsMixin, method)
    assert DFASetOperationsMixin not in ExtendedNFA.__mro__
    assert NFASetOperationsMixin not in ExtendedDFA.__mro__
    assert not hasattr(ExtendedNFA, "difference")
    assert not hasattr(ExtendedGNFA, "difference")
