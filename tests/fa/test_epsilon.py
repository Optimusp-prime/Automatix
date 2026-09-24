"""Epsilon-only reachability, seed validation and source compatibility."""

from copy import deepcopy

import pytest
from automata.base.exceptions import InvalidStateError
from automata.fa.fa import FAStateT

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA


def _nfa() -> ExtendedNFA:
    return ExtendedNFA(
        states={"p", "q", "r", "x", "z"}, input_symbols={"a"},
        transitions={
            "p": {"": {"q", "x"}}, "q": {"": {"r"}},
            "r": {"": {"p"}, "a": {"z"}}, "x": {"": set()},
        }, initial_state="p", final_states={"z"},
    )


@pytest.mark.parametrize(
    ("state", "expected"),
    [("p", {"p", "q", "r", "x"}), ("q", {"p", "q", "r", "x"}),
     ("r", {"p", "q", "r", "x"}), ("x", {"x"}), ("z", {"z"})],
)
def test_epsilon_cycle_branch_and_consuming_edge_ignored(
    state: str, expected: set[str],
) -> None:
    nfa = _nfa()
    result = nfa.epsilon_closure(state)
    assert type(result) is frozenset
    assert result == frozenset(expected)
    assert state in result


def test_epsilon_chain() -> None:
    nfa = ExtendedNFA(
        states={"p", "q", "r"}, input_symbols=set(),
        transitions={"p": {"": {"q"}}, "q": {"": {"r"}}},
        initial_state="p", final_states={"r"},
    )
    assert nfa.epsilon_closure("p") == frozenset({"p", "q", "r"})
    assert nfa.epsilon_closure("q") == frozenset({"q", "r"})


@pytest.mark.parametrize("seeds", [[], ["p"], ["x", "z"], ["p", "z", "p"]])
def test_multisource_matches_union_and_consumes_generator_once(
    seeds: list[str],
) -> None:
    nfa = _nfa()
    expected = frozenset().union(*(nfa.epsilon_closure(q) for q in seeds))
    result = nfa.epsilon_closure_of_set(q for q in seeds)
    assert type(result) is frozenset
    assert result == expected


@pytest.mark.parametrize("invalid", ["missing", None, [], {"p"}])
@pytest.mark.parametrize("multiple", [False, True])
def test_invalid_seed_matches_dfs(invalid: FAStateT, multiple: bool) -> None:
    nfa = _nfa()
    with pytest.raises(InvalidStateError):
        nfa.dfs(invalid)
    with pytest.raises(InvalidStateError):
        if multiple:
            nfa.epsilon_closure_of_set(iter(["p", invalid]))
        else:
            nfa.epsilon_closure(invalid)


def test_none_heterogeneous_states_and_immutability() -> None:
    nfa = ExtendedNFA(
        states={None, "q", 1}, input_symbols={"a"},
        transitions={None: {"": {1}}, 1: {"": {None}, "a": {"q"}}},
        initial_state=None, final_states={"q"},
    )
    before = deepcopy(nfa.input_parameters), dict(vars(nfa))
    assert nfa.epsilon_closure(None) == frozenset({None, 1})
    assert nfa.epsilon_closure_of_set([None, "q"]) == nfa.states
    assert (nfa.input_parameters, vars(nfa)) == before


def test_epsilon_source_compatibility_regression() -> None:
    # Exact n fixture in the mature executed reference.
    n = ExtendedNFA(
        states={"p", "q", "r"}, input_symbols={"a", "b"},
        transitions={
            "p": {"a": {"p", "q"}, "": {"r"}},
            "q": {"b": {"q"}},
            "r": {"a": {"r"}},
        },
        initial_state="p", final_states={"q", "r"},
    )
    assert (sorted(n.epsilon_closure("p")),
            sorted(n.epsilon_closure_of_set({"p"}))) == (["p", "r"], ["p", "r"])


def test_epsilon_closure_is_nfa_only() -> None:
    for cls in (ExtendedDFA, ExtendedGNFA):
        assert not hasattr(cls, "epsilon_closure")
        assert not hasattr(cls, "epsilon_closure_of_set")
