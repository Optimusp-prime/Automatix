# ADR-0038 — Diameter adapts to grouped transition degree

Status: Implemented, awaiting manual verification (2026-11-19).

## Decision

User requests larger states when many arrows crowd their boundary, without tests.
Extend ADR-0035 display sizing with derived `autoMinimum` metadata, computed once
per document update. Count ordered source/target groups, not individual symbols.
Loops have one incoming and one outgoing attachment; the initial marker counts
as incoming. The busiest side determines the baseline: 64 + 20 * max(0, degree-2),
capped at 240px. Full label width and manual diameter remain lower bounds too.

Preserve stored state centers when expanding automatically. Do not persist the
automatic minimum or write it into Python API payloads. Pointer origins, drop
targets, routes, node measurements, resize controls and previews consume the
same derived states. Translate controlled node position updates back to stored
coordinates, preventing a jump when dragging an automatically enlarged state.

## Consequences

Deleting transitions can shrink automatic sizing, but does not erase manual
sizes. The algorithm is O(Q+E) plus label measurement. It does not force arbitrary
states apart or guarantee arrow separation in every dense layout; obstacle
routing and its congestion indicator still apply. No mathematical API changes.

## Verification

No tests/build/browser/server run as requested. Pending manual scenarios: three
or more incoming/outgoing groups, grouped symbols, loops/initial marker, manual
resize, dragging, rename, deletion, undo/redo, reload and generated previews.

## Supersedes

None. Complements ADR-0035 and ADR-0037.
