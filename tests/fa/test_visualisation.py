"""DOT, TikZ and Graphviz rendering share a concrete FA graph model."""

from copy import deepcopy
from pathlib import Path
from shutil import which
from unittest.mock import call, patch

import pytest
from graphviz import ExecutableNotFound, Source

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.fa_mixins.visualisation import VisualisationMixin


def _mature_dfa() -> ExtendedDFA:
    return ExtendedDFA(
        states={"0", "1", "2"}, input_symbols={"a", "b"},
        transitions={
            "0": {"b": "0", "a": "1"},
            "1": {"b": "1", "a": "2"},
            "2": {"a": "0", "b": "2"},
        },
        initial_state="0", final_states={"0"},
    )


def test_dot_mature_source_compatibility_exact() -> None:
    d = _mature_dfa()
    assert d.dot().splitlines() == [
        "digraph {",
        "\trankdir=LR",
        "\t__start__ [shape=point style=invis]",
        "\t__start__ -> s0",
        "\ts0 [label=0 shape=doublecircle]",
        "\ts1 [label=1 shape=circle]",
        "\ts2 [label=2 shape=circle]",
        "\ts0 -> s0 [label=b]",
        "\ts0 -> s1 [label=a]",
        "\ts1 -> s1 [label=b]",
        "\ts1 -> s2 [label=a]",
        "\ts2 -> s0 [label=a]",
        "\ts2 -> s2 [label=b]",
        "}",
    ]


def test_dot_safe_ids_quoting_and_partial_automaton() -> None:
    d = ExtendedDFA(
        states={None, 7, ("q", 1), 'q"1\\\n'}, input_symbols={'a"\\'},
        transitions={
            None: {'a"\\': 'q"1\\\n'}, 7: {}, ("q", 1): {}, 'q"1\\\n': {},
        },
        initial_state=None, final_states={("q", 1)}, allow_partial=True,
    )
    dot = d.dot()
    assert dot.startswith("digraph {\n\trankdir=LR\n")
    assert "__start__ -> s0" in dot
    assert "s0 [label=None shape=circle]" in dot
    assert "shape=doublecircle" in dot
    assert 'label="q\\"1\\\\\\n"' in dot
    assert 'label="a\\"\\\\"' in dot
    assert 'label="(q, 1)"' not in dot  # tuple label retains Python quotes.
    assert dot == d.dot()
    assert dot.count(" -> ") == 2  # start pointer and one real edge


def test_dfa_labels_with_special_graphviz_keywords_are_quoted() -> None:
    d = ExtendedDFA(
        states={"graph"}, input_symbols={"a"},
        transitions={"graph": {"a": "graph"}},
        initial_state="graph", final_states=set(),
    )
    assert 's0 [label="graph" shape=circle]' in d.dot()
    assert 's0 -> s0 [label=a]' in d.dot()


def test_nfa_multiple_targets_epsilon_and_tikz() -> None:
    n = ExtendedNFA(
        states={"p", "q", "r"}, input_symbols={"a"},
        transitions={"p": {"": {"q"}, "a": {"q", "r"}},
                     "r": {"a": {"r"}}},
        initial_state="p", final_states={"r"},
    )
    dot = n.dot()
    tikz = n.tikz()
    assert 's0 -> s1 [label="ε"]' in dot
    assert 's0 -> s1 [label=a]' in dot
    assert 's0 -> s2 [label=a]' in dot
    assert 's2 -> s2 [label=a]' in dot
    assert r"\begin{tikzpicture}" in tikz
    assert r"\node[state,initial] (s0)" in tikz
    assert r"\node[state,accepting] (s2)" in tikz
    assert r"$\varepsilon$" in tikz
    assert "edge[loop above]" in tikz


def test_literal_epsilon_symbol_is_not_a_tikz_epsilon_transition() -> None:
    n = ExtendedNFA(
        states={"s", "epsilon_edge", "symbol_edge"}, input_symbols={"ε"},
        transitions={
            "s": {"": {"epsilon_edge"}, "ε": {"symbol_edge"}},
        },
        initial_state="s", final_states={"symbol_edge"},
    )
    tikz = n.tikz()
    assert tikz.count(r"$\varepsilon$") == 1
    assert "node {ε}" in tikz


