"""Distinct Myhill–Nerode language quotients of extended DFA."""

from copy import deepcopy

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from tests.fa.test_state_elimination import _mature_dfa


def _languages(dfa: ExtendedDFA, words: tuple[str, ...]) -> tuple[tuple[bool, ...], ...]:
    return tuple(tuple(quotient.accepts(word) for word in words)
                 for quotient in dfa.myhill_nerode_quotients())


def _assert_distinct(quotients: tuple[ExtendedDFA, ...]) -> None:
    for index, left in enumerate(quotients):
        for right in quotients[index + 1:]:
            assert not left.is_equivalent(right)


def test_mature_three_state_dfa_and_state_partition_regression() -> None:
    dfa = _mature_dfa()
    assert set(dfa.equivalence_classes()) == {
        frozenset({"0"}), frozenset({"1"}), frozenset({"2"}),
    }
    quotients = dfa.myhill_nerode_quotients()
    assert len(quotients) == 3
    assert isinstance(quotients, tuple)
    assert all(type(quotient) is ExtendedDFA for quotient in quotients)
    assert [quotient.initial_state for quotient in quotients] == ["0", "1", "2"]
    assert quotients[0] is not dfa
    assert quotients[0].is_equivalent(dfa)
    _assert_distinct(quotients)


def test_reachable_equivalent_states_collapse_and_unreachable_class_excluded() -> None:
    dfa = ExtendedDFA(
        states={"start", "one", "two", "unreachable"},
        input_symbols={"a", "b"},
        transitions={
            "start": {"a": "one", "b": "two"},
            "one": {"a": "one", "b": "one"},
            "two": {"a": "two", "b": "two"},
            "unreachable": {"a": "unreachable", "b": "unreachable"},
        },
        initial_state="start", final_states={"one", "two"},
    )
    assert len(dfa.equivalence_classes()) == 3
    quotients = dfa.myhill_nerode_quotients()
    assert len(quotients) == 2
    assert [q.initial_state for q in quotients] == ["start", "one"]
    assert dfa.left_quotient_word("b").is_equivalent(quotients[1])
    _assert_distinct(quotients)


def test_partial_single_a_language_has_three_quotients() -> None:
    dfa = ExtendedDFA(
        states={"start", "final"}, input_symbols={"a", "b"},
        transitions={"start": {"a": "final"}, "final": {}},
        initial_state="start", final_states={"final"}, allow_partial=True,
    )
    quotients = dfa.myhill_nerode_quotients()
    assert len(quotients) == 3
    words = ("", "a", "b", "aa")
    assert _languages(dfa, words) == (
        (False, True, False, False),
        (True, False, False, False),
        (False, False, False, False),
    )
    assert quotients[2].is_empty()
    _assert_distinct(quotients)
    for witness in ("", "a", "b", "aa", "ab", "ba", "bbb"):
        matches = sum(q.is_equivalent(dfa.left_quotient_word(witness))
                      for q in quotients)
        assert matches == 1


def test_explicit_reachable_dead_state_deduplicates_missing_edges() -> None:
    dfa = ExtendedDFA(
        states={"start", "final", "dead"}, input_symbols={"a", "b"},
        transitions={
            "start": {"a": "final", "b": "dead"},
            "final": {}, "dead": {},
        },
        initial_state="start", final_states={"final"}, allow_partial=True,
    )
    quotients = dfa.myhill_nerode_quotients()
    assert len(quotients) == 3
    assert [q.initial_state for q in quotients] == ["start", "final", "dead"]
    assert sum(q.is_empty() for q in quotients) == 1
    _assert_distinct(quotients)


def test_complete_explicit_dead_state_and_one_state_extremes() -> None:
    dfa = ExtendedDFA(
        states={"s", "f", "dead"}, input_symbols={"a", "b"},
        transitions={
            "s": {"a": "f", "b": "dead"},
            "f": {"a": "dead", "b": "dead"},
            "dead": {"a": "dead", "b": "dead"},
        },
        initial_state="s", final_states={"f"},
    )
    assert len(dfa.myhill_nerode_quotients()) == 3
    for final in (False, True):
        one = ExtendedDFA(
            states={"q"}, input_symbols={"a"},
            transitions={"q": {"a": "q"}}, initial_state="q",
            final_states={"q"} if final else set(),
        )
        quotients = one.myhill_nerode_quotients()
        assert len(quotients) == 1
        assert quotients[0].is_equivalent(one)


def test_one_state_partial_empty_and_epsilon_accepting() -> None:
    for final, expected in ((False, 1), (True, 2)):
        dfa = ExtendedDFA(
            states={"q"}, input_symbols={"a", "b"},
            transitions={"q": {}}, initial_state="q",
            final_states={"q"} if final else set(), allow_partial=True,
        )
        quotients = dfa.myhill_nerode_quotients()
        assert len(quotients) == expected
        assert quotients[0].accepts("") is final
        _assert_distinct(quotients)


def test_deterministic_order_cycles_immutability_and_types() -> None:
    dfa = ExtendedDFA(
        states={0, "branch", (2, "final"), None},
        input_symbols={"b", "a"},
        transitions={
            0: {"a": "branch", "b": (2, "final")},
            "branch": {"a": (2, "final"), "b": (2, "final")},
            (2, "final"): {"a": 0, "b": (2, "final")},
            None: {"a": None, "b": None},
        },
        initial_state=0, final_states={(2, "final")},
    )
    before = deepcopy(dfa.input_parameters), dfa.allow_partial
    first = dfa.myhill_nerode_quotients()
    second = dfa.myhill_nerode_quotients()
    assert [q.initial_state for q in first] == [q.initial_state for q in second]
    assert [q.initial_state for q in first] == [0, "branch", (2, "final")]
    assert all(type(q) is ExtendedDFA for q in first)
    assert (dfa.input_parameters, dfa.allow_partial) == before
    assert first[0] is not dfa
    assert type(first[0].complete()) is ExtendedDFA
    assert not hasattr(ExtendedNFA, "myhill_nerode_quotients")
    assert not hasattr(ExtendedGNFA, "myhill_nerode_quotients")


def test_none_as_valid_isolated_initial_state() -> None:
    dfa = ExtendedDFA(
        states={None}, input_symbols={"a"}, transitions={None: {}},
        initial_state=None, final_states=set(), allow_partial=True,
    )
    quotients = dfa.myhill_nerode_quotients()
    assert len(quotients) == 1
    assert quotients[0].initial_state is None
    assert quotients[0].is_empty()
