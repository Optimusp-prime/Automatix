# ADR-0009 — Global cycle analysis by DFS back edges

Status: Accepted
Date: 2026-09-23

## Context

Professor requirement #11 specifies detecting a cycle by finding a back edge
during DFS. Requirement #12 separately covers cycles reachable from a given
state. The supplied reference excerpts place `has_cycle` and `has_cycle_from`
in CycleMixin; only `has_cycle()` is required now. The professor's PDFs were
not available. Upstream automata-lib 9.2.0 has no `has_cycle()` implementation.

ADR-0004 provides private common adjacency through `_build_successors`, with
NFA epsilon transitions included and GNFA None-valued cells omitted.

## Decision

Add CycleMixin to the common ExtendedFA layer and expose only
`has_cycle() -> bool`. Build adjacency once and inspect every state, not just
the component reachable from the initial state. Use recursive DFS with states
absent from the color map (WHITE), on the active DFS path (GRAY), and fully
explored (BLACK). A transition to GRAY is a back edge and establishes a cycle;
a transition to BLACK does not. A self-loop is a cycle.

Keep all working structures local, with no source mutation or cache. Do not
add `has_cycle_from()` or use SCC analysis as the production shortcut.

## Alternatives considered

- Infer cycles from SCCs: mathematically possible, but does not implement
  the explicit DFS/back-edge method requested for this requirement.
- Treat any previously visited neighbor as a cycle: incorrect for DAGs with
  converging paths and edges to BLACK states.
- Parse transitions separately for DFA, NFA and GNFA: duplicates the common
  graph semantics already fixed by ADR-0004.

## Rationale

Cycle detection is a coherent graph-analysis domain separate from SCC and
traversal. A color-state DFS implements the pedagogical back-edge criterion
directly while preserving the common FA architecture and all-state semantics.

## Consequences

Let Q be all states, E the emitted transitions including parallel edges, and
T the cost of exhausting `iter_transitions()`. Adjacency construction plus
DFS take O(|Q| + T) time and O(|Q| + |E|) space, assuming constant-time
state hashing and equality. T includes NFA empty target entries and GNFA
stored None cells. Recursion may exceed Python's limit on a very deep graph.

## Related requirements

Implements #11 only. Requirement #12 remains TODO and receives no public API
or decided behavior from this record.

## Supersedes

None. Reuses ADR-0004 and leaves ADR-0008 unchanged.
