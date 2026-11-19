# Full-canvas editor and resizable states

User request: remove header/footer bars; Excalidraw-like floating controls;
resize circular states without truncating labels. Keep explicit alphabet,
validation, undo, storage, and transition gestures accessible.

## Design and implementation

- [x] Add optional local `size` metadata, minimum diameter based on full label
  measurement, default 64px. Rename grows around the current center if necessary.
  Store sizes, strip them from API, read older documents unchanged.
- [x] Use React Flow NodeResizer with aspect ratio locked, one history checkpoint
  per gesture. Use effective radius everywhere (edges, loops, hit tests, ropes).
  Test long names, resizing bounds, round trips, circle attachment and history.
- [x] Full-screen paper; floating top-center tool palette, top-right alphabet and
  validation, left contextual panel, bottom-left zoom, subtle status bottom-right.
  Hide attribution through supported `proOptions.hideAttribution`; retain dependency
  license. Mobile controls wrap without covering each other.
- [x] Browser verification, frontend tests/build, full pytest, docs/tracker,
  independent review. Stop own servers; no commit/push.

Scope is visual editor only. No Python API or mathematical automaton changes.
The resizer enforces a readable minimum rather than ellipsis or shrinking text.
