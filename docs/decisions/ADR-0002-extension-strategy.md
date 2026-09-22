# ADR-0002 — Extension strategy

Status: Accepted
Date: 2026-09-22

## Context

Automatix must add pedagogical functionality without modifying automata-lib
or duplicating suitable existing behavior.

## Decision

Use inheritance and mixins. All new functionality lives in
`automata_extensions/`.
Monkey patching is not the default; a concrete compatibility need would
require explicit justification and a separate documented decision.
Prefer wrappers or delegation when upstream already adequately implements
the required functionality and satisfies the pedagogical specification.

## Alternatives considered

- Modify upstream source.
- Use monkey patching as the default extension mechanism.
- Reimplement all existing upstream operations.

## Rationale

Inheritance preserves upstream behavior while mixins group coherent
functionality. Wrappers and delegation avoid unnecessary duplication.

## Consequences

Inspect upstream capabilities and name collisions before feature design.
Mixins must not introduce persistent mutable instance state or mutate the
source automaton; transformations may construct and return new automata.
This record does not decide future mixin decomposition, caching, epsilon
handling, or detailed return contracts.

## Related requirements

Cross-cutting extension strategy for requirements 1–62.

## Supersedes

None.
