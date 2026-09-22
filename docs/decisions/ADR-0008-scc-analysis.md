# ADR-0008 — Common strongly connected component analysis

Status: Accepted
Date: 2026-09-23

## Context

Professor requirement #10 asks for all strongly connected components of an
automaton using Tarjan or Kosaraju. The reference excerpts supplied in the task
prompt describe Tarjan in SCCMixin and a list of frozenset components. The
professor's PDFs were not available. Requirements #11 and #12 concern cycle
detection separately and remain out of scope.

ADR-0004 established `_build_successors` as the private common graph abstraction
over `FA.iter_transitions()`. It includes NFA epsilon edges and omits GNFA
None-valued cells while ignoring transition labels.

## Decision

Place `strongly_connected_components()` in SCCMixin at the common ExtendedFA
layer. Use classic recursive Tarjan with discovery indices, lowlinks, a stack
and on-stack membership. Start a search from every unvisited state, including
states inaccessible from the initial state.

Return `list[FrozenSet[FAStateT]]`. Each frozenset is a maximal component;
the list partitions all states. Neither component order nor member order is
contractual. Do not sort states. Keep all working data local, with no source
mutation or cache. Do not add `is_strongly_connected()` or cycle predicates.

## Alternatives considered

- Kosaraju is also permitted, but requires reverse adjacency and a second
  traversal. Tarjan directly uses the established forward adjacency once.
- Per-concrete-class implementations would duplicate an analysis whose graph
  semantics are already common to DFA, NFA and GNFA.
- Iterative Tarjan would avoid Python's recursion limit but obscure the
  textbook algorithm without a demonstrated need.

## Rationale

SCC analysis is a coherent functional domain distinct from traversal and
accessibility. Reusing the private graph builder preserves established edge
semantics and avoids representation-specific branches. Frozensets reflect the
mathematical components, while a list matches the supplied reference API.

## Consequences

Let Q be all states, E the emitted transitions (including parallel edges), and
T the cost of exhausting `iter_transitions()`. Graph construction and Tarjan
together take O(|Q| + T) time and O(|Q| + |E|) space, assuming constant-time
state hashing and equality. T includes empty NFA target entries and stored
GNFA None cells. Very deep graphs may raise RecursionError because Tarjan is
recursive. A new list is computed per call.

## Related requirements

Implements #10 only. The resulting SCC partition may inform later designs for
#11 and #12, without implementing those requirements now.

## Supersedes

None. Reuses ADR-0004 without changing it.
