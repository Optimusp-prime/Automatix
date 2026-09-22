# Automatix — Implementation Status

This document is the canonical implementation tracker for the project.

It tracks the requirements from the professor's specification and must be
updated as part of every feature implementation.

## Status legend

| Status | Meaning |
| ------ | ------- |
| TODO | Not designed or implemented yet |
| DESIGN | Specification and architecture are currently being decided |
| IN_PROGRESS | Implementation is in progress |
| VERIFIED | Implemented, tested, documented and validated |
| BLOCKED | Cannot progress until another issue is resolved |

## Current focus

Current feature: #3 — Accessible states (VERIFIED)

Next planned feature: #4 — Test whether a state is accessible (not started)

Current phase: accessible states implemented and validated; awaiting next feature

## Infrastructure

| Item | Status | Notes |
| ---- | ------ | ----- |
| Conda environment | VERIFIED | `automate-env-clean`, Python 3.11 |
| automata-lib dependency | VERIFIED | Fixed at 9.2.0 |
| Upstream reference | VERIFIED | `reference/automata-lib`, tag v9.2.0 |
| Editable packaging | VERIFIED | `python -m pip install -e .` |
| ExtendedFA hierarchy | VERIFIED | MRO validated |
| ExtendedDFA | VERIFIED | Import and instantiation tested |
| ExtendedNFA | VERIFIED | Import tested |
| ExtendedGNFA | VERIFIED | Import tested |
| pytest setup | VERIFIED | Test suite operational |
| Git repository | VERIFIED | Repository initialized |
| GitHub remote | VERIFIED | Initial project pushed; local HEAD matches origin HEAD |

Infrastructure checked on 2026-09-22. The upstream reference commit is
`04dc1947315f322825991b5dc637604567703c9c`. The initial project commit is
`9dcb40b7387a23d888848c874084e9e4ba79d2ae`.

# Professor requirements

Requirement numbers and ordering follow the professor's specification.
Requirements not yet implemented remain TODO, including those for which
upstream already provides behavior: inherited behavior alone does not validate
the project requirement. Planned public APIs remain TBD until feature design
confirms their names and contracts.

## Level 1

| # | Requirement | Planned public API | Layer / Mixin | Status | Tests | Notes |
| - | ----------- | ------------------ | ------------- | ------ | ----- | ----- |
| 1 | DFS iterative and recursive | `dfs(start_state=<private sentinel>, *, recursive=False)` | `TraversalMixin` via `ExtendedFA`, `fa/fa_mixins/` | VERIFIED | `tests/fa/test_traversal.py` | Iterative default; recursive variant; DFA/NFA/GNFA; explicit None is a state; ADR-0004 |
| 2 | BFS | `bfs(start_state=<private sentinel>)` | `TraversalMixin` | VERIFIED | `tests/fa/test_traversal.py` | Level-order discovery with deque; DFA/NFA/GNFA; reuses ADR-0004 |
| 3 | Accessible states | `accessible_states()` | `AccessibilityMixin` via `ExtendedFA` | VERIFIED | `tests/fa/test_accessibility.py` | FrozenSet via existing iterative DFS; DFA/NFA/GNFA; ADR-0005 |
| 4 | Test whether a state is accessible | TBD | TBD | TODO | — | — |
| 5 | Coaccessible states | TBD | TBD | TODO | — | — |
| 6 | Test whether a state is coaccessible | TBD | TBD | TODO | — | — |
| 7 | Useful states | TBD | TBD | TODO | — | — |
| 8 | Trim an automaton | TBD | TBD | TODO | — | — |
| 9 | Test whether an automaton is trim | TBD | TBD | TODO | — | — |
| 10 | Strongly connected components | TBD | TBD | TODO | — | — |
| 11 | Cycle existence detection | TBD | TBD | TODO | — | — |
| 12 | Cycle detection from a given state | TBD | TBD | TODO | — | — |
| 13 | Empty-language decision | TBD | TBD | TODO | — | — |
| 14 | Infinite-language decision | TBD | TBD | TODO | — | — |
| 15 | Word recognition | TBD | TBD | TODO | — | — |
| 16 | Execution trace of a word | TBD | TBD | TODO | — | — |
| 17 | States reachable from a given state | TBD | TBD | TODO | — | — |
| 18 | Predecessors of a state | TBD | TBD | TODO | — | — |
| 19 | Induced subautomaton | TBD | TBD | TODO | — | — |
| 20 | Test whether an automaton is complete | TBD | TBD | TODO | — | — |
| 21 | Completion | TBD | TBD | TODO | — | — |
| 22 | Complement | TBD | TBD | TODO | — | — |
| 23 | Cartesian product of two automata | TBD | TBD | TODO | — | — |
| 24 | Language inclusion | TBD | TBD | TODO | — | — |
| 25 | Language equality | TBD | TBD | TODO | — | — |
| 26 | Automaton isomorphism | TBD | TBD | TODO | — | — |
| 27 | Prefix-closed language test | TBD | TBD | TODO | — | — |
| 28 | Greatest prefix-closed sublanguage | TBD | TBD | TODO | — | — |
| 29 | Distinguishable states | TBD | TBD | TODO | — | — |
| 30 | Myhill–Nerode equivalence classes | TBD | TBD | TODO | — | — |
| 31 | Test whether an automaton is minimal | TBD | TBD | TODO | — | — |
| 32 | Minimization | TBD | TBD | TODO | — | — |
| 33 | Test whether an automaton is deterministic | TBD | TBD | TODO | — | — |
| 34 | Epsilon closure of a state or set of states | TBD | TBD | TODO | — | — |
| 35 | Determinization | TBD | TBD | TODO | — | — |
| 36 | Reverse | TBD | TBD | TODO | — | — |
| 37 | Epsilon-transition elimination | TBD | TBD | TODO | — | — |
| 38 | Universal-language decision | TBD | TBD | TODO | — | — |
| 39 | State elimination on a normalized ε-NFA/GNFA-like automaton | TBD | TBD | TODO | — | — |
| 40 | DOT export | TBD | TBD | TODO | — | — |
| 41 | SVG/PDF/TikZ export | TBD | TBD | TODO | — | — |

