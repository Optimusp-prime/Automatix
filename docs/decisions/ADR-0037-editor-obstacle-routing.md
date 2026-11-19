# ADR-0037 — Shared display-only transition routing

Status: Implementation awaiting manual verification (2026-11-19).

## Context

Independent straight edges can hide underneath an unrelated state or coincide
with other transitions. User requests automatic improvement without test runs.
Both the main editor and generated-DFA preview must use the same routing.

## Decision

`routeTransitions(states, transitions, drag?)` groups ordered endpoints and derives
rendered geometry without modifying coordinates, curve metadata or DFA semantics.
Short edges are routed first; a bounded search compares quadratic detours and
loop orientations. Sampled segments are scored against all circular states
(with clearance) and near-parallel occupied segments. A temporary spatial index
limits local segment comparisons. Existing manual curves are preferred when clear;
obstructed ones may be adjusted for display, including during dragging. Dragging
starts from the displayed control and commits via the existing immutable history.

Labels are positioned after all routes, trying nearby points on both sides of
each curve. Scores include states, labels and segments; grouped label width is
estimated conservatively. Labels stay horizontal, clickable and transparent.

## Limits and complexity

This is bounded heuristic routing, not a planar-layout guarantee. Forty samples
per curve and at most 25 candidates approximate geometric collisions. Worst-case
cost is O(C*G*S*(Q+G*S)) for C candidates, G groups, S samples and Q states, plus
label placement; the temporary segment grid improves sparse cases. No persistent
algorithm cache. Transverse crossings are allowed; closely overlapping states
or very dense drawings may remain ambiguous. Unresolved routes are underlined
and the main editor displays a count, rather than silently claiming success.

## Verification

No tests/build/browser/server launched at user request. Pending manual scenarios:
q0→q2 across q1, coincident lanes, opposite directions, moved/resized intermediate
states, loops, manual curves, grouped symbols, preview parity, undo and large
drawings. Existing Python APIs and stored mathematical transitions are unchanged.

## Supersedes

None. Extends ADR-0034/0035/0036 with shared display routing.
