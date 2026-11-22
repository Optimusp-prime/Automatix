"""Greedy state elimination: language contract, shape of results, scale."""

import random
from copy import deepcopy
from itertools import product

import pytest
from automata.fa.nfa import NFA

from automata_extensions.fa import ExtendedDFA, ExtendedNFA
from automata_extensions.fa.fa_mixins.regex_heuristic import HeuristicRegexMixin
from automata_extensions.regex import Regex
from tests.fa.test_state_elimination import _mature_dfa


def _assert_same_language(
    automaton: ExtendedDFA | ExtendedNFA, expression: str | None, max_length: int = 6
) -> None:
    """Compare words with an independent upstream oracle and our parser."""
    if expression is None:
        assert automaton.is_empty() is True
        return
    # The result must stay in the #49 syntax used by the web editor.
    Regex(expression, input_symbols=automaton.input_symbols)
    oracle = NFA.from_regex(expression or "()", input_symbols=automaton.input_symbols)
    for length in range(max_length + 1):
        for symbols in product(sorted(automaton.input_symbols), repeat=length):
            word = "".join(symbols)
            assert oracle.accepts_input(word) is automaton.accepts_input(word), word


def _dense_dfa(size: int, symbols: str, seed: int) -> ExtendedDFA:
    """Strongly connected complete DFA: a cycle on symbols[0], random rest."""
    rng = random.Random(seed)
    states = [f"q{i}" for i in range(size)]
    transitions = {state: {s: rng.choice(states) for s in symbols} for state in states}
    for index, state in enumerate(states):
        transitions[state][symbols[0]] = states[(index + 1) % size]
    finals = {state for state in states if rng.random() < 0.4} or {states[-1]}
    return ExtendedDFA(states=set(states), input_symbols=set(symbols),
                       transitions=transitions, initial_state="q0", final_states=finals)


def _multiples_dfa(modulus: int) -> ExtendedDFA:
    """Binary words denoting multiples of modulus (most significant first)."""
    return ExtendedDFA(
        states=set(range(modulus)), input_symbols={"0", "1"},
        transitions={r: {"0": 2 * r % modulus, "1": (2 * r + 1) % modulus}
                     for r in range(modulus)},
        initial_state=0, final_states={0},
    )


def test_mixin_is_available_on_dfa_and_nfa() -> None:
    assert issubclass(ExtendedDFA, HeuristicRegexMixin)
    assert issubclass(ExtendedNFA, HeuristicRegexMixin)


def test_mature_fixture_gives_compact_equivalent_expression() -> None:
    dfa = _mature_dfa()
    expression = dfa.to_regex_heuristic()
    assert expression == "(b|ab*ab*a)*"
    _assert_same_language(dfa, expression)
    assert len(expression) < len(dfa.to_regex() or "")


@pytest.mark.parametrize(
    ("transitions", "finals", "partial", "expected"),
    [
        ({"q": {}}, {"q"}, True, ""),
        ({"q": {"a": "q"}}, {"q"}, False, "a*"),
        ({"q": {"a": "q"}}, set(), False, None),
    ],
)
def test_one_state_automata(
    transitions: dict[str, dict[str, str]], finals: set[str],
    partial: bool, expected: str | None,
) -> None:
    dfa = ExtendedDFA(states={"q"}, input_symbols={"a"}, transitions=transitions,
                      initial_state="q", final_states=finals, allow_partial=partial)
    assert dfa.to_regex_heuristic() == expected
    _assert_same_language(dfa, expected)


def test_empty_language_when_finals_are_inaccessible() -> None:
    dfa = ExtendedDFA(
        states={"q0", "q1", "lost"}, input_symbols={"a"},
        transitions={"q0": {"a": "q1"}, "q1": {"a": "q0"}, "lost": {"a": "lost"}},
        initial_state="q0", final_states={"lost"},
    )
    assert dfa.to_regex_heuristic() is None


def test_epsilon_union_plus_becomes_star() -> None:
    """ε | a a* is rendered a*."""
    dfa = ExtendedDFA(
        states={"q0", "q1"}, input_symbols={"a"},
        transitions={"q0": {"a": "q1"}, "q1": {"a": "q1"}},
        initial_state="q0", final_states={"q0", "q1"},
    )
    assert dfa.to_regex_heuristic() == "a*"
    _assert_same_language(dfa, "a*")


def test_epsilon_is_absorbed_by_a_nullable_operand() -> None:
    """ε | b* | a: the final state is reached by ε then b*, or by a."""
    nfa = ExtendedNFA(
        states={"i", "f"}, input_symbols={"a", "b"},
        transitions={"i": {"": {"f"}}, "f": {"b": {"f"}}},
        initial_state="i", final_states={"i", "f"},
    )
    assert nfa.to_regex_heuristic() == "b*"


