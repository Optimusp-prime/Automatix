# ADR-0027 — Stable video layout and independent render cadence

Status: Accepted
Date: 2026-09-27

## Context

M11 initially rendered a new Graphviz PNG for every input symbol. That
recomputed layout, produced one still per logical step and used the public
`fps` argument as the MP4 frame rate. The video had no in-between motion,
and its changing Graphviz label consumed space needed by the automaton.
The M11 redesign must preserve execution semantics, `animate()` HTML and
the existing meaning of `fps` while producing a stable, readable 16:9 video.

## Decision

Keep `fps` as logical input steps per second and add a keyword-only
`render_fps: int = 30` for MP4 frames per second. Build the trace through
the verified `execution_trace()` and `accepts()` operations. Ask Graphviz
once for its `plain` output from the existing DOT source. Its node centers,
edge labels and cubic spline control points become an immutable layout.
Sample each spline by traveled distance, including self-loops, to move a
small marker. Expand each logical step into movement and arrival moments,
with a short initial pause and final result hold.

Use Pillow to compose a fixed 1280×720 scene from that layout and timeline.
Draw the graph, initial pointer, final double circles, curved arrows and
labels as a stable base; add state emphasis, moving marker, word cells and
acceptance badge on each frame. Render at twice the target resolution and
downsample once per frame. Pillow is a declared Python dependency. FFmpeg
remains an optional external runtime executable and still encodes the MP4
inside a temporary directory before replacing the requested destination.

## Alternatives considered

- Re-run Graphviz for every frame: allows style changes in DOT but moves
  nodes and curves and scales poorly with 30-fps timelines.
- Parse SVG paths and rasterize SVG per frame: requires another SVG renderer
  or a more complex path/transform parser. Graphviz `plain` already exposes
  cubic control points and labels in a small documented text format.
- Launch a browser to record the HTML animation: less deterministic and
  conflicts with the browser-free M11 contract.
- Change `fps` to mean video frame rate: silently breaks the existing M11
  public API.

## Consequences

The graph layout is computed once and remains fixed; motion follows the
actual Graphviz spline. Very high logical step rates can leave too few
render frames for visible intermediate motion, but still preserve input
semantics. Fixed output resolution is isolated in the private renderer for
a future 1920×1080 option. Existing SVG/PNG/PDF exports and HTML animation
do not change. Tests cover normal and loop splines, partial DFA blocking,
empty words, accepted/rejected results, video metadata and no mutation.

## Related requirements

M11 visual redesign, primary #16 and #40–#41, ADR-0014.

## Supersedes

None.
