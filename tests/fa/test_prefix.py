"""DFA prefix-closed language tests using useful states."""

from copy import deepcopy
from itertools import product
from typing import Mapping, cast

from automata.fa.fa import FAStateT

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.dfa_mixins.prefix import PrefixMixin


def test_source_compatibility_non_prefix_closed_three_state_cycle() -> None:
    """Preserve the mature d.is_prefix_closed() is False observation."""
    d = ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a"},
        transitions={"0": {"a": "1"}, "1": {"a": "2"}, "2": {"a": "0"}},
        initial_state="0", final_states={"2"},
    )
    assert d.is_prefix_closed() is False
    assert d.accepts("aa") is True
    assert d.accepts("a") is False


def test_accessible_nonuseful_sink_does_not_break_prefix_closure() -> None:
    d = ExtendedDFA(
        states={"initial", "final", "sink"}, input_symbols={"a", "b"},
        transitions={
            "initial": {"a": "final", "b": "sink"},
            "final": {"a": "sink", "b": "sink"},
            "sink": {"a": "sink", "b": "sink"},
        },
        initial_state="initial", final_states={"initial", "final"},
    )
    assert d.accessible_states() == d.states
    assert d.useful_states() == frozenset({"initial", "final"})
    assert d.is_prefix_closed() is True


def test_empty_language_is_prefix_closed() -> None:
    d = ExtendedDFA(
        states={"start", "trap"}, input_symbols={"a"},
        transitions={"start": {"a": "trap"}, "trap": {"a": "trap"}},
        initial_state="start", final_states=set(),
    )
    assert d.is_empty() is True
    assert d.useful_states() == frozenset()
    assert d.is_prefix_closed() is True
    assert d.trim().is_prefix_closed() is True


def test_nonempty_language_without_epsilon_is_not_prefix_closed() -> None:
    d = ExtendedDFA(
        states={"start", "final"}, input_symbols={"a"},
        transitions={"start": {"a": "final"}, "final": {"a": "final"}},
        initial_state="start", final_states={"final"},
    )
    assert d.accepts("") is False
    assert d.accepts("a") is True
    assert d.useful_states() == d.states
    assert d.is_prefix_closed() is False


def test_epsilon_only_language_and_unreachable_nonfinal_state() -> None:
    d = ExtendedDFA(
        states={"initial", "dead", "unreachable"}, input_symbols={"a"},
        transitions={
            "initial": {"a": "dead"},
            "dead": {"a": "dead"},
            "unreachable": {"a": "unreachable"},
        },
        initial_state="initial", final_states={"initial"},
    )
    assert d.useful_states() == frozenset({"initial"})
    assert d.accepts("") is True
    assert d.accepts("a") is False
    assert d.is_prefix_closed() is True


def test_partial_dfa_with_useful_cycle_is_prefix_closed() -> None:
    d = ExtendedDFA(
        states={None, 1, "unused"}, input_symbols={"a", "b"},
        transitions={
            None: {"a": 1}, 1: {"a": 1}, "unused": {},
        },
        initial_state=None, final_states={None, 1}, allow_partial=True,
    )
    assert d.useful_states() == frozenset({None, 1})
    assert d.is_prefix_closed() is True
    assert type(d.is_prefix_closed()) is bool


def test_query_is_immutable_and_dfa_specific() -> None:
    d = ExtendedDFA(
        states={0, 1}, input_symbols={"a"},
        transitions={0: {"a": 1}, 1: {"a": 1}},
        initial_state=0, final_states={1},
    )
    before = deepcopy(d.input_parameters)
    assert d.is_prefix_closed() is False
    assert d.input_parameters == before
    assert ExtendedDFA.is_prefix_closed is PrefixMixin.is_prefix_closed
    assert PrefixMixin in ExtendedDFA.__mro__
    assert PrefixMixin not in ExtendedNFA.__mro__
    assert PrefixMixin not in ExtendedGNFA.__mro__


def _branching_source() -> ExtendedDFA:
    return ExtendedDFA(
        states={"initial", "middle", "final"}, input_symbols={"a", "b"},
        transitions={
            "initial": {"a": "final", "b": "middle"},
            "middle": {"a": "final", "b": "middle"},
            "final": {"a": "final", "b": "middle"},
        },
        initial_state="initial", final_states={"initial", "final"},
    )


