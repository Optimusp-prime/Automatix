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
| [ADR-0005](ADR-0005-accessibility-analysis-layer.md) | Accepted | Accessibility analysis layer |
| [ADR-0006](ADR-0006-reverse-graph-foundation.md) | Accepted | Reverse graph foundation |
| [ADR-0007](ADR-0007-automaton-restriction-policy.md) | Accepted | Automaton restriction policy |
| [ADR-0008](ADR-0008-scc-analysis.md) | Accepted | Strongly connected components |
| [ADR-0009](ADR-0009-cycle-analysis.md) | Accepted | Cycle analysis |
| [ADR-0010](ADR-0010-productive-cycles-and-language-finiteness.md) | Accepted | Language finiteness |
| [ADR-0011](ADR-0011-direct-graph-neighborhood.md) | Accepted | Direct graph neighborhoods |
| [ADR-0012](ADR-0012-exact-induced-subautomata.md) | Accepted | Induced subautomata |
| [ADR-0013](ADR-0013-partial-dfa-quotient-transitions.md) | Accepted | Partial DFA quotient transitions |
| [ADR-0014](ADR-0014-shared-visualization-source.md) | Accepted | Shared visualization source |
| [ADR-0015](ADR-0015-immutable-regex-derivatives.md) | Accepted | Immutable regex derivatives |
| [ADR-0016](ADR-0016-brzozowski-reverse-start-normalization.md) | Accepted | Brzozowski reverse normalization |
| [ADR-0017](ADR-0017-regular-grammar-language-semantics.md) | Accepted | Grammar language semantics |
| [ADR-0018](ADR-0018-standalone-arden-solver.md) | Accepted | Standalone Arden solver |
| [ADR-0019](ADR-0019-rational-equation-systems.md) | Accepted | Rational equation systems |
| [ADR-0020](ADR-0020-myhill-nerode-quotient-representation.md) | Accepted | Myhill–Nerode quotients |
| [ADR-0021](ADR-0021-automaton-morphism-projection-quotient.md) | Accepted | Morphisms and projection |
| [ADR-0022](ADR-0022-syntactic-monoid-representation.md) | Accepted | Syntactic monoid |
| [ADR-0023](ADR-0023-pair-table-rounds.md) | Accepted | Read-only pair-table rounds |
| [ADR-0024](ADR-0024-bounded-regex-order-search.md) | Accepted | Bounded regex order search |
| [ADR-0025](ADR-0025-cached-method-runtime-patch.md) | Accepted | Cached-method runtime patch |
| [ADR-0026](ADR-0026-subprocess-diagram-rendering.md) | Accepted | Graphviz subprocess renderer |
| [ADR-0027](ADR-0027-stable-video-layout-and-timeline.md) | Accepted | Stable video layout and independent render cadence |
| [ADR-0028](ADR-0028-epsilon-free-accepting-runs.md) | Accepted | Lazy accepting runs and exact counting for epsilon-free NFAs |
| [ADR-0029](ADR-0029-derivative-dfa-normal-forms.md) | Accepted | Complete DFA from canonical regex derivatives |

## Template

Interactive curves: [ADR-0034 — Local curve metadata](ADR-0034-editor-curve-metadata.md) (Accepted).

Web editor: [ADR-0032 — Optional DFA editor and API](ADR-0032-web-dfa-editor.md)
(placement and installation superseded by
[ADR-0033 — Separate web application](ADR-0033-root-web-application.md), Accepted).

Recent editor decisions:

- [ADR-0034 — Curve metadata](ADR-0034-editor-curve-metadata.md)
- [ADR-0035 — State size](ADR-0035-editor-state-size.md)
- [ADR-0036 — Regex actions](ADR-0036-web-regex-actions.md)
- [ADR-0037 — Obstacle routing](ADR-0037-editor-obstacle-routing.md)
- [ADR-0038 — Degree sizing](ADR-0038-editor-degree-sizing.md)

Verification follow-up: [19 November 2026](../WEB_VERIFICATION.md).

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