def test_gnfa_regex_edges_and_none_cells() -> None:
    g = ExtendedGNFA(
        states={"s", "p", "f"}, input_symbols={"a", "b"},
        transitions={"s": {"p": "a*", "f": None},
                     "p": {"p": "b|a", "f": ""}},
        initial_state="s", final_state="f",
    )
    dot = g.dot()
    assert 's0 -> s2 [label="a*"]' in dot
    assert 's2 -> s2 [label="b|a"]' in dot
    assert 's2 -> s1 [label="ε"]' in dot
    assert "s0 -> s1" not in dot
    assert "s1 [label=f shape=doublecircle]" in dot
    assert r"$\varepsilon$" in g.tikz()


def test_none_and_heterogeneous_gnfa_states() -> None:
    g = ExtendedGNFA(
        states={None, 2}, input_symbols={"a"},
        transitions={None: {2: "a"}},
        initial_state=None, final_state=2,
    )
    assert "s0 [label=None shape=circle]" in g.dot()
    assert "s1 [label=2 shape=doublecircle]" in g.dot()
    assert "s0 -> s1 [label=a]" in g.dot()


def test_tikz_escaping_latex_wrapper_and_mature_examples() -> None:
    d = ExtendedDFA(
        states={"q_1%", "f\\#"}, input_symbols={"a"},
        transitions={"q_1%": {"a": "f\\#"}, "f\\#": {"a": "f\\#"}},
        initial_state="q_1%", final_states={"f\\#"},
    )
    tikz = d.tikz()
    latex = d.latex()
    assert len(tikz) > 0
    assert len(latex) > 0
    assert r"q\_1\%" in tikz
    assert r"f\textbackslash{}\#" in tikz
    assert "edge[loop above]" in tikz
    assert r"\documentclass{standalone}" in latex
    assert r"\usetikzlibrary{automata}" in latex
    assert r"\begin{document}" in latex
    assert tikz in latex
    assert len(_mature_dfa().tikz()) > 0  # Supplied mature regression.
    assert len(_mature_dfa().latex()) > 0


@pytest.mark.parametrize("kind", ["dfa", "nfa", "gnfa"])
def test_text_export_no_binary_no_mutation(kind: str) -> None:
    automaton: ExtendedDFA | ExtendedNFA | ExtendedGNFA
    if kind == "dfa":
        automaton = _mature_dfa()
    elif kind == "nfa":
        automaton = ExtendedNFA(
            states={"s", "f"}, input_symbols={"a"},
            transitions={"s": {"a": {"f"}}},
            initial_state="s", final_states={"f"},
        )
    else:
        automaton = ExtendedGNFA(
            states={"s", "f"}, input_symbols={"a"},
            transitions={"s": {"f": "a"}},
            initial_state="s", final_state="f",
        )
    before = deepcopy(automaton.input_parameters), dict(vars(automaton))
    with patch("subprocess.run", side_effect=AssertionError("no renderer")):
        assert type(automaton.dot()) is str
        assert type(automaton.tikz()) is str
        assert type(automaton.latex()) is str
        assert isinstance(automaton.graph(), Source)
    assert (automaton.input_parameters, vars(automaton)) == before


def test_graph_source_exact_dot_and_in_memory_render_delegation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    d = _mature_dfa()
    monkeypatch.chdir(tmp_path)
    graph = d.graph()
    assert type(graph) is Source
    assert graph.source == d.dot()
    with patch.object(Source, "pipe", return_value=b"rendered") as pipe:
        assert d.svg() == b"rendered"
        assert d.pdf() == b"rendered"
        assert d.png() == b"rendered"
    assert pipe.call_args_list == [
        call(format="svg"), call(format="pdf"), call(format="png")
    ]
    assert list(tmp_path.iterdir()) == []


def test_missing_system_dot_raises_clear_library_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATH", "")
    with pytest.raises(ExecutableNotFound):
        _mature_dfa().svg()


@pytest.mark.skipif(which("dot") is None, reason="system Graphviz dot is absent")
def test_real_graphviz_render_when_available() -> None:
    d = _mature_dfa()
    assert b"<svg" in d.svg()
    assert d.pdf().startswith(b"%PDF")
    assert d.png().startswith(b"\x89PNG\r\n\x1a\n")


def test_public_import_and_mro() -> None:
    for cls in (ExtendedDFA, ExtendedNFA, ExtendedGNFA):
        assert cls.dot is VisualisationMixin.dot
        assert cls.svg is VisualisationMixin.svg
        assert cls.tikz is VisualisationMixin.tikz
        assert cls.__mro__.count(VisualisationMixin) == 1
