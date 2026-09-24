"""Epsilon propagation preserves the NFA language and every original state."""

from copy import deepcopy
from itertools import product

import pytest
from automata.fa.nfa import NFA

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.nfa_mixins.elimination import EliminationMixin


def _nfa() -> ExtendedNFA:
    return ExtendedNFA(
        states={"s", "p", "q", "r", "f", "unused"}, input_symbols={"a", "b"},
        transitions={
            "s": {"": {"p", "q"}}, "p": {"": {"s"}, "a": {"r"}},
            "q": {"b": {"r"}}, "r": {"": {"f"}},
            "f": {"b": {"f"}}, "unused": {"": {"unused"}},
        }, initial_state="s", final_states={"f"},
    )


def test_epsilon_propagation_before_and_after_symbols() -> None:
    source = _nfa()
    result = source.remove_epsilon_transitions()
    assert result.transitions["s"] == {"a": {"r", "f"}, "b": {"r", "f"}}
    assert result.transitions["p"] == result.transitions["s"]
    assert result.transitions["r"] == {"b": {"f"}}
    assert result.transitions["unused"] == {}
    assert result.final_states == {"r", "f"}
    assert all("" not in paths for paths in result.transitions.values())
    assert result.states == source.states
    assert result.initial_state == source.initial_state
    assert result.input_symbols == source.input_symbols


@pytest.mark.parametrize("length", range(5))
def test_language_and_determinization_composition(length: int) -> None:
    source = _nfa()
    cleaned = source.remove_epsilon_transitions()
    before = source.determinize()
    after = cleaned.determinize()
    assert after.is_equivalent(before)
    for symbols in product("ab", repeat=length):
        word = "".join(symbols)
        assert cleaned.accepts(word) is source.accepts(word)
        assert after.accepts(word) is before.accepts(word)


@pytest.mark.parametrize("accepting", [False, True])
def test_epsilon_chain_propagates_empty_word_finality(accepting: bool) -> None:
    source = ExtendedNFA(
        states={"p", "q", "r"}, input_symbols=set(),
        transitions={"p": {"": {"q"}}, "q": {"": {"r"}}},
        initial_state="p", final_states={"r"} if accepting else set(),
    )
    result = source.remove_epsilon_transitions()
    assert result.final_states == (source.states if accepting else frozenset())
    assert result.accepts("") is source.accepts("") is accepting
    assert result.transitions == {"p": {}, "q": {}, "r": {}}


def test_without_epsilon_preserves_nondeterminism_and_unreachable_states() -> None:
    source = ExtendedNFA(
        states={"s", "p", "f", "unused"}, input_symbols={"a", "b"},
        transitions={"s": {"a": {"p", "f"}, "b": set()}, "p": {"b": {"f"}}},
        initial_state="s", final_states={"f", "unused"},
    )
    result = source.remove_epsilon_transitions()
    assert result.is_deterministic() is False
    assert result.states == source.states
    assert result.final_states == source.final_states
    assert result.transitions["s"]["a"] == {"p", "f"}
    for word in ("", "a", "ab", "b", "aa"):
        assert result.accepts(word) is source.accepts(word)


def test_none_heterogeneous_states_and_finality() -> None:
    source = ExtendedNFA(
        states={None, 1, "f"}, input_symbols={"a"},
        transitions={None: {"": {1}}, 1: {"a": {None}, "": {"f"}}},
        initial_state=None, final_states={"f"},
    )
    result = source.remove_epsilon_transitions()
    alias = source.eliminate_lambda()
    assert result.initial_state is None
    assert result.states == source.states == result.final_states
    assert result.transitions[None]["a"] == {None, 1, "f"}
    assert alias.transitions == result.transitions
    assert all("" not in paths for paths in alias.transitions.values())
    assert result.determinize().is_equivalent(source.determinize())


def test_source_immutable_and_alias_retains_unreachable_states() -> None:
    source = _nfa()
    before = deepcopy(source.input_parameters), dict(vars(source))
    result = source.remove_epsilon_transitions()
    alias = source.eliminate_lambda()
    assert type(result) is type(alias) is ExtendedNFA
    assert result is not source and alias is not source and alias is not result
    assert result.states == alias.states == source.states
    assert alias.transitions == result.transitions
    assert alias.final_states == result.final_states
    assert (source.input_parameters, vars(source)) == before


def test_elimination_source_compatibility_regression() -> None:
    # Minimal compatible example; the original mature fixture was not supplied.
    n = ExtendedNFA(
        states={"p", "r", "f"}, input_symbols={"a"},
        transitions={"p": {"": {"r"}}, "r": {"a": {"f"}}},
        initial_state="p", final_states={"f"},
    )
    assert n.remove_epsilon_transitions().accepts_input("a") is True
    assert n.eliminate_lambda().accepts_input("a") is True


def test_elimination_mro_and_nfa_only_scope() -> None:
    assert ExtendedNFA.eliminate_lambda is EliminationMixin.eliminate_lambda
    assert ExtendedNFA.__mro__.index(EliminationMixin) < ExtendedNFA.__mro__.index(NFA)
    for cls in (ExtendedDFA, ExtendedGNFA):
        assert EliminationMixin not in cls.__mro__
        assert not hasattr(cls, "remove_epsilon_transitions")
