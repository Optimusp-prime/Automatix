"""Exercise 38: paths, multiplicities and epsilon-free domain boundaries."""

from copy import deepcopy
from itertools import islice, product
from unittest.mock import patch

import pytest
from automata.fa.nfa import NFA

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.nfa_mixins.accepting_runs import AcceptingRunsMixin


def _occurrence_nfa() -> ExtendedNFA:
    # Choosing the one transition 0 --a--> 1 marks one occurrence of a.
    return ExtendedNFA(
        states={0, 1}, input_symbols={"a", "b"},
        transitions={0: {"a": {0, 1}, "b": {0}}, 1: {"a": {1}, "b": {1}}},
        initial_state=0, final_states={1},
    )


def _binary_nfa() -> ExtendedNFA:
    return ExtendedNFA(
        states={0, 1}, input_symbols={"a"},
        transitions={0: {"a": {0, 1}}, 1: {"a": {0, 1}}},
        initial_state=0, final_states={0, 1},
    )


def test_exercise_38_abaa_lists_exactly_three_accepting_runs() -> None:
    nfa = _occurrence_nfa()
    assert set(nfa.accepting_runs("abaa")) == {
        (0, 1, 1, 1, 1), (0, 0, 0, 1, 1), (0, 0, 0, 0, 1),
    }
    assert nfa.count_accepting_runs("abaa") == 3


@pytest.mark.parametrize("length", range(6))
def test_occurrence_identity_and_product_square(length: int) -> None:
    nfa = _occurrence_nfa()
    squared = nfa.intersection(nfa)
    for letters in product("ab", repeat=length):
        word = "".join(letters)
        expected = word.count("a")
        assert nfa.count_accepting_runs(word) == expected
        assert len(list(nfa.accepting_runs(word))) == expected
        assert squared.count_accepting_runs(word) == expected**2
        assert len(list(squared.accepting_runs(word))) == expected**2


def test_merged_histories_remain_distinct_and_rejection_is_not_counted() -> None:
    nfa = ExtendedNFA(
        states={"s", "l", "r", "f", "dead", "unreachable"},
        input_symbols={"a", "b"},
        transitions={
            "s": {"a": {"l", "r", "dead"}},
            "l": {"b": {"f"}}, "r": {"b": {"f"}},
            "f": {}, "dead": {"b": {"dead"}},
            "unreachable": {"a": {"unreachable"}},
        }, initial_state="s", final_states={"f", "unreachable"},
    )
    assert set(nfa.accepting_runs("ab")) == {("s", "l", "f"), ("s", "r", "f")}
    assert nfa.count_accepting_runs("ab") == 2
    assert len(nfa.execution_trace("ab")[-1] & nfa.final_states) == 1


@pytest.mark.parametrize("final", [False, True])
@pytest.mark.parametrize("initial", [None, "s", 7])
def test_empty_word_and_singleton_with_empty_alphabet(initial: object, final: bool) -> None:
    nfa = ExtendedNFA(
        states={initial}, input_symbols=set(), transitions={initial: {}},
        initial_state=initial, final_states={initial} if final else set(),
    )
    assert list(nfa.accepting_runs("")) == ([(initial,)] if final else [])
    assert nfa.count_accepting_runs("") == int(final)
    assert list(nfa.accepting_runs("a")) == []
    assert nfa.count_accepting_runs("a") == 0


@pytest.mark.parametrize("word", ["", "a", "aa", "b", "ab", "aaa", "z"])
def test_against_independent_exhaustive_state_sequence_definition(word: str) -> None:
    nfa = ExtendedNFA(
        states={None, "branch", 3}, input_symbols={"a", "b"},
        transitions={
            None: {"a": {None, "branch"}, "b": {3}},
            "branch": {"a": {3}, "b": {None, 3}}, 3: {"a": {3}},
        }, initial_state=None, final_states={None, 3},
    )
    expected: set[tuple[object, ...]] = set()
    for tail in product(nfa.states, repeat=len(word)):
        run = (nfa.initial_state,) + tail
        if run[-1] in nfa.final_states and all(
            run[i + 1] in nfa.transitions.get(run[i], {}).get(symbol, ())
            for i, symbol in enumerate(word)
        ):
            expected.add(run)
    actual = list(nfa.accepting_runs(word))
    assert len(actual) == len(set(actual))
    assert set(actual) == expected
    assert nfa.count_accepting_runs(word) == len(expected)
    # Upstream NFA simulation uses NetworkX, which rejects a None state.
    # Determinization wraps states in frozensets and preserves the language.
    assert bool(expected) is nfa.determinize().accepts(word)


def test_exact_large_integer_count_never_enumerates_paths() -> None:
    nfa = _binary_nfa()
    with patch.object(AcceptingRunsMixin, "accepting_runs", side_effect=AssertionError):
        assert nfa.count_accepting_runs("a" * 2000) == 2**2000


