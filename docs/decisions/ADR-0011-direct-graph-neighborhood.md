# ADR-0011 — Direct graph neighborhood

Status: Accepted
Date: 2026-09-23

## Context

Professor requirement #18 asks for direct predecessors of one state, ignoring
transition labels. The supplied reference excerpt places graph-neighbor APIs
in GraphMixin and names this one `predecessors_graph` because automata-lib
DFA already defines `predecessors(input_str)` for lexicographically preceding
words. The professor PDFs were not available. ADR-0004 and ADR-0006 already
establish private common adjacency builders in `fa/fa_mixins/graph.py`.

## Decision

Add a small common `GraphMixin` in the existing graph module and compose it
into ExtendedFA. For #18, expose only
`predecessors_graph(state) -> FrozenSet[FAStateT]`. Validate the state with
the existing graph start-state policy, including InvalidStateError for an
absent or unhashable state. Build inverse adjacency with the existing private
`_build_predecessors` helper and return only its direct neighbors as an
immutable set. No cache, source mutation, public `successors_graph`, helper
relocation or DFA/NFA/GNFA-specific parsing is introduced.

## Alternatives considered

- Add the method to AccessibilityMixin: direct neighborhood is a graph
  primitive, while accessibility concerns paths and state-set analysis.
- Name it `predecessors`: would shadow upstream DFA word enumeration.
- Scan transitions separately for every call: would duplicate the accepted
  inverse-adjacency foundation.
- Add `successors_graph` by symmetry: outside requirement #18.

## Rationale

The common mixin keeps graph-neighbor semantics separate from accessibility
and makes the existing inverse builder publicly useful without changing its
behavior. The distinct name preserves the upstream word-oriented method.

## Consequences

Each call rebuilds global inverse adjacency, costing O(|Q| + T) time and
O(|Q| + |E|) space with expected constant-time hashing and equality. Q is
all states, E all emitted edges and T exhausts `iter_transitions`. Parallel
edges collapse in the public frozenset; NFA epsilon edges count, while GNFA
None labels do not. The method returns no indirect ancestors. The concrete
class MRO and upstream `DFA.predecessors` remain intact.

## Related requirements

Implements #18 only. A public successor-neighborhood operation and induced
subautomata are not implemented here. Reuses ADR-0003, ADR-0004 and ADR-0006.

## Supersedes

None.
