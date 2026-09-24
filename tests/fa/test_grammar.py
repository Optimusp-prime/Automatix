"""Right-linear grammar conversion, professor requirement #55."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from itertools import product

import pytest

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.fa_mixins.grammar_fa import GrammarMixin
from automata_extensions.grammar import Grammar


def _words(alphabet: str, max_length: int = 4) -> list[str]:
    return [
        "".join(letters)
        for length in range(max_length + 1)
        for letters in product(alphabet, repeat=length)
    ]


def _dfa(
    *,
    states: set[object],
    transitions: dict[object, dict[str, object]],
    initial: object,
    finals: set[object],
) -> ExtendedDFA:
    return ExtendedDFA(
        states=states, input_symbols={"a", "b"},
        transitions=transitions, initial_state=initial,
        final_states=finals, allow_partial=True,
    )


def test_mature_type_name_and_approved_source_divergence() -> None:
    dfa = _dfa(
        states={"S"}, transitions={"S": {"a": "S"}},
        initial="S", finals={"S"},
    )
    assert type(dfa.to_grammar()).__name__ == "Grammar"

    nfa = ExtendedNFA.from_grammar_string("S -> aS | b")
    assert type(nfa) is ExtendedNFA
    for word in ("b", "ab", "aab", "aaab"):
        assert nfa.accepts_input(word) is True
    for word in ("", "a", "ba", "bb"):
        assert nfa.accepts_input(word) is False


@pytest.mark.parametrize(
    ("transitions", "finals"),
    [({"q": {}}, set()), ({"q": {}}, {"q"}),
     ({"q": {"a": "q"}}, {"q"})],
)
def test_one_state_dfa_round_trip(
    transitions: dict[object, dict[str, object]], finals: set[object],
) -> None:
    dfa = _dfa(states={"q"}, transitions=transitions, initial="q", finals=finals)
    grammar = dfa.to_grammar()
    rebuilt = ExtendedNFA.from_grammar(grammar)
    assert grammar.nonterminals == frozenset({"q"})
    assert grammar.start_symbol == "q"
    assert all(dfa.accepts_input(w) is rebuilt.accepts_input(w) for w in _words("ab"))


def test_partial_multiple_finals_and_inaccessible_state_round_trip() -> None:
    dfa = _dfa(
        states={"q0", "q1", "q2", "isolated"},
        transitions={
            "q0": {"a": "q1", "b": "q2"},
            "q1": {"a": "q1"}, "q2": {},
            "isolated": {"b": "isolated"},
        }, initial="q0", finals={"q1", "q2", "isolated"},
    )
    before = deepcopy(dfa.input_parameters)
    grammar = dfa.to_grammar()
    rebuilt = ExtendedNFA.from_grammar(grammar)
    assert grammar.nonterminals == frozenset(dfa.states)
    assert ("isolated", "", None) in grammar.productions
    assert ("q0", "a", "q1") in grammar.productions
    assert all(dfa.accepts_input(w) is rebuilt.accepts_input(w) for w in _words("ab"))
    assert dfa.input_parameters == before


def test_nfa_nondeterminism_and_epsilon_round_trip() -> None:
    nfa = ExtendedNFA(
        states={"s", "p", "r", "f"}, input_symbols={"a", "b"},
        transitions={
            "s": {"": {"p"}, "a": {"p", "r"}},
            "p": {"a": {"p"}, "b": {"f"}},
            "r": {"b": {"f"}}, "f": {},
        }, initial_state="s", final_states={"f"},
    )
    before = deepcopy(nfa.input_parameters)
    grammar = nfa.to_grammar()
    rebuilt = ExtendedNFA.from_grammar(grammar)
    assert ("s", "", "p") in grammar.productions
    assert ("s", "a", "p") in grammar.productions
    assert ("s", "a", "r") in grammar.productions
    assert all(nfa.accepts_input(w) is rebuilt.accepts_input(w) for w in _words("ab"))
    assert nfa.input_parameters == before


def test_structural_unit_epsilon_terminal_and_multichar_words() -> None:
    grammar = Grammar(
        terminals={"a", "b", "c"}, nonterminals={"S", "A", "B"},
        start_symbol="S",
        productions={
            ("S", "", "A"), ("A", "", None),
            ("S", "abc", "B"), ("B", "b", None),
            ("S", "ab", None),
        },
    )
    before = deepcopy(grammar)
    nfa = ExtendedNFA.from_grammar(grammar)
    assert type(nfa) is ExtendedNFA
    for word in ("", "ab", "abcb"):
        assert nfa.accepts_input(word) is True
    for word in ("a", "abc", "abb", "abcbc"):
        assert nfa.accepts_input(word) is False
    assert nfa.input_symbols == grammar.terminals
    assert len(nfa.states) > len(grammar.nonterminals)
    assert grammar == before


def test_text_multiple_lines_epsilon_unit_and_longest_declared_suffix() -> None:
    nfa = ExtendedNFA.from_grammar_string(
        "S -> () | aAB | B\nAB -> b\nB -> c"
    )
    assert nfa.accepts_input("") is True
    assert nfa.accepts_input("ab") is True
    assert nfa.accepts_input("c") is True
    assert nfa.accepts_input("aAc") is False


@pytest.mark.parametrize("text", [
    "S a", " -> a", "1S -> a", "S ->", "S -> a | ",
    "S -> aT", "S -> a()", "S -> a -> b", "",
])
def test_malformed_text_rejected(text: str) -> None:
    with pytest.raises(ValueError):
        ExtendedNFA.from_grammar_string(text)


def test_repeated_lhs_lines_are_additive() -> None:
    nfa = ExtendedNFA.from_grammar_string("S -> a\nS -> b")
    assert nfa.accepts_input("a") is True
    assert nfa.accepts_input("b") is True
    assert nfa.accepts_input("ab") is False


def test_empty_and_epsilon_language_grammars() -> None:
    empty = Grammar(
        terminals={"a"}, nonterminals={"S"},
        start_symbol="S", productions=set(),
    )
    epsilon = Grammar(
        terminals={"a"}, nonterminals={"S"},
        start_symbol="S", productions={("S", "", None)},
    )
    empty_nfa = ExtendedNFA.from_grammar(empty)
    epsilon_nfa = ExtendedNFA.from_grammar(epsilon)
    assert all(not empty_nfa.accepts_input(w) for w in _words("a"))
    assert epsilon_nfa.accepts_input("") is True
    assert all(not epsilon_nfa.accepts_input(w) for w in _words("a") if w)


def test_grammar_immutability_and_validation() -> None:
    terminals = {"a"}
    productions = {("S", "a", None)}
    grammar = Grammar(
        terminals=terminals, nonterminals={"S"},
        start_symbol="S", productions=productions,
    )
    terminals.add("b")
    productions.clear()
    assert grammar.terminals == frozenset({"a"})
    assert grammar.productions == frozenset({("S", "a", None)})
    with pytest.raises(FrozenInstanceError):
        setattr(grammar, "start_symbol", "T")
    with pytest.raises(ValueError):
        Grammar(terminals={"ab"}, nonterminals={"S"}, start_symbol="S", productions=set())
    with pytest.raises(ValueError):
        Grammar(terminals={"a"}, nonterminals={"S"}, start_symbol="S",
                productions={("S", "b", None)})


def test_deterministic_collision_safe_names_for_heterogeneous_states() -> None:
    states: set[object] = {None, 0, "Q0", "q", "bad-name"}
    transitions = {state: {"a": state, "b": state} for state in states}
    dfa = _dfa(states=states, transitions=transitions, initial=None, finals={None})
    grammar1 = dfa.to_grammar()
    grammar2 = dfa.to_grammar()
    assert grammar1 == grammar2
    assert len(grammar1.nonterminals) == len(states)
    assert {"Q0", "q"} <= grammar1.nonterminals
    rebuilt = ExtendedNFA.from_grammar(grammar1)
    assert all(dfa.accepts_input(w) is rebuilt.accepts_input(w) for w in _words("ab"))


def test_public_mro_and_gnfa_exclusion() -> None:
    assert GrammarMixin in ExtendedDFA.__mro__
    assert GrammarMixin in ExtendedNFA.__mro__
    assert GrammarMixin not in ExtendedGNFA.__mro__
    assert hasattr(ExtendedNFA, "from_grammar")
    assert not hasattr(ExtendedDFA, "from_grammar")
