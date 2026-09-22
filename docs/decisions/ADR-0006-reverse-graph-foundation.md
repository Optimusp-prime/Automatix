# ADR-0006 — Private reverse graph foundation

Status: Accepted
Date: 2026-09-23

## Context

Requirement #5 asks for states able to reach any final state. The supplied
professor excerpts define reverse exploration from accepting states; no PDF
was accessed. ADR-0004 provides the common transition iterator abstraction,
and ADR-0005 places this analysis in AccessibilityMixin.

Inspection of automata-lib 9.2.0 confirms that iter_transitions yields
(source, target, label) for DFA/NFA/GNFA. NFA epsilon edges are emitted;
GNFA None labels are omitted. DFA/NFA allow empty final sets; the GNFA
constructor supplies final_states={final_state}. No coaccessible_states
name collision exists upstream. Its get_reachable_nodes helper supports
reverse multi-source exploration but requires a NetworkX DiGraph.

## Decision

Add private _build_predecessors in fa/fa_mixins/graph.py. Build inverse
adjacency directly in one pass over iter_transitions, retaining parallel
edges and iterator order in tuple-valued neighbor sequences. Include every
state, even one without predecessors. Reuse _GraphSource without changing
_build_successors or TraversalMixin. No representation-specific branches,
forward adjacency allocation, persistent state or cache are introduced.

AccessibilityMixin.coaccessible_states returns FrozenSet[FAStateT]. Seed
local visited and pending collections with all final states, then explore
the inverse adjacency once using a stack, marking states when scheduled.
A short local loop is sufficient: public DFS/BFS target the forward graph
from one start and need no refactor for this reverse multi-source query.
A private read-only Protocol adds the final_states dependency.

## Alternatives considered

- Reverse an already built successor mapping: valid but allocates an
  unnecessary forward adjacency before constructing the inverse.
- Construct a NetworkX graph for upstream get_reachable_nodes: valid but
  adds an intermediate graph object for a short pedagogical traversal.
- Refactor verified DFS/BFS into generic traversal helpers: unnecessary
  changes to established implementations for this small private operation.
- Run a forward search from each state: repeats work and loses linear cost.
- Add public reverse or predecessors methods: outside requirement #5.

## Rationale

The private inverse adjacency is reusable by future graph analyses while
preserving the common FA abstraction. It does not establish a public
predecessor API. The separate local traversal has different inputs and no
discovery-order contract, unlike public DFS/BFS.

## Consequences

Let Q contain all states, E the emitted transitions, and T the cost of
exhausting iter_transitions. Construction takes O(|Q| + T) time and
O(|Q| + |E|) space. Traversal examines each coaccessible state and its
incoming edges once; freezing adds O(|Q_co|). Total bounds remain
O(|Q| + T) time and O(|Q| + |E|) space with constant-time hashing/equality.
T includes empty NFA target entries and stored GNFA None labels. Even an
empty final set incurs adjacency construction; dense GNFA scanning may be
quadratic. No ordering is exposed by the immutable result.

Validation covers multiple finals, cycles, absent paths, epsilon edges,
GNFA labels, empty final sets, None states, immutability and a single scan.

## Related requirements

Implements #5 only. The private foundation may support #18 and other graph
analyses later. No public predecessors (#18), reverse (#36), or #6 query
is introduced. Requirements #1–#4 retain their existing implementations.

## Supersedes

None. Complements ADR-0004 and ADR-0005 without rewriting either.
