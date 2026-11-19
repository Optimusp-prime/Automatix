# ADR-0033 — Separate the web application from the library

Status: Accepted
Date: 2026-11-18

## Context

The user explicitly requested sibling `automata_extensions/` and `web/`
directories and approved `web/backend/` plus `web/frontend/`.

## Decision

Move the existing HTTP adapter to `web/backend/` and the React application to
`web/frontend/`. The backend imports the public library API. Its entry point is
`web.backend.app:app`, launched from the checkout root. The root Python package
continues to distribute only `automata_extensions`; the web application is run
from the checkout. Web dependencies live in backend requirements files, not in
the library's extras. Existing API tests remain in `tests/web/`.

## Alternatives considered

Keeping a nested adapter preserves the old module path but does not provide the
requested separation. A separately published backend package adds unnecessary
packaging work for this local POC.

## Consequences

HTTP paths, payloads, editor behavior and browser storage keys remain unchanged.
Existing launch commands and installation instructions must use the new paths.
This is an application relocation, not a new automata algorithm. No upstream
source, mathematical semantics, immutability or complexity is changed.

## Verification plan

Update imports and documentation; run the full Python suite, frontend tests and
build, strict documentation build, public imports and a live HTTP smoke test.

## Related requirements

W01 in [implementation status](../IMPLEMENTATION_STATUS.md).

## Supersedes

[ADR-0032](ADR-0032-web-dfa-editor.md) for application placement and dependency
installation only. All other editor and validation decisions remain in force.
