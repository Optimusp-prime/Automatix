# ADR-0001 — Fixed upstream version

Status: Accepted
Date: 2026-09-22

## Context

Automatix extends automata-lib and needs a stable API and local source
reference for its pedagogical implementation.

## Decision

Pin the dependency to `automata-lib==9.2.0`.
Keep `reference/automata-lib/` as a read-only reference at tag `v9.2.0`,
commit `04dc1947315f322825991b5dc637604567703c9c`.
Never modify upstream source, either in that clone or in site-packages.

## Alternatives considered

- Allow a range of upstream versions.
- Maintain a modified upstream fork.

These alternatives are outside the accepted project architecture.

## Rationale

A fixed version makes source inspection and API compatibility checks
reproducible. Keeping upstream intact separates our extension from the
reference implementation.

## Consequences

Inspect the actual 9.2.0 source before relying on upstream behavior.
All project changes belong outside upstream. A version-policy change
requires a new ADR superseding this decision.

## Related requirements

Cross-cutting foundation for requirements 1–62; no algorithm is implemented
or validated by this decision.

## Supersedes

None.
