# ADR-0034 — Local editable transition curves

Status: Accepted
Date: 2026-11-18

## Context

The user requested hover connection points only in Transition mode, a freely
moving connection preview and direct curve deformation in Selection mode.

## Decision

The browser stores optional `curve: {x, y}` metadata on a draft transition.
It describes a control offset relative to the endpoint midpoint (or the state
center for loops). Documents without this field retain automatic routing.
The HTTP serializer explicitly selects mathematical fields and omits geometry.

Pointer capture and graph-coordinate conversion support movement outside the
starting handle and at arbitrary zoom. Previews are transient; pointer release
inside an actual state opens the symbol dialog. Empty release and cancellation
discard the preview. A completed deformation commits once to document history.
Frames use requestAnimationFrame. Hit detection is O(Q), curve evaluation O(1).

## Alternatives considered

Storing absolute SVG paths would detach curves from moved states. Persisting
every pointer event would flood undo history. Replacing library Graphviz exports
is unnecessary: this metadata belongs only to the interactive web editor.

## Consequences

The existing version-1 local document accepts optional validated finite curve
coordinates. Older documents remain readable. API models, immutable automata
and Python algorithms do not change. The UI uses smooth Bezier geometry, not
a physical rope simulation. Four connection points are shown on hover in
Transition mode; touch devices display them while that mode is active.

## Related requirements

W01 and [gesture plan](../superpowers/plans/2026-11-18-rope-transitions.md).

## Supersedes

None; complements ADR-0032 and ADR-0033.
