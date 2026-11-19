# ADR-0032 — Optional web DFA editor and validation adapter

Status: Superseded (placement and installation only; see [ADR-0033](ADR-0033-root-web-application.md))
Date: 2026-11-18

## Context

The user requested a local WSL proof of concept for drawing and validating DFA,
with an explicit alphabet and a minimal canvas interface. Incomplete drawings
must remain editable, whereas mathematical automata are immutable and validated.

## Decision

Use React, TypeScript and React Flow for an independently editable graph document.
Keep stable opaque state IDs separate from editable labels and coordinates.
Use an optional FastAPI adapter under `automata_extensions/web/`; install its
dependencies through the `web` extra. No mixin or upstream behavior is changed.

The HTTP boundary uses bounded strict Pydantic models. Validate list entries,
references and duplicate (state, symbol) pairs before constructing dictionaries.
For a structurally valid draft, construct `ExtendedDFA(allow_partial=False)` and
explicitly invoke its existing validation. Return localized structured issues;
never mutate the draft. Complexity is O(|Q||Σ| + |E|), including missing-edge issues.

The browser owns positions, bounded undo history and versioned local storage.
Edits invalidate results and cancel pending requests. Development uses a local
Vite proxy to FastAPI, both bound to loopback, without adding permissive CORS.

## Alternatives considered

- Constructing an automaton on each UI gesture prevents editing invalid drafts.
- Converting transitions straight to dictionaries silently loses duplicates.
- Reimplementing DFA validation in JavaScript makes the library integration weak.
- Graphviz remains the static rendering engine; it is not a direct-manipulation
  editor. React Flow provides interaction, not an alternative library export API.

## Consequences

The core library still imports without web dependencies. The frontend has its own
Node toolchain and lockfile. This POC validates complete DFA only, allows empty
final-state sets and empty alphabets, and does not add simulation, accounts,
server persistence or production hosting. The editor's frontend source is run
from the checkout, not served by installing the Python package alone.

## Related requirements

W01 in [implementation status](../IMPLEMENTATION_STATUS.md), requested by the user
in addition to the professor's existing requirements. See [guide](../WEB_POC.md).

## Supersedes

None. ADR-0014 continues to govern static library rendering.
