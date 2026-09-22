# ADR-0003 — Common ExtendedFA layer

Status: Accepted
Date: 2026-09-22

## Context

DFA, NFA, and GNFA each inherit directly from the abstract upstream FA,
which inherits from Automaton. Shared functionality should not be duplicated
across the concrete extensions.

## Decision

Use ExtendedFA as the common extension layer. Factor generic finite-automaton
algorithms there, through appropriate mixins, whenever technically possible.
Specialize DFA/NFA/GNFA behavior only when semantics or representation
actually require it.

The validated hierarchy is:

- `ExtendedFA(AnalyseMixin, ConversionMixin, GrammaireMixin, VisualisationMixin, FA)`
- `ExtendedDFA(ExtendedFA, DFA)`
- `ExtendedNFA(ExtendedFA, NFA)`
- `ExtendedGNFA(ExtendedFA, GNFA)`

ExtendedFA remains abstract. The concrete extensions retain their upstream
constructors. This architecture has been validated without MRO conflicts.

## Alternatives considered

- Duplicate shared functionality in each concrete extension.
- Omit the common ExtendedFA layer.

## Rationale

A common layer supports reuse and consistent contracts. The tested Python
MRO places the concrete upstream class before FA, preserving constructor
resolution despite the shared FA ancestor.

## Consequences

Check generic behavior against each relevant concrete automaton type.
The existing empty mixins are scaffolding; this decision does not select
future domain-specific mixins or settle algorithm semantics.

## Related requirements

Cross-cutting factoring policy for requirements 1–62. Feature-specific
placement remains TBD in the tracker.

## Supersedes

None.
