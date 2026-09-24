# ADR-0014 — Shared finite-automaton visualization source

Status: Accepted
Date: 2026-09-24

## Context

Professor requirements #40 and #41 ask for DOT and SVG/PDF/TikZ exports.
The supplied mature excerpts place them in the common VisualisationMixin and
show a precise DOT example with safe internal node IDs. automata-lib 9.2.0
provides `iter_transitions()` on DFA, NFA and GNFA; GNFA omits None cells.
The source PDFs and full mature document were unavailable. The Python
`graphviz` package and system `dot` binary were initially absent locally.

## Decision

Keep VisualisationMixin in ExtendedFA. Build a fresh private immutable visual
description from `states`, `initial_state`, `final_states` and
`iter_transitions()` for each textual export. Assign IDs `s0`, `s1`, ...
with the initial state first, then other states ordered by type/repr keys.
Keep original state values only as escaped labels. Preserve the upstream edge
stream within each source row, including NFA epsilon transitions and real
GNFA regex labels; omit GNFA None-valued cells. Use the same graph description
for DOT and TikZ, so neither exporter parses the other's output.

`dot()` and `tikz()` are pure Python text operations. `latex()` wraps the
TikZ text in a standalone document. `graph()` returns
`graphviz.Source(self.dot())`; `svg()`, `pdf()` and `png()` call its `pipe`
method and return bytes in memory. Rendering may raise the package's normal
missing-executable or process error. It does not write files by default.

Add `graphviz>=0.21,<1` as a Python dependency. The system `dot` executable
is needed only to render SVG/PDF/PNG, not to produce DOT/TikZ/LaTeX or
construct a Source object. Because graphviz 0.21 lacks a `py.typed` marker,
a narrow local mypy stub covers the Source methods and exceptions used here;
runtime behavior still comes from the installed package.

## Alternatives considered

- Rebuild DFA/NFA/GNFA transition structures separately for each exporter:
  duplicates the accepted graph abstraction.
- Generate TikZ by parsing DOT: adds an avoidable parser and risks losing
  label semantics. The common private model provides equivalent layering.
- Invoke Graphviz for DOT or TikZ: text output should work without a binary.
- Use pygraphviz or save rendered files by default: unnecessary dependency
  and side effects for the required in-memory output.

## Rationale

The common model keeps representation-specific transition details in the
upstream iterator and gives every exporter the same states and actual edges.
Stable IDs allow None, tuples and heterogeneous state values. A single
Graphviz adapter keeps binary rendering separate from text generation.

## Consequences

DOT/TikZ construction takes O(|Q| log |Q| + T + C) time and
O(|Q| + |E| + C) space, treating type/repr key comparison as constant-cost;
C is total label length and T is the upstream transition scan. Long state
representations add their string comparison cost to sorting. Graphviz layout
has its own implementation-dependent cost. The optional integration test
skips when `dot` is not installed; deterministic unit tests still verify
the shared graph, delegation, returned bytes and error propagation.

## Related requirements

Implements the shared visualization policy for #40 and #41. #39 continues
to inherit upstream GNFA.to_regex; no high-level DFA/NFA regex conversion
or level-two requirement is introduced.

## Supersedes

None. Complements ADR-0003 and ADR-0004 without changing them.
