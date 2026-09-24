"""Requirement #39 delegates normalized GNFA state elimination upstream."""

from copy import deepcopy
from itertools import product

import pytest
from automata.fa.gnfa import GNFA
from automata.fa.nfa import NFA

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA


def _mature_dfa() -> ExtendedDFA:
    # This transition table yields both exact examples supplied for #39/#40.
    return ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a", "b"},
        transitions={
            "0": {"b": "0", "a": "1"},
            "1": {"b": "1", "a": "2"},
            "2": {"a": "0", "b": "2"},
        },
        initial_state="0", final_states={"0"},
    )


def _direct_gnfa(label: str | None) -> ExtendedGNFA:
    return ExtendedGNFA(
        states={"s", "f"}, input_symbols={"a", "b"},
        transitions={"s": {"f": label}},
        initial_state="s", final_state="f",
    )


@pytest.mark.parametrize(
    ("label", "expected"),
    [("a", "a"), ("a|b", "a|b"), ("a*", "a*"), ("", "")],
)
def test_direct_gnfa_path_union_loop_and_epsilon(
    label: str, expected: str,
) -> None:
    gnfa = _direct_gnfa(label)
    assert type(gnfa.to_regex()) is str
    assert gnfa.to_regex() == expected


def test_language_empty_uses_upstream_none_convention() -> None:
    gnfa = _direct_gnfa(None)
    assert GNFA.to_regex(gnfa) is None
    assert gnfa.to_regex() is None  # Upstream annotation says str; runtime differs.


def test_multiple_intermediate_states_and_language() -> None:
    dfa = _mature_dfa()
    gnfa = ExtendedGNFA.from_dfa(dfa)
    regex = gnfa.to_regex()
    assert isinstance(gnfa, ExtendedGNFA)
    assert isinstance(regex, str)
    converted = NFA.from_regex(regex, input_symbols=dfa.input_symbols)
    for length in range(5):
        for symbols in product("ab", repeat=length):
            word = "".join(symbols)
            assert converted.accepts_input(word) is dfa.accepts(word)


def test_state_elimination_mature_source_compatibility_exact() -> None:
    d = _mature_dfa()
    assert GNFA.from_dfa(d).to_regex() == "(ab*ab*a|b)*"
    assert ExtendedGNFA.from_dfa(d).to_regex() == "(ab*ab*a|b)*"


def test_inherited_upstream_method_and_source_immutability() -> None:
    gnfa = ExtendedGNFA.from_dfa(_mature_dfa())
    before = deepcopy(gnfa.input_parameters), dict(vars(gnfa))
    assert ExtendedGNFA.to_regex is GNFA.to_regex
    assert isinstance(gnfa.to_regex(), str)
    assert (gnfa.input_parameters, vars(gnfa)) == before
    assert len(gnfa.states) > 2  # Intermediates eliminated locally, not in self.


def test_none_and_heterogeneous_gnfa_states() -> None:
    gnfa = ExtendedGNFA(
        states={None, (1, "middle"), 2}, input_symbols={"a"},
        transitions={
            None: {(1, "middle"): "a", 2: None},
            (1, "middle"): {(1, "middle"): None, 2: "a"},
        },
        initial_state=None, final_state=2,
    )
    before = deepcopy(gnfa.input_parameters), dict(vars(gnfa))
    assert gnfa.to_regex() == "aa"
    assert (gnfa.input_parameters, vars(gnfa)) == before
