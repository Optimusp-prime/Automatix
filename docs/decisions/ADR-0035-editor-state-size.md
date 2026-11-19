# ADR-0035 — Local state diameters

Status: Accepted (2026-11-18)

## Context

The user requests resizable circles and readable full state names in W01.
Fixed 64px measurements were necessary for stable controlled updates, but must
now reflect the actual circle size.

## Decision

Store optional `size` metadata in the local draft, alongside positions and curves.
`stateSize` centralizes the effective diameter: at least 64px and the measured
14px system-font label width plus 32px padding. Renaming preserves the center.
React Flow NodeResizer keeps aspect ratio and groups a gesture into one history
entry. Manual sizes are bounded at 2048px. Controlled nodes carry their effective
measurements on every update; edge clipping, loops, rope origins and hit testing
use the same radius. Size metadata is excluded from the validation payload.

## Consequences

Existing drafts without sizes remain readable. Full labels replace ellipsis.
Resizing changes only presentation, never mathematical DFA semantics or Python
APIs. Label measurement is O(L); rebuilding node geometry is O(V + total label
length). No algorithm-result caching is introduced.

## Validation

`stateSize.test.ts` covers readable bounds, immutable centered renaming,
persistence, payload isolation and variable-radius geometry. Browser checks cover
drag resizing, single-step undo/redo, reload persistence and a 390px viewport.

## Related requirements

W01 (user-requested editor). Complements ADR-0033 and ADR-0034.

## Supersedes

None.
