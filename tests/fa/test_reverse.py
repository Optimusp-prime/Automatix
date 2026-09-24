"""Language reversal through the upstream NFA engine."""

from copy import deepcopy
from itertools import product

import pytest
from automata.fa.nfa import NFA

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.fa_mixins.reverse import ReverseMixin


def _dfa() -> ExtendedDFA:
    return ExtendedDFA(
        states={"s", "p", "f"}, input_symbols={"a", "b"},
        transitions={"s": {"a": "p"}, "p": {"b": "f"}, "f": {}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )


def _nfa() -> ExtendedNFA:
    return ExtendedNFA(
        states={"s", "p", "q", "f"}, input_symbols={"a", "b"},
        transitions={"s": {"": {"p"}, "a": {"p", "q"}},
                     "p": {"b": {"q"}}, "q": {"": {"f"}},
                     "f": {"a": {"s"}, "b": {"f"}}},
        initial_state="s", final_states={"p", "f"},
    )


def test_ab_dfa_reversal_and_incorrect_word() -> None:
    source = _dfa()
    result = source.reverse()
    assert type(result) is ExtendedNFA
    assert result.accepts("ba") is True
    assert result.accepts("ab") is False
    assert result.accepts("a") is False
    assert result.final_states == {source.initial_state}
    assert result.input_symbols == source.input_symbols
    assert result.transitions["p"]["a"] == {"s"}
    assert result.transitions["f"]["b"] == {"p"}
    assert result.transitions[result.initial_state][""] == source.final_states


@pytest.mark.parametrize("nondeterministic", [False, True])
@pytest.mark.parametrize("length", range(5))
def test_reversal_and_double_reversal_language(
    nondeterministic: bool, length: int,
) -> None:
    source = _nfa() if nondeterministic else _dfa()
    result = source.reverse()
    twice = result.reverse()
    for symbols in product("ab", repeat=length):
        word = "".join(symbols)
        assert result.accepts(word[::-1]) is source.accepts(word)
        assert twice.accepts(word) is source.accepts(word)


def test_multiple_finals_and_reversed_epsilon_edges_match_upstream() -> None:
    source = _nfa()
    result = source.reverse()
    reference = NFA.reverse(source)
    assert result.states == reference.states
    assert result.transitions == reference.transitions
    assert result.initial_state == reference.initial_state
    assert result.final_states == reference.final_states
    assert result.transitions[result.initial_state][""] == {"p", "f"}
    assert result.transitions["p"][""] == {"s"}
    assert result.transitions["f"][""] == {"q"}


@pytest.mark.parametrize("nondeterministic", [False, True])
@pytest.mark.parametrize("accepting", [False, True])
def test_no_finals_or_initial_final_with_empty_alphabet(
    nondeterministic: bool, accepting: bool,
) -> None:
    cls = ExtendedNFA if nondeterministic else ExtendedDFA
    source = cls(
        states={"q"}, input_symbols=set(), transitions={"q": {}},
        initial_state="q", final_states={"q"} if accepting else set(),
    )
    result = source.reverse()
    assert result is not source
    assert result.accepts("") is accepting
    assert result.accepts("a") is False
    assert result.is_empty() is (not accepting)
    assert result.states == source.states | {result.initial_state}
    assert result.initial_state not in source.states


@pytest.mark.parametrize("nondeterministic", [False, True])
def test_none_heterogeneous_states_and_new_initial_collision(
    nondeterministic: bool,
) -> None:
    if nondeterministic:
        source: ExtendedDFA | ExtendedNFA = ExtendedNFA(
            states={None, 0, 1, "f"}, input_symbols={"a"},
            transitions={None: {"a": {"f"}}, "f": {"": {1}}},
            initial_state=None, final_states={"f"},
        )
    else:
        source = ExtendedDFA(
            states={None, 0, 1, "f"}, input_symbols={"a"},
            transitions={None: {"a": "f"}, 0: {}, 1: {}, "f": {}},
            initial_state=None, final_states={"f"}, allow_partial=True,
        )
    before = deepcopy(source.input_parameters), dict(vars(source))
    result = source.reverse()
    assert result.initial_state == 2
    assert result.final_states == {None}
    assert result.states == {None, 0, 1, 2, "f"}
    assert result.transitions["f"]["a"] == {None}
    assert (source.input_parameters, vars(source)) == before
    # NFA reading with None is an upstream limitation; #35 supplies an
    # equivalent readable DFA without modifying that upstream behavior.
    assert result.determinize().accepts("a") is True


@pytest.mark.parametrize("nondeterministic", [False, True])
def test_source_immutable_and_extended_composition(nondeterministic: bool) -> None:
    source = _nfa() if nondeterministic else _dfa()
    before = deepcopy(source.input_parameters), dict(vars(source))
    result = source.reverse()
    assert result is not source
    assert type(result) is ExtendedNFA
    assert (source.input_parameters, vars(source)) == before
    converted = result.determinize()
    assert type(converted) is ExtendedDFA
    assert converted.is_equivalent(result.to_dfa())


def test_reverse_source_compatibility_regression() -> None:
    # Three-state cycle consistent with the supplied mature example.
    d = ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a"},
        transitions={"0": {"a": "1"}, "1": {"a": "2"}, "2": {"a": "0"}},
        initial_state="0", final_states={"0"},
    )
    assert d.reverse().accepts_input("aaa") is True


def test_reverse_mro_and_gnfa_scope() -> None:
    for cls in (ExtendedDFA, ExtendedNFA):
        assert cls.reverse is ReverseMixin.reverse
        assert cls.__mro__.count(ReverseMixin) == 1
    assert ExtendedNFA.__mro__.index(ReverseMixin) < ExtendedNFA.__mro__.index(NFA)
    assert ReverseMixin not in ExtendedGNFA.__mro__
    assert not hasattr(ExtendedGNFA, "reverse")