def test_inaccessible_and_sink_states_do_not_change_result() -> None:
    trim = ExtendedDFA(
        states={"p", "q"}, input_symbols={"a", "b"},
        transitions={"p": {"a": "q"}, "q": {"b": "p"}},
        initial_state="p", final_states={"q"}, allow_partial=True,
    )
    noisy = ExtendedDFA(
        states={"p", "q", "sink", "island"}, input_symbols={"a", "b"},
        transitions={"p": {"a": "q", "b": "sink"}, "q": {"a": "sink", "b": "p"},
                     "sink": {"a": "sink", "b": "sink"}, "island": {"a": "q", "b": "p"}},
        initial_state="p", final_states={"q"},
    )
    assert noisy.to_regex_heuristic() == trim.to_regex_heuristic()
    _assert_same_language(noisy, noisy.to_regex_heuristic())


def test_multiple_finals_and_parallel_symbols() -> None:
    dfa = ExtendedDFA(
        states={"s", "t", "u"}, input_symbols={"a", "b", "c"},
        transitions={"s": {"a": "t", "b": "t", "c": "u"}, "t": {"c": "u"}, "u": {"a": "s"}},
        initial_state="s", final_states={"t", "u"}, allow_partial=True,
    )
    _assert_same_language(dfa, dfa.to_regex_heuristic())


def test_heterogeneous_and_compound_state_labels() -> None:
    dfa = ExtendedDFA(
        states={0, "1", frozenset({2})}, input_symbols={"a", "b"},
        transitions={0: {"a": "1", "b": 0}, "1": {"a": frozenset({2}), "b": 0},
                     frozenset({2}): {"a": frozenset({2}), "b": "1"}},
        initial_state=0, final_states={frozenset({2})},
    )
    _assert_same_language(dfa, dfa.to_regex_heuristic())


@pytest.mark.parametrize("seed", range(40))
def test_random_partial_dfas_preserve_language(seed: int) -> None:
    rng = random.Random(seed)
    size = rng.randint(1, 6)
    states = list(range(size))
    transitions = {
        state: {s: rng.choice(states) for s in "ab" if rng.random() < 0.8}
        for state in states
    }
    dfa = ExtendedDFA(states=set(states), input_symbols={"a", "b"}, transitions=transitions,
                      initial_state=0, final_states={s for s in states if rng.random() < 0.4},
                      allow_partial=True)
    _assert_same_language(dfa, dfa.to_regex_heuristic())


def test_nfa_with_epsilon_and_nondeterminism() -> None:
    nfa = ExtendedNFA(
        states={"i", "x", "y", "f"}, input_symbols={"a", "b"},
        transitions={"i": {"": {"x", "y"}}, "x": {"a": {"x", "f"}},
                     "y": {"b": {"y"}, "": {"f"}}, "f": {}},
        initial_state="i", final_states={"f"},
    )
    expression = nfa.to_regex_heuristic()
    _assert_same_language(nfa, expression)
    assert Regex(expression or "()", input_symbols={"a", "b"}).to_dfa().is_equivalent(
        nfa.determinize())


def test_nfa_epsilon_only_language() -> None:
    nfa = ExtendedNFA(states={"i", "f"}, input_symbols={"a"},
                      transitions={"i": {"": {"f"}}, "f": {}},
                      initial_state="i", final_states={"f"})
    assert nfa.to_regex_heuristic() == ""


def test_source_is_not_modified_and_result_is_deterministic() -> None:
    dfa = _dense_dfa(8, "ab", seed=3)
    snapshot = deepcopy(dfa)
    first = dfa.to_regex_heuristic()
    assert dfa.to_regex_heuristic() == first
    assert dfa == snapshot
    assert dfa.transitions == snapshot.transitions
    assert type(first) is str


def test_composes_with_minimize() -> None:
    dfa = _dense_dfa(10, "ab", seed=7)
    expression = dfa.minimize().to_regex_heuristic()
    assert Regex(expression or "()", input_symbols={"a", "b"}).to_dfa().is_equivalent(dfa)


@pytest.mark.parametrize("modulus", [3, 5, 7])
def test_binary_multiples_are_recognized(modulus: int) -> None:
    dfa = _multiples_dfa(modulus)
    _assert_same_language(dfa, dfa.to_regex_heuristic(), max_length=9)


def test_regression_eighteen_dense_states_stay_tractable() -> None:
    """Regression: the lexical #53 result exceeds 14 million characters here."""
    dfa = _dense_dfa(18, "abc", seed=183)
    expression = dfa.to_regex_heuristic()
    assert expression is not None
    assert len(expression) < 50_000
    Regex(expression, input_symbols={"a", "b", "c"})
    _assert_same_language(dfa, expression, max_length=4)


def test_larger_structured_automaton_gives_small_expression() -> None:
    dfa = _multiples_dfa(40)
    expression = dfa.minimize().to_regex_heuristic()
    assert expression is not None and len(expression) < 1_000
    assert Regex(expression, input_symbols={"0", "1"}).to_dfa().is_equivalent(dfa)
