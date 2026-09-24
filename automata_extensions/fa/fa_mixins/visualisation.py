"""Textual and rendered views of the common finite-automaton graph."""

from __future__ import annotations

import re
from collections.abc import Iterator, Set
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from automata.fa.fa import FAStateT

if TYPE_CHECKING:
    from graphviz import Source


class _VisualSource(Protocol):
    """Read-only interface shared by the three concrete FA extensions."""

    @property
    def states(self) -> Set[FAStateT]: ...

    @property
    def initial_state(self) -> FAStateT: ...

    @property
    def final_states(self) -> Set[FAStateT]: ...

    def iter_transitions(self) -> Iterator[tuple[FAStateT, FAStateT, str]]: ...

    def dot(self) -> str: ...

    def graph(self) -> Source: ...

    def tikz(self) -> str: ...


@dataclass(frozen=True)
class _VisualGraph:
    """Temporary immutable description shared by DOT and TikZ."""

    nodes: tuple[tuple[str, str, bool], ...]
    edges: tuple[tuple[str, str, str], ...]
    initial_id: str


def _visual_graph(automaton: _VisualSource) -> _VisualGraph:
    """Assign safe IDs, then collect actual edges once from upstream."""
    initial = automaton.initial_state
    states = [initial, *sorted(
        automaton.states - {initial},
        key=lambda state: (type(state).__module__, type(state).__qualname__, repr(state)),
    )]
    ids = {state: f"s{index}" for index, state in enumerate(states)}
    nodes = tuple(
        (ids[state], str(state), state in automaton.final_states)
        for state in states
    )
    edges_by_source: dict[str, list[tuple[str, str, str]]] = {
        ids[state]: [] for state in states
    }
    for source, target, label in automaton.iter_transitions():
        # GNFA.iter_transitions omits None-valued cells. Empty labels denote
        # real epsilon edges for both NFA and GNFA.
        edges_by_source[ids[source]].append((ids[source], ids[target], label))
    edges = tuple(
        edge for state in states for edge in edges_by_source[ids[state]]
    )
    return _VisualGraph(nodes, edges, ids[initial])


_DOT_UNQUOTED = re.compile(
    r"(?:[A-Za-z_][A-Za-z_0-9]*|-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))\Z"
)
_DOT_KEYWORDS = {"node", "edge", "graph", "digraph", "subgraph", "strict"}


def _dot_atom(value: str) -> str:
    """Quote arbitrary state/edge labels without changing safe examples."""
    if _DOT_UNQUOTED.fullmatch(value) and value.lower() not in _DOT_KEYWORDS:
        return value
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


_LATEX_SPECIAL = {
    "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}",
    "$": r"\$", "&": r"\&", "#": r"\#", "%": r"\%",
    "_": r"\_", "^": r"\textasciicircum{}", "~": r"\textasciitilde{}",
}


def _latex_text(value: str) -> str:
    """Escape text in a TikZ node; preserve explicit line breaks."""
    lines = ["".join(_LATEX_SPECIAL.get(char, char) for char in line)
             for line in value.split("\n")]
    if len(lines) > 1:
        return r"\shortstack{" + r"\\".join(lines) + "}"
    return lines[0]


