"""Accessible subset construction and NFA language preservation."""

from collections.abc import Mapping
from copy import deepcopy
from itertools import product
from typing import cast

import pytest
from automata.fa.dfa import DFA
from automata.fa.fa import FAStateT

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.nfa_mixins.determinization import DeterminizationMixin
from automata_extensions.fa.nfa_mixins.epsilon import EpsilonMixin


def _branching_nfa() -> ExtendedNFA:
    return ExtendedNFA(
        states={"s", "p", "q", "f", "g", "unreachable"},
        input_symbols={"a", "b"},
        transitions={
            "s": {"": {"p"}}, "p": {"": {"s"}, "a": {"p", "q"}},
            "q": {"": {"f"}, "b": {"g"}},
            "f": {"b": {"g"}}, "g": {"b": {"g"}},
            "unreachable": {"a": {"unreachable"}},
        }, initial_state="s", final_states={"f", "g"},
    )


def test_only_reachable_subsets_and_exact_transition_rule() -> None:
    nfa = _branching_nfa()
    result = nfa.determinize()
    start = frozenset({"s", "p"})
    after_a = frozenset({"s", "p", "q", "f"})
    after_b = frozenset({"g"})
    expected = {start: {"a": after_a},
                after_a: {"a": after_a, "b": after_b},
                after_b: {"b": after_b}}
    assert result.states == frozenset(expected)
    assert cast(Mapping[FAStateT, Mapping[str, FAStateT]], result.transitions) == expected
    assert result.initial_state == start
    assert result.final_states == frozenset({after_a, after_b})
    assert len(result.states) < 2 ** len(nfa.states)
    assert all(type(state) is frozenset for state in result.states)
    assert all("unreachable" not in state for state in result.states)
    assert result.accessible_states() == result.states
    assert result.is_deterministic() is True


@pytest.mark.parametrize("length", range(5))
def test_language_preserved_for_all_short_words(length: int) -> None:
    nfa = _branching_nfa()
    result = nfa.determinize()
    for symbols in product("ab", repeat=length):
        word = "".join(symbols)
        assert result.accepts(word) is nfa.accepts(word)


@pytest.mark.parametrize("initial_final", [False, True])
@pytest.mark.parametrize("alphabet", [set(), {"a"}])
def test_no_edges_empty_language_or_epsilon_only(
    initial_final: bool, alphabet: set[str],
) -> None:
    nfa = ExtendedNFA(
        states={"s"}, input_symbols=alphabet, transitions={"s": {}},
        initial_state="s", final_states={"s"} if initial_final else set(),
    )
    result = nfa.determinize()
    assert result.states == frozenset({frozenset({"s"})})
    assert result.accepts("") is initial_final
    assert result.accepts("a") is False
    assert result.input_symbols == nfa.input_symbols
    assert result.allow_partial is bool(alphabet)
    assert result.is_complete() is (not alphabet)


def test_epsilon_accepts_empty_word_and_closes_after_consumption() -> None:
    nfa = ExtendedNFA(
        states={"s", "p", "q", "f"}, input_symbols={"a"},
        transitions={"s": {"": {"p"}}, "p": {"a": {"q"}},
                     "q": {"": {"f"}}},
        initial_state="s", final_states={"p", "f"},
    )
    result = nfa.determinize()
    assert result.final_states == result.states
    assert result.states == {frozenset({"s", "p"}), frozenset({"q", "f"})}
    assert result.accepts("") is True
    assert result.accepts("a") is True
    assert result.accepts("aa") is False


def test_already_deterministic_nfa_and_no_implicit_minimization() -> None:
    nfa = ExtendedNFA(
        states={"s", "p"}, input_symbols={"a"},
        transitions={"s": {"a": {"p"}}, "p": {"a": {"p"}}},
        initial_state="s", final_states={"s", "p"},
    )
    assert nfa.is_deterministic() is True
    result = nfa.determinize()
    assert result.states == {frozenset({"s"}), frozenset({"p"})}
    assert result.allow_partial is False
    assert result.is_complete() is True
    assert result.is_minimal() is False


