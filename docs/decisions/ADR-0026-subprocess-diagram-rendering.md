# ADR-0026 — Standalone Graphviz subprocess renderer

Status: Accepted
Date: 2026-09-27

## Context

The mature documentation proposes `render_diagram(agraph, filename,
prog="dot", fmt=None)` for an upstream pygraphviz AGraph returned by
`show_diagram()`. It avoids drawing through pygraphviz's C binding when
native DLLs conflict. Existing Automatix `dot()/svg()/pdf()/png()` serve a
different in-memory export path and remain unchanged. The mature helper
does not have a fixed package module.

## Decision

Expose `render_diagram` from `automata_extensions.utils`, implemented in
`utils/render.py` beside `utils/patches.py`. Accept AGraph structurally
through its `string() -> str` operation. Infer the format from the output
suffix when omitted, defaulting to PNG. Search for the selected Graphviz
program under the current Python environment's Library/bin on Windows or
bin on POSIX, then fall back to PATH. Pass DOT as subprocess text input,
capture errors, raise FileNotFoundError for a missing executable and
RuntimeError for a failed render, and return the requested Path. Never
invoke a shell or draw through the pygraphviz binding.

## Alternatives considered

- Add a method to every automaton: the mature text proposes a standalone
  helper, not a mixin API.
- Put the function in VisualisationMixin: it operates on an AGraph rather
  than an automaton and would mix two rendering paths.
- Require a fixed Conda location: unnecessarily ties the API to one
  machine and prevents use with a system Graphviz installation.

## Consequences

The helper writes exactly the requested output artifact; tests use
temporary directories. A fake subprocess verifies arguments and errors,
and a real integration check renders PNG, SVG and PDF. The existing
in-memory rendering pipeline remains intact.

## Related requirements

M10 and primary visualisation requirements #40–#41.

## Supersedes

None.