## Level 2

| # | Requirement | Planned public API | Layer / Mixin | Status | Tests | Notes |
| - | ----------- | ------------------ | ------------- | ------ | ----- | ----- |
| 42 | Union | TBD | TBD | TODO | — | — |
| 43 | Intersection | TBD | TBD | TODO | — | — |
| 44 | Difference | TBD | TBD | TODO | — | — |
| 45 | Concatenation | TBD | TBD | TODO | — | — |
| 46 | Kleene star | TBD | TBD | TODO | — | — |
| 47 | Left quotient | TBD | TBD | TODO | — | — |
| 48 | Right quotient | TBD | TBD | TODO | — | — |
| 49 | Brzozowski derivatives | TBD | TBD | TODO | — | — |
| 50 | Brzozowski automaton / minimization | TBD | TBD | TODO | — | — |
| 51 | Regex -> NFA conversion using Thompson construction | TBD | TBD | TODO | — | — |
| 52 | NFA -> DFA conversion using subset construction | TBD | TBD | TODO | — | — |
| 53 | DFA -> regex by state elimination | TBD | TBD | TODO | — | — |
| 54 | DFA -> regex by language equations / Arden | TBD | TBD | TODO | — | — |

## Level 3

| # | Requirement | Planned public API | Layer / Mixin | Status | Tests | Notes |
| - | ----------- | ------------------ | ------------- | ------ | ----- | ----- |
| 55 | Automaton <-> regular grammar conversion | TBD | TBD | TODO | — | — |
| 56 | Derivation trees | TBD | TBD | TODO | — | — |
| 57 | Arden lemma | TBD | TBD | TODO | — | — |
| 58 | Systems of rational-language equations | TBD | TBD | TODO | — | — |
| 59 | Myhill–Nerode classes / language quotients | TBD | TBD | TODO | — | — |
| 60 | Residual automaton | TBD | TBD | TODO | — | — |
| 61 | Automaton morphisms | TBD | TBD | TODO | — | — |
| 62 | Syntactic monoid | TBD | TBD | TODO | — | — |

# Feature notes

## #1 — DFS iterative and recursive

- **Specification:** explore reachable states depth-first using either an
  explicit stack or recursive calls. Return a discovery-order list, starting
  with the selected state and including each reachable state exactly once.
- **Design decisions:** use upstream `iter_transitions()` as the common edge
  abstraction. Preserve its neighbor order without sorting heterogeneous
  states. An omitted start uses `initial_state`; explicit `None` selects the
  state `None`, as chosen by the user. Invalid or unhashable starts raise
  upstream `InvalidStateError`.
