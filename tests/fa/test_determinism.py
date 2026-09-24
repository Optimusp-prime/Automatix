"""Determinism is uniqueness of symbol targets, not completeness."""

from copy import deepcopy

import pytest
from automata.fa.fa import FAStateT

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.fa_mixins.determinism import DeterminismMixin


@pytest.mark.parametrize("partial", [False, True])
def test_dfa_source_compatibility_regression(partial: bool) -> None:
    # Supplied mature contract: d.is_deterministic() -> True.
    d = ExtendedDFA(
        states={"q"}, input_symbols={"a"},
        transitions={"q": {} if partial else {"a": "q"}},
        initial_state="q", final_states={"q"}, allow_partial=partial,
    )
    before = deepcopy(d.input_parameters), dict(vars(d))
    assert d.is_deterministic() is True
    assert d.is_complete() is (not partial)
    assert (d.input_parameters, vars(d)) == before


@pytest.mark.parametrize(
    ("paths", "expected"),
    [({}, True), ({"a": set()}, True), ({"a": {"q"}}, True),
     ({"a": {"q"}, "b": {"r"}}, True),
     ({"a": {"q", "r"}}, False), ({"": {"q"}}, False),
     ({"": {"r"}, "a": {"q"}}, False), ({"": set()}, True)],
)
def test_nfa_determinism(
    paths: dict[str, set[str]], expected: bool,
) -> None:
    nfa = ExtendedNFA(
        states={"q", "r"}, input_symbols={"a", "b"},
        transitions={"q": paths}, initial_state="q", final_states={"r"},
    )
    before = deepcopy(nfa.input_parameters), dict(vars(nfa))
    result = nfa.is_deterministic()
    assert type(result) is bool
    assert result is expected
    assert (nfa.input_parameters, vars(nfa)) == before


def test_unreachable_branching_still_makes_nfa_nondeterministic() -> None:
    nfa = ExtendedNFA(
        states={"q", "x", "y"}, input_symbols={"a"},
        transitions={"q": {}, "x": {"a": {"x", "y"}}},
        initial_state="q", final_states=set(),
    )
    assert nfa.is_deterministic() is False


def test_none_heterogeneous_and_set_valued_dfa_states() -> None:
    states: set[FAStateT] = {None, 1, "q", frozenset({"x", "y"})}
    dfa = ExtendedDFA(
        states=states, input_symbols={"a"},
        transitions={q: {"a": frozenset({"x", "y"})} for q in states},
        initial_state=None, final_states={1},
    )
    nfa = ExtendedNFA(
        states=states, input_symbols={"a"},
        transitions={None: {"a": {1}}, 1: {"a": {"q"}}},
        initial_state=None, final_states={"q"},
    )
    assert dfa.is_deterministic() is True
    assert nfa.is_deterministic() is True


def test_determinism_mro_and_gnfa_scope() -> None:
    for cls in (ExtendedDFA, ExtendedNFA):
        assert cls.is_deterministic is DeterminismMixin.is_deterministic
        assert cls.__mro__.count(DeterminismMixin) == 1
    assert DeterminismMixin not in ExtendedGNFA.__mro__
    assert not hasattr(ExtendedGNFA, "is_deterministic")
