# ADR-0005 — Accessibility analysis layer

Status: Accepted
Date: 2026-09-22

## Context

Professor requirement #3 defines accessible states as states reachable from
the initial state by zero or more transitions. The task-provided reference
information places this query in AccessibilityMixin. The professor's PDFs
are unavailable and were not read; the supplied excerpts provide the contract.

DFS and BFS are already verified in TraversalMixin under ADR-0004. They include
the initial state, follow NFA epsilon transitions, and support DFA/NFA/GNFA.
No upstream accessible_states name collision was found. Upstream FAStateT
aliases AutomatonStateT (Any); states must work in upstream set/map containers.
Upstream uses both sets and frozensets, including FrozenSet annotations for
NFA state collections and immutable freezing of input sets.

## Decision

Create AccessibilityMixin in `fa/fa_mixins/accessibility.py`, composed through
ExtendedFA. Keep it distinct from TraversalMixin: traversal returns an ordered
discovery sequence, whereas accessibility expresses a mathematical state set.
Only accessible_states is implemented in this mixin at this stage.

Expose `accessible_states() -> FrozenSet[FAStateT]`, with no start parameter.
The initial state is included by the zero-length path. Final-state membership
and the ability to reach a final state do not determine accessibility.

Implement the query as `frozenset(self.dfs())`, delegating once to the existing
iterative default. Do not reimplement DFS, adjacency extraction or epsilon
handling. No source mutation, persistent instance state or caching is added.
A private structural Protocol describes only the no-argument DFS call needed
by the query; it adds no runtime methods to the concrete automata.

Choose frozenset to preserve the unordered mathematical set contract while
preventing mutation of the result. Membership, equality, union, intersection
and difference remain available. The pedagogical set example does not impose
mutability, and the project explicitly favors immutable sets where appropriate.

## Alternatives considered

- Delegate to BFS: mathematically equivalent and valid; the existing iterative
  DFS default already provides the needed traversal without recursion limits.
- Return a mutable set: mathematically valid, but immutable results better
  express this query and the project's immutability conventions.
- Return the DFS list: exposes irrelevant order instead of a state set.
- Add the query to TraversalMixin or duplicate a traversal: blurs the functional
  domains or duplicates algorithms already factored and validated.

## Rationale

This is a durable domain boundary separate from ADR-0004's traversal mechanics.
The common layer keeps DFA/NFA/GNFA behavior consistent and leaves traversal
implementations unchanged. The explicit return contract supports future set
operations without prescribing their implementations.

## Consequences

The result is an immutable set; callers needing a mutable working copy can use
`set(result)`. Discovery order has no meaning in the result.

Let Q be all states, E all emitted edges including parallel transitions, and
T the cost of exhausting iter_transitions. Delegated adjacency construction
costs O(|Q| + T) time and O(|Q| + |E|) space. DFS costs
O(|Q_reached| + |E_reached|) time and O(|Q_reached|) additional space; freezing
its output adds O(|Q_reached|) time and space. Total: O(|Q| + T) time and
O(|Q| + |E|) space, assuming constant-time hashing/equality. T includes empty
NFA target-set entries and stored GNFA None labels. The entire adjacency is
rebuilt per query, even for a small reachable component.

Validation: 26 new accessibility cases pass along with all 123 existing cases
(149 total). Strict typing validation passes for the package and the traversal
and accessibility tests (16 source files). Public imports, concrete upstream
constructors and the MRO remain valid for ExtendedDFA, ExtendedNFA and
ExtendedGNFA. ExtendedFA remains abstract.

## Related requirements

Implements #3 only. AccessibilityMixin is the domain intended to accommodate
related requirements #4–#9 and #17 when separately designed and requested.
This record does not decide or implement their algorithms or public contracts.

## Supersedes

None. Complements ADR-0003 and reuses ADR-0004 without changing either.