def test_source_compatibility_prefix_sublanguage_accepts_epsilon() -> None:
    """Mature (is_prefix_closed(), sublanguage.accepts_input('')) analogue."""
    d = _branching_source()
    assert (
        d.is_prefix_closed(),
        d.prefix_closed_sublanguage().accepts_input(""),
    ) == (False, True)


def test_filter_preserves_exactly_final_to_final_transitions() -> None:
    source = _branching_source()
    before = deepcopy(source.input_parameters)
    result = source.prefix_closed_sublanguage()
    assert isinstance(result, ExtendedDFA)
    assert result is not source
    assert result.states == source.states
    assert result.input_symbols == source.input_symbols
    assert result.initial_state == source.initial_state
    assert result.final_states == source.final_states
    assert result.transitions == {
        "initial": {"a": "final"},
        "middle": {},
        "final": {"a": "final"},
    }
    assert result.allow_partial is True
    assert source.input_parameters == before
    assert result.is_prefix_closed() is True
    assert result.is_included_in(source) is True


def test_greatest_property_keeps_good_branch_and_removes_bad_prefixes() -> None:
    source = _branching_source()
    result = source.prefix_closed_sublanguage()
    for word in ("", "a", "aa", "aaa"):
        assert source.accepts(word) is True
        assert result.accepts(word) is True
    for word in ("b", "ba", "ab", "aba", "bba"):
        assert result.accepts(word) is False
    assert source.accepts("ba") is True
    assert source.accepts("aba") is True


def test_result_contains_exactly_words_with_all_prefixes_in_source() -> None:
    source = _branching_source()
    result = source.prefix_closed_sublanguage()
    for length in range(5):
        for symbols in product("ab", repeat=length):
            word = "".join(symbols)
            every_prefix_accepted = all(
                source.accepts(word[:end]) for end in range(length + 1)
            )
            assert result.accepts(word) is every_prefix_accepted


def test_nonfinal_initial_produces_empty_prefix_closed_language() -> None:
    source = ExtendedDFA(
        states={"start", "accept"}, input_symbols={"a"},
        transitions={
            "start": {"a": "accept"}, "accept": {"a": "accept"},
        },
        initial_state="start", final_states={"accept"},
    )
    result = source.prefix_closed_sublanguage()
    assert result.states == source.states
    assert result.final_states == source.final_states
    assert result.transitions == {"start": {}, "accept": {"a": "accept"}}
    assert source.accepts("a") is True
    assert result.is_empty() is True
    assert result.is_prefix_closed() is True
    assert result.is_included_in(source) is True


def test_empty_and_already_prefix_closed_sources_return_fresh_dfas() -> None:
    empty = ExtendedDFA(
        states={"q"}, input_symbols={"a"},
        transitions={"q": {"a": "q"}}, initial_state="q",
        final_states=set(),
    )
    empty_result = empty.prefix_closed_sublanguage()
    assert empty_result is not empty
    assert empty_result.is_empty() is True
    assert empty_result.is_prefix_closed() is True

    closed = ExtendedDFA(
        states={"q", "dead"}, input_symbols={"a", "b"},
        transitions={
            "q": {"a": "q", "b": "dead"},
            "dead": {"a": "dead", "b": "dead"},
        },
        initial_state="q", final_states={"q"},
    )
    result = closed.prefix_closed_sublanguage()
    assert result is not closed
    assert result.is_prefix_closed() is True
    for word in ("", "a", "aa", "b", "ab", "ba"):
        assert result.accepts(word) is closed.accepts(word)


def test_partial_dfa_and_heterogeneous_states_remain_composable() -> None:
    source = ExtendedDFA(
        states={None, 1, ("dead", 2)}, input_symbols={"a", "b"},
        transitions={
            None: {"a": 1, "b": ("dead", 2)},
            1: {"a": 1},
            ("dead", 2): {"a": 1},
        },
        initial_state=None, final_states={None, 1}, allow_partial=True,
    )
    result = source.prefix_closed_sublanguage()
    assert isinstance(result, ExtendedDFA)
    transitions = cast(Mapping[FAStateT, Mapping[str, FAStateT]], result.transitions)
    assert len(transitions) == 3
    assert transitions[None] == {"a": 1}
    assert transitions[1] == {"a": 1}
    assert transitions[("dead", 2)] == {}
    assert result.is_prefix_closed() is True
    assert result.complete().is_complete() is True
