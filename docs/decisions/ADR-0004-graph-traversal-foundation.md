# ADR-0004 — Common graph traversal foundation

Status: Accepted
Date: 2026-09-22

## Context

Professor requirement #1 requires iterative and recursive DFS over reachable
states. The supplied reference-extension excerpts specify TraversalMixin.dfs,
an iterative default, a list result, and graph successors independent of labels.
No separate full reference-extension document was found in the workspace;
only those supplied excerpts are used as its contract.

The following automata-lib 9.2.0 sources and relevant upstream construction
and validation tests were inspected before implementation:

- `automata/base/automaton.py`: AutomatonStateT is Any; states need not be
  strings or mutually orderable. None is accepted as an actual DFA state.
- `automata/base/exceptions.py`: InvalidStateError is the existing exception.
- `automata/fa/fa.py`: iter_transitions yields (source, target, label).
- `automata/fa/dfa.py`: symbol-to-state mappings yield one edge per symbol.
- `automata/fa/nfa.py`: symbol-to-state-set mappings yield one edge per target,
  including the empty-string epsilon label and parallel edges.
- `automata/fa/gnfa.py`: target-to-regex mappings omit None labels from the
  iterator, but retain empty-string epsilon labels. GNFA does not read words;
  this does not prevent traversal of its transition graph.

No upstream dfs or successors_graph method conflicts with the proposed names.
DFA._get_digraph is DFA-specific and cached; get_reachable_nodes in base.utils
uses breadth-first exploration and returns a set. Neither satisfies this DFS
contract with two pedagogical variants and a discovery-order list.

## Decision

Move the common scaffolding from `fa/mixins/` to `fa/fa_mixins/` before the
first algorithm. Keep public imports from `automata_extensions.fa` unchanged.
Add TraversalMixin to ExtendedFA; concrete DFA/NFA/GNFA extensions continue to
inherit their respective upstream classes. Do not create speculative
dfa_mixins/nfa_mixins directories or additional empty feature files.

Use a private reusable `_build_successors` helper in `fa/fa_mixins/graph.py`.
It builds a fresh adjacency mapping once per call from iter_transitions,
without inspecting concrete transition representations. Its tuple-valued
neighbor sequences retain parallel edges and upstream iteration order.
A small read-only Protocol expresses the attributes required by the mixin;
it adds no runtime state or upstream method overrides.

A public GraphMixin/successors_graph API is unnecessary for this feature:
the reference excerpts establish its purpose but not its complete contract.
The private helper supplies the necessary shared abstraction without fixing
an extra public API prematurely. No predecessor helper is added.

Expose only `dfs(start_state=<private sentinel>, *, recursive=False)`.
The omitted argument selects initial_state. Explicit None selects the state
None; it does not select the default. This distinction was explicitly chosen
by the user after validation that upstream accepts None as a state.
Reject an absent or unhashable start with upstream InvalidStateError.

Return a fresh list in discovery order, visiting each reachable state once.
Use an explicit stack of neighbor iterators by default and actual recursive
calls when recursive=True. With an identical transition stream the two
variants have identical discovery order. Do not sort states or promise a
lexical or cross-process order for siblings originating from sets.

Use local working data only: no mutation of self, persistent instance state,
cache, recursion-limit change, NetworkX traversal, or class-specific branch.

## Alternatives considered

- Keep `fa/mixins/`: valid, but migrating the empty scaffolding now establishes
  the common-versus-specific distinction before algorithms accumulate.
- Use None as the default: prevents explicitly choosing a non-initial None
  state; rejected in favor of the user-selected private sentinel.
- Rescan all transitions for each vertex: can cost O(|Q_reached| * T).
- Add a public successors_graph method or full GraphMixin now: unnecessary
  public contract beyond the shared private prerequisite.
- Implement representation-specific traversal or use cached upstream graphs:
  unnecessary duplication or conflict with the no-cache requirement.
- Mark all neighbors when pushing them onto a vertex stack: can prevent a
  pending sibling from being discovered through the active DFS branch.

## Rationale

The upstream transition iterator is the common edge abstraction needed here.
One adjacency construction supports both DFS implementations and future graph
algorithms without repeated scans or assumptions about sortable state names.
An iterator stack mirrors recursive suspension and resumption explicitly.

## Consequences

Let Q be all states, E the emitted transitions (including parallel edges),
and T the cost of exhausting iter_transitions. Building adjacency takes
O(|Q| + T) time and O(|Q| + |E|) space. The subsequent DFS takes
O(|Q_reached| + |E_reached|) time and O(|Q_reached|) additional space.
Total time is O(|Q| + T), assuming constant-time hashing/equality.

For DFA, T is O(|Q| + |E|). NFA iteration also examines symbol entries with
empty target sets. GNFA examines every stored regex/None entry, even when
few edges are emitted; its dense representation may therefore require
quadratic scanning. A small reachable component does not avoid this initial
global scan. This is explicitly documented rather than hidden behind a
reached-only complexity claim.

Recursive DFS remains subject to Python's recursion limit and may raise
RecursionError on deep paths. The default iterative mode avoids that limit.
Tests cover all three classes, branch completion, cross edges, cycles,
unreachable states, invalid starts, None, unorderable states, epsilon edges,
GNFA absent edges, a single transition scan and absence of mutation/cache.

Validation: 78 new test cases and all six existing tests pass (84 total).
Public imports and MRO remain valid; both manual DFS examples return the
expected list. Strict typing validation covers the package and traversal tests.

## Related requirements

Implements #1 only. The foundation can later support #2, #3, #11, #12 and #17,
without implementing or advancing them now.

## Supersedes

None. Refines the common-layer strategy of ADR-0003 without changing it.
