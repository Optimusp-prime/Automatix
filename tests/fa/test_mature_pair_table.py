"""Marking rounds and ASCII views of DFA distinguishability."""

from copy import deepcopy

import pytest

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from tests.fa.test_state_elimination import _mature_dfa


def test_mature_pair_rounds_match_distinguishable_states() -> None:
    d = _mature_dfa()
    table = d.pair_table()
    assert dict(table) == {
        frozenset({"0", "1"}): 0,
        frozenset({"0", "2"}): 0,
        frozenset({"1", "2"}): 1,
    }
    assert d.distinguishable_states() == set(table)
    with pytest.raises(TypeError):
        table[frozenset({"0", "1"})] = 9  # type: ignore[index]


def test_exact_prompt_ascii_rounds_and_plain_marks(
    capsys: pytest.CaptureFixture[str],
) -> None:
    d = _mature_dfa()
    before = deepcopy(d.input_parameters)
    expected = " 0 1\n1 0\n2 0 1"
    assert d.pair_table_str(show_round=True) == expected
    assert d.pair_table_str(show_round=False) == " 0 1\n1 X\n2 X X"
    d.print_pair_table(show_round=True)
    assert capsys.readouterr().out == expected + "\n"
    d.print_pair_table(show_round=False)
    assert capsys.readouterr().out == d.pair_table_str(False) + "\n"
    assert d.input_parameters == before


def test_marking_propagates_beyond_first_round() -> None:
    d = ExtendedDFA(
        states={0, 1, 2, 3}, input_symbols={"a"},
        transitions={0: {"a": 1}, 1: {"a": 2},
                     2: {"a": 3}, 3: {"a": 3}},
        initial_state=0, final_states={3},
    )
    table = d.pair_table()
    assert table[frozenset({0, 3})] == 0
    assert table[frozenset({0, 2})] == 1
    assert table[frozenset({0, 1})] == 2


def test_equivalent_pairs_and_partial_dfa_do_not_export_sink() -> None:
    d = ExtendedDFA(
        states={"start", "left", "right"}, input_symbols={"a", "b"},
        transitions={"start": {"a": "left", "b": "right"},
                     "left": {}, "right": {}},
        initial_state="start", final_states={"start"}, allow_partial=True,
    )
    before = deepcopy(d.input_parameters)
    table = d.pair_table()
    assert table[frozenset({"left", "right"})] is None
    assert table[frozenset({"start", "left"})] == 0
    assert all(pair <= d.states for pair in table)
    assert d.distinguishable_states() == {
        frozenset({"start", "left"}),
        frozenset({"start", "right"}),
    }
    assert "." in d.pair_table_str(show_round=True)
    assert "." in d.pair_table_str(show_round=False)
    assert d.input_parameters == before


def test_heterogeneous_state_labels_are_safe() -> None:
    states = {None, 1, ("final",)}
    d = ExtendedDFA(
        states=states, input_symbols={"a"},
        transitions={None: {"a": 1}, 1: {"a": ("final",)},
                     ("final",): {"a": ("final",)}},
        initial_state=None, final_states={("final",)},
    )
    first = d.pair_table()
    second = d.pair_table()
    assert list(first.items()) == list(second.items())
    assert len(first) == 3
    assert d.pair_table_str() == d.pair_table_str()


def test_singleton_has_no_pairs_or_table(capsys: pytest.CaptureFixture[str]) -> None:
    d = ExtendedDFA(
        states={"q"}, input_symbols={"a"},
        transitions={"q": {"a": "q"}}, initial_state="q",
        final_states={"q"},
    )
    assert dict(d.pair_table()) == {}
    assert d.pair_table_str() == ""
    d.print_pair_table()
    assert capsys.readouterr().out == "\n"


def test_dfa_only_scope() -> None:
    for cls in (ExtendedNFA, ExtendedGNFA):
        assert not hasattr(cls, "pair_table")
        assert not hasattr(cls, "pair_table_str")
        assert not hasattr(cls, "print_pair_table")