def test_empty_target_policy_matches_inspected_upstream() -> None:
    nfa = ExtendedNFA(
        states={"p", "r"}, input_symbols={"a", "b"},
        transitions={"p": {"": {"r"}, "b": set()}, "r": {"a": {"r"}}},
        initial_state="p", final_states={"r"},
    )
    result = nfa.determinize()
    reference = DFA.from_nfa(nfa, retain_names=True, minify=False)
    assert result.states == reference.states
    assert result.transitions == reference.transitions
    assert result.final_states == reference.final_states
    assert result.initial_state == reference.initial_state
    assert result.allow_partial is reference.allow_partial is True
    assert frozenset() not in result.states


def test_none_heterogeneous_states_are_preserved_inside_subsets() -> None:
    nfa = ExtendedNFA(
        states={None, 1, "f"}, input_symbols={"a"},
        transitions={None: {"": {1}}, 1: {"a": {None, "f"}}},
        initial_state=None, final_states={"f"},
    )
    result = nfa.determinize()
    start = frozenset({None, 1})
    final = frozenset({None, 1, "f"})
    transitions = cast(Mapping[FAStateT, Mapping[str, FAStateT]], result.transitions)
    assert result.states == {start, final}
    assert transitions[start]["a"] == final
    assert result.final_states == {final}
    # Upstream NFA reading rejects None via NetworkX; the resulting DFA
    # has frozenset states and can be read without that upstream limitation.
    assert result.accepts("") is False
    assert result.accepts("a") is True
    assert result.accepts("aaa") is True


def test_new_extended_result_source_unchanged_and_composable() -> None:
    nfa = _branching_nfa()
    before = deepcopy(nfa.input_parameters), dict(vars(nfa))
    result = nfa.determinize()
    alias = nfa.to_dfa()
    assert type(result) is ExtendedDFA
    assert type(alias) is ExtendedDFA
    assert result is not alias
    assert (nfa.input_parameters, vars(nfa)) == before
    assert result.input_symbols == nfa.input_symbols
    assert result.is_equivalent(alias)
    assert result.complete().is_complete() is True
    assert result.trim().minimize().is_equivalent(result)
    for subset in result.states:
        assert (subset in result.final_states) is bool(subset & nfa.final_states)


def test_determinization_source_compatibility_regression() -> None:
    # Minimal analogue of the supplied mature n example, not its unknown fixture.
    n = ExtendedNFA(
        states={"p", "r", "f"}, input_symbols={"a"},
        transitions={"p": {"": {"r"}}, "r": {"a": {"f"}}},
        initial_state="p", final_states={"f"},
    )
    assert (n.determinize().accepts_input("a"),
            n.to_dfa().accepts_input("a")) == (True, True)
    assert n.determinize().is_equivalent(n.to_dfa())


def test_thompson_nfa_composes_with_to_dfa() -> None:
    """Requirement #52 reuses #35 on an NFA built by requirement #51."""
    nfa = ExtendedNFA.from_regex("(a|b)*a", input_symbols={"a", "b"})
    before = (nfa.states, nfa.transitions, nfa.input_symbols,
              nfa.initial_state, nfa.final_states)
    converted = nfa.to_dfa()
    direct = nfa.determinize()
    assert type(converted) is type(direct) is ExtendedDFA
    assert converted.initial_state == nfa.epsilon_closure(nfa.initial_state)
    assert converted.states == converted.accessible_states()
    assert converted.states == direct.states
    assert converted.transitions == direct.transitions
    assert converted.final_states == direct.final_states
    assert all(type(subset) is frozenset for subset in converted.states)
    assert (nfa.states, nfa.transitions, nfa.input_symbols,
            nfa.initial_state, nfa.final_states) == before
    for length in range(4):
        for symbols in product("ab", repeat=length):
            word = "".join(symbols)
            assert converted.accepts_input(word) == nfa.accepts_input(word)
    assert converted.accepts_input("aba") is True


def test_nfa_mro_and_conversion_scope() -> None:
    assert ExtendedNFA.determinize is DeterminizationMixin.determinize
    assert ExtendedNFA.to_dfa is DeterminizationMixin.to_dfa
    assert ExtendedNFA.epsilon_closure is EpsilonMixin.epsilon_closure
    for mixin in (DeterminizationMixin, EpsilonMixin):
        assert ExtendedNFA.__mro__.count(mixin) == 1
        assert mixin not in ExtendedDFA.__mro__
        assert mixin not in ExtendedGNFA.__mro__
    for cls in (ExtendedDFA, ExtendedGNFA):
        assert not hasattr(cls, "determinize")