- **Implementation:** `fa/fa_mixins/traversal.py` provides `TraversalMixin`,
  composed through `ExtendedFA`. The iterative variant uses a stack of neighbor
  iterators; the recursive variant makes actual recursive calls. The private
  `fa/fa_mixins/graph.py` helper builds fresh adjacency once per call. No cache,
  source mutation, representation-specific branch, or additional public graph
  API is introduced. The former `fa/mixins/` scaffolding moved to `fa/fa_mixins/`;
  public imports remain unchanged.
- **Public API:** `dfs(start_state=<private sentinel>, *, recursive=False)`
  returns `list[FAStateT]`. `dfs()` is iterative; `dfs(recursive=True)` is
  recursive; `dfs(None)` explicitly selects an actual `None` state.
- **Tests:** `tests/fa/test_traversal.py`: 78 new parametrized test cases.
  Covers branching and cross edges, full/partial DFA, NFA multiple destinations,
  epsilon-only paths and cycles, GNFA regex/epsilon/absent edges, terminal and
  singleton states, unreachable states, invalid starts, heterogeneous state
  types, actual `None` states, duplicate edges, recursion limits, a single
  transition scan, fresh results, and absence of mutation/cache. Full suite:
  **84 passed**, with one pre-existing `pydub/audioop` deprecation warning.
  Strict mypy checks cover the package and traversal tests. Public imports,
  MRO, package discovery, and manual iterative/recursive examples also pass.
- **Complexity:** let Q be all states, E all emitted transitions including
  parallel edges, and T the cost of exhausting `iter_transitions()`. Adjacency:
  O(|Q| + T) time, O(|Q| + |E|) space. DFS after construction:
  O(|Q_reached| + |E_reached|) time, O(|Q_reached|) additional space.
  Total: O(|Q| + T) time, O(|Q| + |E|) space, assuming constant-time state
  hashing/equality. T includes NFA empty target-set entries and GNFA stored
  `None` entries; a dense GNFA can require quadratic scanning.
- **Related requirements:** #1 only is implemented. Potential future users:
  #2, #3, #11, #12 and #17; their requirements are not advanced.
- **ADR:** [ADR-0004](decisions/ADR-0004-graph-traversal-foundation.md).
- **Known limitations:** recursive DFS may raise `RecursionError` on deep
  paths; use the iterative default. Sibling order is not guaranteed across
  processes. Each call builds the full adjacency even for a small reachable
  component. Automata must satisfy their upstream structural invariants.
  Reference-extension documentation was available as user-supplied excerpts,
  not as a separate full document in the workspace.
- **Git commit:** pending.

## #2 — BFS

- **Specification:** explore reachable states level by level using a queue.
  Return a fresh discovery-order list with the selected start first and each
  reachable state exactly once; omit unreachable states and terminate on cycles.
- **Design decisions:** reuse ADR-0004, `TraversalMixin`, `_build_successors`,
  and the existing private start sentinel. The supplied reference excerpt
  confirms BFS starts at the initial state or a given state. Upstream
  `get_reachable_nodes` returns a set, so it cannot supply the required ordered
  list. No upstream `bfs` name collision was found. No new durable architecture
  decision, public graph API, or ADR is needed; DFS is not refactored.
- **Implementation:** `fa/fa_mixins/traversal.py` uses `collections.deque` and
  `popleft()`. Mark states as discovered when enqueuing them. Build adjacency
  once, using the existing common helper, and keep all working data local.
  There is no cache, mutation of self, or DFA/NFA/GNFA-specific branch.
- **Public API:** `bfs(start_state=<private sentinel>) -> list[FAStateT]`.
  `bfs()` uses `initial_state`; `bfs(None)` selects the real state `None`.
  Absent and unhashable starts raise upstream `InvalidStateError`, using the
  same contract as DFS. No recursive parameter is provided. Discovery order
  is nondecreasing graph distance; ties follow the existing neighbor order.
  Every emitted transition, including epsilon transitions, counts as one edge.
- **Tests:** 13 new test functions, 39 cases after parametrization, in
  `tests/fa/test_traversal.py`. Cover true level order distinct from both DFS
  variants, full/partial DFA, NFA multiple destinations and epsilon edges,
  GNFA regex/epsilon/absent edges, default/explicit/None starts, invalid and
  unhashable starts, singleton states, cycles, unreachable states, repeated
  edges, heterogeneous states, list results, immutability, fresh results,
  and a single transition scan. Full suite: **123 passed**, including all
  78 DFS cases and the six structural cases; one existing `pydub/audioop`
  deprecation warning. The same strict mypy check as for #1 passes on the
  package and traversal tests (14 source files). `git diff --check` is clean.