class VisualisationMixin:
    """Expose one graph through DOT, TikZ and Graphviz renderers."""

    def dot(self: _VisualSource) -> str:
        """Return the automaton's Graphviz DOT source as plain text.

        Safe internal IDs s0, s1, ... are assigned with the initial state
        first; other states use a type/repr key, avoiding comparisons between
        unlike types. Outgoing edges follow upstream iter_transitions order,
        grouped by this node order. Repeated calls on an unchanged automaton
        are stable. NFA epsilon and GNFA empty regex labels display ε; GNFA
        None cells are absent. No Python Graphviz package or binary is needed.

        Returns
        -------
        str
            DOT with an invisible initial pointer, true state labels,
            double-circle accepting states and escaped edge labels.

        Complexity
        ----------
        O(|Q| log |Q| + T + C) time and O(|Q| + |E| + C) space, where T
        exhausts iter_transitions, E is emitted edges and C is total label
        character count. Sorting uses type/repr keys, not state comparison.
        No source mutation, cache or subprocess occurs.

        References
        ----------
        Professor requirement #40; supplied mature VisualisationMixin DOT
        example; automata-lib 9.2.0 FA.iter_transitions implementations.
        """
        view = _visual_graph(self)
        lines = [
            "digraph {", "\trankdir=LR",
            "\t__start__ [shape=point style=invis]",
            f"\t__start__ -> {view.initial_id}",
        ]
        lines.extend(
            f"\t{node_id} [label={_dot_atom(label)} "
            f"shape={'doublecircle' if final else 'circle'}]"
            for node_id, label, final in view.nodes
        )
        lines.extend(
            f"\t{source} -> {target} "
            f"[label={_dot_atom('ε' if label == '' else label)}]"
            for source, target, label in view.edges
        )
        lines.append("}")
        return "\n".join(lines) + "\n"

    def graph(self: _VisualSource) -> Source:
        """Wrap exactly dot() in a renderable graphviz.Source object.

        Returns
        -------
        graphviz.Source
            In-memory DOT source. Construction does not invoke the dot binary.

        Complexity
        ----------
        The dot() construction cost plus O(C) to store its source, where C
        is the DOT text length. No file is created and self is unchanged.

        References
        ----------
        Professor requirement #41; python-graphviz Source API.
        """
        from graphviz import Source

        return Source(self.dot())

    def svg(self: _VisualSource) -> bytes:
        """Render the DOT graph as SVG bytes in memory.

        Returns
        -------
        bytes
            SVG encoded by Graphviz's dot executable.

        Raises
        ------
        graphviz.ExecutableNotFound
            If the system dot executable is absent.
        graphviz.CalledProcessError
            If Graphviz rejects the source or rendering fails.

        Complexity
        ----------
        dot() construction plus external Graphviz layout/rendering cost;
        O(output size) additional space for returned bytes. No file is made.

        References
        ----------
        Professor requirement #41; python-graphviz Source.pipe(format='svg').
        """
        return self.graph().pipe(format="svg")

    def pdf(self: _VisualSource) -> bytes:
        """Render the DOT graph as PDF bytes in memory.

        Returns
        -------
        bytes
            PDF encoded by Graphviz's dot executable.

        Raises
        ------
        graphviz.ExecutableNotFound
            If the system dot executable is absent.
        graphviz.CalledProcessError
            If Graphviz rendering fails.

        Complexity
        ----------
        dot() construction plus external Graphviz layout/rendering cost;
        O(output size) space for returned bytes. No file is made.

        References
        ----------
        Professor requirement #41; python-graphviz Source.pipe(format='pdf').
        """
        return self.graph().pipe(format="pdf")

    def png(self: _VisualSource) -> bytes:
        """Render the DOT graph as PNG bytes in memory.

        Returns
        -------
        bytes
            PNG encoded by Graphviz's dot executable.

        Raises
        ------
        graphviz.ExecutableNotFound
            If the system dot executable is absent.
        graphviz.CalledProcessError
            If Graphviz rendering fails.

        Complexity
        ----------
        dot() construction plus external Graphviz layout/rendering cost;
        O(output size) space for returned bytes. No file is made.

        References
        ----------
        Professor requirement #41; python-graphviz Source.pipe(format='png').
        """
        return self.graph().pipe(format="png")

    def tikz(self: _VisualSource) -> str:
        """Return TikZ/PGF text over the same nodes and edges as dot().

        A shared private graph model supplies DOT and TikZ; TikZ is produced
        directly in Python without invoking Graphviz. State/edge labels are
        LaTeX-escaped. Caller-supplied LaTeX should load the tikz automata
        library; latex() supplies a standalone wrapper doing so.

        Returns
        -------
        str
            A nonempty tikzpicture with initial/accepting nodes and edges.

        Complexity
        ----------
        O(|Q| log |Q| + T + C) time and O(|Q| + |E| + C) space for the
        common graph model, labels and output. No source mutation or binary.

        References
        ----------
        Professor requirement #41 and supplied mature tikz() example;
        requirement #40 provides the shared graph representation.
        """
        view = _visual_graph(self)
        lines = [r"\begin{tikzpicture}[->,>=stealth]"]
        for index, (node_id, label, final) in enumerate(view.nodes):
            styles = ["state"]
            if node_id == view.initial_id:
                styles.append("initial")
            if final:
                styles.append("accepting")
            lines.append(
                f"  \\node[{','.join(styles)}] ({node_id}) at ({3*index},0) "
                f"{{{_latex_text(label)}}};"
            )
        for source, target, label in view.edges:
            displayed = r"$\varepsilon$" if label == "" else _latex_text(label)
            loop = "[loop above]" if source == target else ""
            lines.append(
                f"  \\path[->] ({source}) edge{loop} node "
                f"{{{displayed}}} ({target});"
            )
        lines.append(r"\end{tikzpicture}")
        return "\n".join(lines) + "\n"

    def latex(self: _VisualSource) -> str:
        """Wrap tikz() in a standalone LaTeX document.

        Returns
        -------
        str
            Document loading tikz and its automata library. Nothing is
            written to disk or rendered, and self is unchanged.

        Complexity
        ----------
        tikz() generation cost plus O(output size) wrapping/copying.

        References
        ----------
        Supplied mature latex() compatibility example for requirement #41.
        """
        return (
            "\\documentclass{standalone}\n"
            "\\usepackage{tikz}\n"
            "\\usetikzlibrary{automata}\n"
            "\\begin{document}\n"
            + self.tikz()
            + "\\end{document}\n"
        )
