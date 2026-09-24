"""Derivation chains for professor requirement #56."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError

import pytest
from automata.base.exceptions import RejectionException

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.fa_mixins.grammar_fa import GrammarMixin
from automata_extensions.grammar import DerivationStep, Grammar
from tests.fa.test_state_elimination import _mature_dfa


def _grammar(
    productions: set[tuple[str, str, str | None]],
    *, nonterminals: set[str] | None = None,
) -> Grammar:
    return Grammar(
        terminals={"a", "b", "c", "d"},
        nonterminals=nonterminals or {"S"},
        start_symbol="S",
        productions=productions,
    )


def test_exact_mature_sequence_and_word_pair() -> None:
    dfa = _mature_dfa()
    step = dfa.derivation_tree("aaa")
    assert type(step) is DerivationStep
    assert step.sequence() == "0 => a1 => aa2 => aaa0 => aaa"
    assert (step.word(), step.sequence()) == (
        "aaa", "0 => a1 => aa2 => aaa0 => aaa",
    )
    assert step.sequence() == dfa.derivation_tree("aaa").sequence()


def test_grammar_terminal_word_and_multichar_production() -> None:
    grammar = _grammar(
        {("S", "abc", "B"), ("B", "d", None)},
        nonterminals={"S", "B"},
    )
    step = grammar.derivation_tree("abcd")
    assert step.word() == "abcd"
    assert step.sequence() == "S => abcB => abcd"
    assert grammar.derivation_tree("abcd").sequence() == step.sequence()


def test_one_step_terminal_production_and_epsilon() -> None:
    terminal = _grammar({("S", "a", None)})
    epsilon = _grammar({("S", "", None)})
    assert terminal.derivation_tree("a").sequence() == "S => a"
    assert epsilon.derivation_tree("").word() == ""
    assert epsilon.derivation_tree("").sequence() == "S => "


def test_unit_production_and_epsilon_cycle_terminate() -> None:
    grammar = _grammar(
        {("S", "", "A"), ("A", "", "S"), ("A", "b", None)},
        nonterminals={"S", "A"},
    )
    assert grammar.derivation_tree("b").sequence() == "S => A => b"
    with pytest.raises(RejectionException):
        grammar.derivation_tree("")


def test_nondeterministic_branch_and_ambiguous_tie_break() -> None:
    grammar = _grammar(
        {("S", "a", "B"), ("S", "a", "A"),
         ("A", "b", None), ("B", "b", None)},
        nonterminals={"S", "A", "B"},
    )
    assert grammar.derivation_tree("ab").sequence() == "S => aA => ab"
    assert grammar.derivation_tree("ab").sequence() == "S => aA => ab"
    with pytest.raises(RejectionException):
        grammar.derivation_tree("aa")


def test_shortest_rule_derivation_wins() -> None:
    grammar = _grammar(
        {("S", "", "A"), ("A", "a", None), ("S", "a", None)},
        nonterminals={"S", "A"},
    )
    assert grammar.derivation_tree("a").sequence() == "S => a"


def test_empty_language_rejected_without_partial_step() -> None:
    grammar = _grammar(set())
    with pytest.raises(RejectionException):
        grammar.derivation_tree("")


def test_approved_grammar_semantics_remain_intact() -> None:
    grammar = _grammar({("S", "a", "S"), ("S", "b", None)})
    assert grammar.derivation_tree("aab").sequence() == "S => aS => aaS => aab"
    nfa = ExtendedNFA.from_grammar_string("S -> aS | b")
    assert nfa.accepts_input("aab") is True
    assert nfa.derivation_tree("aab").word() == "aab"


def test_partial_dfa_and_rejected_word() -> None:
    dfa = ExtendedDFA(
        states={"s", "f"}, input_symbols={"a", "b"},
        transitions={"s": {"a": "f"}, "f": {}},
        initial_state="s", final_states={"f"}, allow_partial=True,
    )
    before = deepcopy(dfa.input_parameters)
    assert dfa.derivation_tree("a").sequence() == "s => af => a"
    with pytest.raises(RejectionException):
        dfa.derivation_tree("b")
    assert dfa.input_parameters == before


def test_initial_final_dfa_epsilon_derivation() -> None:
    dfa = ExtendedDFA(
        states={"s"}, input_symbols={"a"}, transitions={"s": {}},
        initial_state="s", final_states={"s"}, allow_partial=True,
    )
    assert dfa.accepts_input("") is True
    assert dfa.derivation_tree("").sequence() == "s => "
    with pytest.raises(RejectionException):
        dfa.derivation_tree("a")


def test_nfa_nondeterminism_and_epsilon_derivation() -> None:
    nfa = ExtendedNFA(
        states={"s", "p", "q", "f"}, input_symbols={"a", "b"},
        transitions={
            "s": {"": {"p"}, "a": {"q"}},
            "p": {"a": {"f"}}, "q": {"b": {"f"}}, "f": {},
        }, initial_state="s", final_states={"f"},
    )
    before = deepcopy(nfa.input_parameters)
    assert nfa.derivation_tree("a").sequence() == "s => p => af => a"
    assert nfa.derivation_tree("ab").word() == "ab"
    with pytest.raises(RejectionException):
        nfa.derivation_tree("b")
    assert nfa.input_parameters == before


def test_source_grammar_and_derivation_step_immutable() -> None:
    grammar = _grammar({("S", "a", None)})
    before = deepcopy(grammar)
    step = grammar.derivation_tree("a")
    assert grammar == before
    assert isinstance(step._forms, tuple)
    with pytest.raises(FrozenInstanceError):
        setattr(step, "_terminal_word", "changed")
    assert step.word() == "a"


def test_dfa_nfa_mro_and_gnfa_exclusion() -> None:
    assert GrammarMixin in ExtendedDFA.__mro__
    assert GrammarMixin in ExtendedNFA.__mro__
    assert GrammarMixin not in ExtendedGNFA.__mro__
    assert not hasattr(ExtendedGNFA, "derivation_tree")