- **Complexity:** adjacency construction takes O(|Q| + T) time and
  O(|Q| + |E|) space, where Q contains all states, E the emitted transitions
  including parallel edges, and T is the cost of exhausting `iter_transitions`.
  BFS then takes O(|Q_reached| + |E_reached|) time and O(|Q_reached|) additional
  space. Overall: O(|Q| + T) time and O(|Q| + |E|) space, assuming constant-time
  hashing/equality. T includes NFA empty target-set entries and GNFA stored
  `None` entries; a dense GNFA may require quadratic scanning.
- **Related requirements:** implements #2 only, reusing the foundation of #1.
  Possible future users #3, #4 and #17 remain TODO and are not implemented.
- **ADR reference:** [ADR-0004](decisions/ADR-0004-graph-traversal-foundation.md),
  reused without modification. No new ADR created.
- **Known limitations:** adjacency is built globally even for a small reachable
  component. Ordering within a level depends on the upstream transition stream
  and is not guaranteed lexical or stable across processes. Automata must
  satisfy their upstream structural invariants.
- **Git commit:** pending.

## #3 — Accessible states

- **Specification:** an accessible state is reachable from `initial_state`
  through zero or more transitions. Include the initial state, omit unreachable
  states, and treat epsilon transitions as edges. Accessibility is distinct
  from the ability to reach a final state. Professor-source information comes
  exclusively from the supplied prompt excerpts; no PDF was accessed.
- **Design decisions:** separate the unordered accessibility analysis from
  ordered traversal. Place `AccessibilityMixin` in the common ExtendedFA layer.
  Reuse the existing iterative DFS default, which already handles DFA/NFA/GNFA
  and avoids Python recursion limits. No new graph extraction, epsilon logic,
  traversal loop, cache, or source mutation is introduced.
- **Implementation:** `fa/fa_mixins/accessibility.py` contains only the public
  `accessible_states` query in AccessibilityMixin. Its body is
  `return frozenset(self.dfs())`. A private Protocol expresses the required
  no-argument DFS call. ExtendedFA composes the mixin; constructors and MRO
  remain valid. TraversalMixin and `_build_successors` are unchanged.
- **Public API:** `accessible_states()` takes no parameters; accessibility is
  always measured from `initial_state`, including when it is the state `None`.
- **Return type:** `FrozenSet[FAStateT]` (runtime `frozenset`), an immutable,
  unordered state set without duplicates. This respects the mathematical set
  contract, the project's immutable-set preference and upstream conventions,
  while retaining membership and set operations. Use `set(result)` if a mutable
  local working copy is required; no discovery order is part of this API.
- **Tests:** `tests/fa/test_accessibility.py`: 10 new test functions, 26 cases
  after parametrization. Cover complete/partial DFA, full reachability and
  isolated states, zero-length paths, cycles, multiple NFA targets, epsilon-only
  reachability, GNFA absent/epsilon/regex edges, initial `None`, heterogeneous
  states, no duplicates, independence from actual DFS order, frozenset/set
  operations, source immutability, no cache, equality with both traversal sets,
  and a single delegated DFS and transition scan. Full suite: **149 passed**,
  including all existing DFS/BFS and structural tests; one pre-existing
  `pydub/audioop` deprecation warning. Strict mypy passes on 16 source files.
  Public imports, inherited constructors and MRO are validated;
  `git diff --check` is clean.
- **Complexity:** adjacency construction costs O(|Q| + T) time and
  O(|Q| + |E|) space; delegated DFS costs O(|Q_reached| + |E_reached|) time
  and O(|Q_reached|) additional space; building the frozenset adds
  O(|Q_reached|) time and space. Total: O(|Q| + T) time, O(|Q| + |E|) space,
  assuming constant-time hashing/equality. Q includes all states, E all emitted
  transitions including parallel edges, and T is the cost of exhausting
  `iter_transitions`, including empty NFA target-set and GNFA None entries.
- **Related requirements:** implements #3 only. #1 and #2 remain VERIFIED and
  unchanged; #4–#9 and #17 are related future work, not implemented here.
- **ADR:** [ADR-0005](decisions/ADR-0005-accessibility-analysis-layer.md),
  complementing [ADR-0004](decisions/ADR-0004-graph-traversal-foundation.md).
- **Known limitations:** every query rebuilds full adjacency via DFS, even for
  a small reachable component. A dense GNFA may require quadratic scanning.
  Automata must satisfy their upstream structural invariants. The returned
  frozenset deliberately provides neither ordering nor in-place mutation.
- **Git commit:** pending.
