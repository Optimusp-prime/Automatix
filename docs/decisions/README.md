# Architecture Decision Records

An Architecture Decision Record (ADR) captures a durable architectural
decision, its context, alternatives, and consequences. ADRs complement the
requirement tracker; they do not replace feature status updates.

Use sequential identifiers and filenames such as
`ADR-0004-short-title.md`. Choose one status from Proposed, Accepted, or
Superseded and record the date in YYYY-MM-DD format.

An accepted ADR must not be silently rewritten when a decision changes.
Create a new ADR explaining the replacement and reference the previous ADR
in its Supersedes section. Retain the previous decision and its rationale;
mark its status Superseded with a link to the replacement once accepted.

## Current records

| ADR | Status | Decision |
| --- | ------ | -------- |
| [ADR-0001](ADR-0001-fixed-upstream-version.md) | Accepted | Fixed upstream version |
| [ADR-0002](ADR-0002-extension-strategy.md) | Accepted | Inheritance and mixins |
| [ADR-0003](ADR-0003-common-extended-fa-layer.md) | Accepted | Common ExtendedFA layer |
| [ADR-0004](ADR-0004-graph-traversal-foundation.md) | Accepted | Common graph traversal foundation |

## Template

```markdown
# ADR-NNNN — Title

Status: Proposed | Accepted | Superseded
Date: YYYY-MM-DD

## Context

## Decision

## Alternatives considered

## Rationale

## Consequences

## Related requirements

## Supersedes
```

For an initial decision, use `None.` under Supersedes.
Reference requirement numbers from `../IMPLEMENTATION_STATUS.md`.
