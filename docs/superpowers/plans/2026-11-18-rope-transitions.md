# Interactive transition ropes

User-approved design: hover points only in Transition mode; drag a point to a
state to open the symbol dialog; release on empty space to cancel. Retain the
two-click workflow. In Selection mode drag an existing curve to reshape it,
keeping its endpoints attached. Curves follow the pointer as smooth Beziers.

## Design

The frontend owns this interaction; no mathematical method or API contract changes.
Use pointer capture for continuous gestures, React Flow coordinate conversion
for zoom/pan, and a canvas overlay for the temporary curve. Four hover points per
state, only actionable in Transition mode. A release on the same state allows a
loop. Escape and pointer cancellation discard the gesture. No history entry or
storage write for a temporary rope. Commit one immutable document change on
successful curve deformation, with undo/redo and local persistence.

Optional transition `curve: {x, y}` is a control offset from the endpoint midpoint.
Old documents without it retain automatic routing. Strip curve from API payloads.
Keep validation semantics and existing 64px state measurements unchanged.

## Plan

- [x] Test model round trips, stripping visual data, invalid curve data, endpoint
  clipping, rotated loops and hit testing; implement model/geometry helpers.
- [x] Implement pointer lifecycle in `useRopeGesture.ts`, preview overlay,
  StateNode hover points and draggable TransitionEdge stroke; integrate App.
- [x] Verify empty release, Escape, loop, zoom/pan, curve editing, undo and reload
  in browser; run frontend tests/build, full pytest and strict MkDocs build.
- [x] Independent review, update W01/docs, stop all test servers. No commit/push.

## Verification

15 frontend tests pass, production build passes; 1422 Python tests pass, four
existing video tests skip. Browser confirms creation, empty drop with no undo
entry, loop creation at 83% zoom, reshaping, undo/redo and persisted curves.
Reviewer found an automatic/explicit loop mismatch causing a jump on pointerdown;
a failing regression test was added and the geometries unified. Further review
found no important lifecycle or metadata issue; independent reread of the final
loop fix was unavailable due to the reviewer usage limit. Exact-center control
points now retain circle-boundary attachment, also covered by regression tests.

## Review focus

No stale endpoints after undo/deletion; no edge creation outside state circles;
pointer cancellation and Escape leave the original document intact; one undo per
gesture; metadata stays out of API requests; mode change cancels pending gesture.
