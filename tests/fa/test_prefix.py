"""DFA prefix-closed language tests using useful states."""

from copy import deepcopy

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
    assert not hasattr(d, "prefix_closed_sublanguage")