def test_lazy_iterative_enumeration_handles_long_words_without_recursion() -> None:
    nfa = _binary_nfa()
    iterator = nfa.accepting_runs("a" * 2000)
    assert iter(iterator) is iterator
    first = list(islice(iterator, 2))
    assert len(first) == 2
    assert first[0] != first[1]
    assert all(type(run) is tuple and len(run) == 2001 for run in first)
    assert all(run[0] == 0 and run[-1] in nfa.final_states for run in first)


def test_iterators_are_independent_and_yield_immutable_snapshots() -> None:
    nfa = _occurrence_nfa()
    first = nfa.accepting_runs("aaa")
    saved = next(first)
    snapshot = tuple(saved)
    assert len(list(nfa.accepting_runs("a"))) == 1
    remaining = list(first)
    assert saved == snapshot
    assert len(remaining) == 2
    assert saved not in remaining


@pytest.mark.parametrize("word", ["a", "ab", "b", "aaaa", "az"])
def test_dead_ends_missing_rows_and_empty_destination_sets(word: str) -> None:
    nfa = ExtendedNFA(
        states={"s", "f"}, input_symbols={"a", "b"},
        transitions={"s": {"a": {"f"}, "b": set()}},
        initial_state="s", final_states={"f"},
    )
    expected = [("s", "f")] if word == "a" else []
    assert list(nfa.accepting_runs(word)) == expected
    assert nfa.count_accepting_runs(word) == len(expected)


@pytest.mark.parametrize("method", ["accepting_runs", "count_accepting_runs"])
@pytest.mark.parametrize("epsilon_kind", ["chain", "cycle", "unreachable"])
def test_actual_epsilon_edges_are_rejected_eagerly(method: str, epsilon_kind: str) -> None:
    transitions: dict[object, dict[str, set[object]]] = {
        "s": {"a": {"f"}}, "f": {}, "u": {},
    }
    if epsilon_kind == "chain":
        transitions["s"][""] = {"f"}
    elif epsilon_kind == "cycle":
        transitions["s"][""] = {"s"}
    else:
        transitions["u"][""] = {"u"}
    nfa = ExtendedNFA(
        states=set(transitions), input_symbols={"a"}, transitions=transitions,
        initial_state="s", final_states={"f"},
    )
    # Calling accepting_runs itself must raise, without next() or list().
    with pytest.raises(ValueError, match="epsilon-free"):
        getattr(nfa, method)("a")


def test_empty_epsilon_destination_set_is_not_a_real_edge() -> None:
    nfa = ExtendedNFA(
        states={"s"}, input_symbols={"a"},
        transitions={"s": {"": set(), "a": {"s"}}},
        initial_state="s", final_states={"s"},
    )
    assert list(nfa.accepting_runs("aa")) == [("s", "s", "s")]
    assert nfa.count_accepting_runs("aa") == 1


@pytest.mark.parametrize("word", [None, 4, ["a"], b"a"])
@pytest.mark.parametrize("method", ["accepting_runs", "count_accepting_runs"])
def test_word_type_is_validated_before_iteration(method: str, word: object) -> None:
    with pytest.raises(TypeError, match="word must be a string"):
        getattr(_occurrence_nfa(), method)(word)


def test_empty_final_set_has_no_runs() -> None:
    nfa = ExtendedNFA(
        states={0}, input_symbols={"a"}, transitions={0: {"a": {0}}},
        initial_state=0, final_states=set(),
    )
    assert list(nfa.accepting_runs("a" * 2000)) == []
    assert nfa.count_accepting_runs("") == 0


def test_queries_preserve_source_caches_and_compose_with_subautomata() -> None:
    source = _occurrence_nfa()
    before = deepcopy(source.input_parameters), dict(vars(source))
    assert len(list(source.accepting_runs("aaa"))) == 3
    assert source.count_accepting_runs("aaa") == 3
    assert (source.input_parameters, vars(source)) == before
    restricted = source.induced_subautomaton({0, 1})
    assert restricted.count_accepting_runs("aaa") == 3
    assert source.determinize().accepts("aaa") is True


def test_public_mro_and_no_upstream_monkey_patch() -> None:
    assert ExtendedNFA.accepting_runs is AcceptingRunsMixin.accepting_runs
    assert ExtendedNFA.count_accepting_runs is AcceptingRunsMixin.count_accepting_runs
    assert ExtendedNFA.__mro__.index(AcceptingRunsMixin) < ExtendedNFA.__mro__.index(NFA)
    for cls in (NFA, ExtendedDFA, ExtendedGNFA):
        assert not hasattr(cls, "accepting_runs")
        assert not hasattr(cls, "count_accepting_runs")
