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

Current feature: #19 - Induced subautomaton (VERIFIED)

Next planned feature: #20 - Automaton completeness test (not started)

Current phase: exact-state reconstruction verified across ExtendedDFA/NFA/GNFA

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
| 4 | Test whether a state is accessible | `is_accessible(state) -> bool` | `AccessibilityMixin` | VERIFIED | `tests/fa/test_accessibility.py` | Membership in accessible_states; absent hashable state returns False |
| 5 | Coaccessible states | `coaccessible_states()` | `AccessibilityMixin` | VERIFIED | `tests/fa/test_accessibility.py` | FrozenSet; one reverse multi-source traversal; ADR-0006 |
| 6 | Test whether a state is coaccessible | `is_coaccessible(state) -> bool` | `AccessibilityMixin` | VERIFIED | `tests/fa/test_accessibility.py` | Membership in coaccessible_states; absent hashable state returns False |
| 7 | Useful states | `useful_states()` | `AccessibilityMixin` | VERIFIED | `tests/fa/test_accessibility.py` | FrozenSet intersection of accessible and coaccessible states |
| 8 | Trim an automaton | `trim()` | `AccessibilityMixin` with private concrete restrictions | VERIFIED | `tests/fa/test_trim.py` | Same-type new object; empty-language representatives; ADR-0007 |
| 9 | Test whether an automaton is trim | `is_trim() -> bool` | `AccessibilityMixin` | VERIFIED | `tests/fa/test_accessibility.py` | Literal states == useful_states, including empty-language representatives |
| 10 | Strongly connected components | `strongly_connected_components()` | `SCCMixin` via `ExtendedFA` | VERIFIED | `tests/fa/test_scc.py` | Tarjan; all states; list of frozensets; ADR-0008 |
| 11 | Cycle existence detection | `has_cycle() -> bool` | `CycleMixin` via `ExtendedFA` | VERIFIED | `tests/fa/test_cycle.py` | Global DFS back edge; all states; ADR-0009 |
| 12 | Cycle detection from a given state | `has_cycle_from(state) -> bool` | `CycleMixin` via `ExtendedFA` | VERIFIED | `tests/fa/test_cycle.py` | DFS back edge only from supplied state; InvalidStateError |
| 13 | Empty-language decision | `is_empty() -> bool` | `AccessibilityMixin` via `ExtendedFA` | VERIFIED | `tests/fa/test_language_analysis.py` | No accessible accepting state; GNFA final_states; no upstream isempty delegation |
| 14 | Infinite-language decision | `is_finite() -> bool` | `CycleMixin` via `ExtendedFA`; GNFA override | VERIFIED | `tests/fa/test_language_analysis.py` | DFA/NFA productive useful SCC; GNFA raises NotImplementedError by agreed scope; ADR-0010 |
| 15 | Word recognition | `accepts(word) -> bool` | WordMixin via ExtendedFA; GNFA override | VERIFIED | `tests/fa/test_word.py` | Delegates to `accepts_input`; GNFA raises `NotImplementedError` because upstream cannot read words. |
| 16 | Execution trace of a word | `execution_trace(word: str)` | `WordMixin` via `ExtendedFA`; GNFA override | VERIFIED | `tests/fa/test_word.py` | Configurations from upstream; rejected words retain their yielded trace; partial DFA may emit `None`. |
| 17 | States reachable from a given state | `reachable_states(state) -> FrozenSet[FAStateT]` | `AccessibilityMixin` via `ExtendedFA` | VERIFIED | `tests/fa/test_accessibility.py` | Delegates to `dfs(state)`; includes start; inherits `InvalidStateError`. |
| 18 | Predecessors of a state | `predecessors_graph(state) -> FrozenSet[FAStateT]` | `GraphMixin` via `ExtendedFA` | VERIFIED | `tests/fa/test_graph.py` | Direct neighbors from `_build_predecessors`; avoids upstream DFA word API collision. |
| 19 | Induced subautomaton | `induced_subautomaton(states)` | `SubautomatonMixin` via `ExtendedFA` | VERIFIED | `tests/fa/test_subautomaton.py` | Exact requested state set; invalid structural subsets raise `InvalidStateError`; ADR-0012. |
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

## #4 — Test whether a state is accessible

- **Specification:** return membership in the set of states reachable from
  `initial_state`. The professor-source excerpts supplied in the prompt define
  this predicate and its placement; no PDF was accessed. Those excerpts do
  not prescribe an exception for arguments absent from `self.states`.
- **Design:** extend the existing AccessibilityMixin under ADR-0005, without
  changing architecture or requirements #1–#3. No upstream `is_accessible`
  collision was found. The inspected `Automaton.accepts_input` and
  `Automaton.__contains__` distinguish a boolean membership query from a
  validating operation; DFA language predicates `issubset` and `isdisjoint`
  also express boolean properties. These are supporting analogies, not an
  identical upstream state-predicate contract.
- **Public API:** `is_accessible(state: FAStateT) -> bool`, with one required
  state argument and no start-state option. None is an ordinary state value.
- **Behavior for invalid states:** a hashable state absent from the automaton
  returns False, as does a valid but unreachable state. This follows the
  supplied set-membership definition; it is a project choice, not a behavior
  claimed to appear in the unavailable PDFs. DFS/BFS reject invalid starting
  states because they must start a traversal there; this query does not select
  a new start. Native frozenset membership behavior is preserved: unsupported
  keys such as lists raise TypeError; Python's set-to-frozenset lookup handling
  is not overridden. No InvalidStateError is introduced for an absent query.
- **Implementation:** `return state in self.accessible_states()`. The set query
  is called once per predicate call. A private structural Protocol types this
  dependency without changing the existing accessible_states method. No local
  traversal, adjacency extraction, cache, mutation, or new mixin is introduced.
- **Tests:** six new functions, 31 cases after parametrization, appended to
  `tests/fa/test_accessibility.py`. Cover initial/accessible/unreachable/absent
  states, cycles, singleton automata, partial DFA, NFA epsilon-only reachability,
  GNFA, valid and absent None, heterogeneous states, exact bool results,
  equivalence to set membership, list TypeError, no mutation/cache and exactly
  one delegation. All existing tests and fixtures are unchanged. Full suite:
  **180 passed**, with one existing `pydub/audioop` deprecation warning.
  The established strict mypy check passes on 16 source files;
  `git diff --check` is clean. Public imports and the inherited API remain valid.
- **Complexity:** each call recomputes accessible_states: O(|Q| + T) time and
  O(|Q| + |E|) space, including adjacency, traversal and the result set. Q means
  all states, E all emitted transitions, and T the cost of exhausting the
  upstream transition iterator, including empty NFA target sets and stored
  GNFA None labels. The final membership check is expected O(1), but the
  complete query is not O(1). Bounds assume constant-time hashing/equality.
- **Related requirements:** implements #4 only using #3; #1–#3 remain VERIFIED.
  Requirements #5–#62 remain TODO and are not implemented here.
- **ADR:** [ADR-0005](decisions/ADR-0005-accessibility-analysis-layer.md), reused
  without modification. No new ADR is needed for this local predicate contract.
- **Known limitations:** repeated calls repeat the full accessible-set
  computation; callers checking many states can explicitly reuse a set returned
  by accessible_states(). Automata must satisfy upstream structural invariants.
  Membership uses Python's standard equality and hashing semantics.
- **Git commit:** pending.


## #5 ? Coaccessible states

- **Specification:** reverse exploration from accepting states, as specified
  in the professor excerpts supplied in the task; no PDF was accessed.
- **Definition:** q is coaccessible iff a path of zero or more transitions
  leads from q to at least one final state. Finals are included independently
  of accessibility from the initial state.
- **Design decisions:** common AccessibilityMixin under ADR-0005; preserve
  requirements #1?#4 unchanged. A short local stack traversal handles reverse
  multi-source exploration without adapting public forward DFS/BFS.
- **Reverse-graph strategy:** private `_build_predecessors` builds inverse
  adjacency once using upstream `iter_transitions`. No concrete-class branch,
  forward graph allocation, public reverse/predecessors method or cache.
  The inspected upstream `get_reachable_nodes` requires a NetworkX graph;
  constructing one is unnecessary for this small pedagogical traversal.
- **Public API:** `coaccessible_states()` with no parameters.
- **Return type:** `FrozenSet[FAStateT]`, unordered and immutable.
- **Tests:** seven new functions, 21 parametrized cases in
  `tests/fa/test_accessibility.py`. Cover chains, multiple finals, zero-length
  paths, cycles with/without exits, accessible versus coaccessible states,
  disconnected predecessors, singleton and empty-final DFA/NFA, partial DFA,
  NFA epsilon and parallel targets, GNFA None/epsilon/regex labels, None and
  heterogeneous states, no duplicates, no mutation/cache and one scan per call.
  Full suite: **201 passed**, including all 180 previous cases; one existing
  pydub/audioop deprecation warning. Strict mypy passes on 16 source files.
  Public imports remain valid and `git diff --check` reports no errors.
- **Complexity:** O(|Q| + T) time and O(|Q| + |E|) space for inverse adjacency
  and the complete query, assuming constant-time hashing/equality. Q contains
  all states, E all emitted edges including parallel edges, T the cost of
  exhausting the transition iterator (including empty NFA target entries and
  stored GNFA None labels). The multi-source traversal costs
  O(|Q_co| + |E_co|); freezing costs O(|Q_co|).
- **Related requirements:** implements #5 only. #1?#4 remain VERIFIED;
  #6?#62 remain TODO, including public predecessors #18 and reverse #36.
- **ADR:** [ADR-0006](decisions/ADR-0006-reverse-graph-foundation.md),
  complementing unchanged ADR-0004 and ADR-0005.
- **Known limitations:** full inverse adjacency is rebuilt for every call,
  even with no final states; dense GNFA scanning can be quadratic. DFA/NFA
  allow empty final sets; GNFA construction requires one final state.
  Valid upstream automata and standard state hashing/equality are assumed.
- **Git commit:** pending.

## #6 — Test whether a state is coaccessible

- **Specification:** return whether the given state belongs to the set of
  states that can reach at least one final state, as supplied in the task
  prompt. The professor's PDFs were not accessed.
- **Public API:** `is_coaccessible(state: FAStateT) -> bool`, with one required
  state argument. `None` is an ordinary state value.
- **Invalid-state behavior:** a hashable value absent from `self.states`
  returns False. A non-hashable list retains native frozenset membership
  `TypeError`, matching `is_accessible()`. This is the established project
  predicate contract, not an additional claim from the unavailable PDFs.
- **Implementation:** `return state in self.coaccessible_states()` in the
  existing common `AccessibilityMixin`. A private structural Protocol types
  this read-only dependency. No inverse traversal, edge extraction, cache or
  source mutation is added to the predicate.
- **Tests:** nine new functions, 32 cases after parametrization, appended to
  `tests/fa/test_accessibility.py`. Cover final and predecessor states,
  accessible but non-coaccessible states, inaccessible but coaccessible
  states, cycles with and without a final-state exit, partial DFA, NFA epsilon
  and multiple targets, GNFA absent/epsilon/regex edges, valid `None`,
  absent and non-hashable arguments, exact bool results, set membership
  equivalence, one delegation and source immutability. All 201 previous tests
  continue to pass: **233 passed** in total, with one existing pydub/audioop
  deprecation warning. Strict mypy passes on 16 source files.
- **Complexity:** the complete query recomputes `coaccessible_states()`:
  O(|Q| + T) time and O(|Q| + |E|) space, including inverse adjacency,
  multi-source traversal and result creation. Q contains all states, E all
  emitted edges including parallel edges, and T is the cost of exhausting
  `iter_transitions`, including NFA empty target entries and stored GNFA None
  labels. Frozenset membership alone is expected O(1), but the full query
  has the larger bound. Standard constant-time state hashing and equality
  are assumed.
- **Related requirements:** implements #6 using #5. Requirements #1–#5
  remain VERIFIED; #7–#62 remain TODO.
- **ADR:** [ADR-0005](decisions/ADR-0005-accessibility-analysis-layer.md) and
  [ADR-0006](decisions/ADR-0006-reverse-graph-foundation.md), reused without
  modification. No new architectural decision is needed.
- **Known limitations:** repeated calls rebuild the coaccessible set and
  inverse adjacency; dense GNFA scanning may be quadratic. Callers making
  many queries can reuse a separately computed `coaccessible_states()` set.
- **Git commit:** pending.

## #7 — Useful states

- **Specification:** compute the states that are both accessible and
  coaccessible, from the professor-source information in the task prompt;
  the PDF documents were not accessed.
- **Mathematical definition:**
  `useful_states = accessible_states ∩ coaccessible_states`. A useful state
  lies on a path from the initial state to a final state. Accessible-only,
  coaccessible-only and neither-category states are excluded. The set can be
  empty when no final state is reachable from the initial state.
- **Public API:** `useful_states()` with no parameters.
- **Implementation:** in the existing common `AccessibilityMixin`, return
  `self.accessible_states() & self.coaccessible_states()`. A private Protocol
  types these two read-only dependencies. No new traversal, edge extraction,
  representation-specific branch, mutation or cache is added.
- **Return type:** `FrozenSet[FAStateT]`; the intersection of two frozensets
  remains an immutable, unordered frozenset without duplicates.
- **Tests:** nine new functions, 22 parametrized cases in
  `tests/fa/test_accessibility.py`. Cover all-useful and empty results,
  distinct accessible/coaccessible/useful sets, all four membership
  categories, an inaccessible final, an initial state unable to reach any
  final, cycles with and without a final exit, partial DFA, singleton
  initial/final DFA and NFA including None, empty final sets, NFA epsilon
  with heterogeneous states, GNFA present/absent and epsilon edges, exact
  frozenset type, immutability and one call to each existing set query.
  Full suite: **255 passed**, including all 233 previous tests; one existing
  pydub/audioop deprecation warning. Strict mypy passes on 16 source files.
- **Complexity:** each input analysis costs O(|Q| + T) time and
  O(|Q| + |E|) space, and each constructs its own adjacency. Intersecting
  the two sets adds at most O(|Q|) expected time and O(|Q|) result space.
  Overall: O(|Q| + T) time and O(|Q| + |E|) peak space, at a constant factor
  for two scans, assuming constant-time state hashing and equality. Q is all
  states, E all emitted edges including parallel edges, and T exhausts the
  transition iterator, including empty NFA target entries and stored GNFA
  None labels.
- **Related requirements:** implements #7 using #3 and #5. Requirements
  #1–#6 remain VERIFIED; #8–#62 remain TODO. No trim or is_trim behavior is
  introduced.
- **ADR:** [ADR-0005](decisions/ADR-0005-accessibility-analysis-layer.md)
  covers the common accessibility layer; [ADR-0006](decisions/ADR-0006-reverse-graph-foundation.md)
  remains applicable to coaccessible_states. No new ADR is needed.
- **Known limitations:** each call recalculates both input sets, including
  two transition scans; dense GNFA scanning may be quadratic. The result
  intentionally carries no discovery order.
- **Git commit:** pending.

## #8 — Trim an automaton

- **Specification:** return a new automaton without states that cannot
  participate in an accepting path. The professor-source information is
  supplied in the task prompt; the PDFs were not accessed.
- **Mathematical meaning:** for nonempty `useful_states()`, retain exactly
  those states, restrict transitions to endpoints within them, retain the
  initial state and restrict final states. Preserve the recognized language.
- **Reconstruction strategy:** `AccessibilityMixin.trim()` calls
  `useful_states()` once and delegates to a private `_restrict_to_states`
  method on each Extended concrete class. Reconstruct with `type(self)(...)`
  and explicit constructor arguments; do not use `copy()` or generic
  `input_parameters`, and do not expose `induced_subautomaton()`.
- **Concrete return types:** each result is a fresh ExtendedDFA, ExtendedNFA,
  or ExtendedGNFA matching its source type; extension methods remain usable.
- **Empty-useful-state policy:** as explicitly chosen by the user, return
  a valid same-type automaton for the empty language. DFA/NFA retain one
  nonfinal initial state. GNFA retains separate initial/final states with a
  None-labelled absent edge. In this case result states cannot equal the
  empty useful set, because upstream validates that the initial state
  belongs to states; GNFA also requires its final state.
- **DFA `allow_partial` policy:** retain the source option unless deleting
  edges from a complete DFA makes the result partial. Then set it to True,
  as required by upstream validation. An empty-language complete DFA uses
  an initial sink loop for every input symbol; an empty partial DFA uses
  an empty transition row.
- **NFA handling:** restrict each existing source row and each destination
  set, including epsilon transitions. Preserve absent source rows when
  upstream permits them. An empty-language result has no final state or edge.
- **GNFA handling:** restrict the dense target table while keeping required
  None-labelled cells, singular final_state and regex labels. The empty
  representative has no real edge between initial and final.
- **Immutability:** no source states, transitions, final states, options,
  instance attributes or caches are changed; even an already-trim source
  yields a distinct object. No cache is added.
- **Language preservation:** representative words have equal acceptance
  before and after trim for DFA/NFA, including empty-language results;
  a nonempty GNFA example retains the same upstream `to_regex()` result.
- **Tests:** 16 new functions, 38 cases in `tests/fa/test_trim.py`. Cover
  all four state categories, transition/final-state restriction, complete
  and partial DFA, NFA epsilon, GNFA None cells, useful/unuseful cycles,
  None and heterogeneous states, already-trim inputs, all three empty
  policies, source immutability, concrete return types, extension methods,
  repeated trim and representative language preservation. **293 passed**
  in the full suite, including all 255 previous cases; one existing
  pydub/audioop deprecation warning. Strict mypy passes on 17 source files.
- **Complexity:** useful-state analysis costs O(|Q| + T) time and
  O(|Q| + |E|) peak space; restriction is one pass over retained transition
  entries. Upstream constructor freezing/validation adds cost V and
  temporary memory M. Full bounds are O(|Q| + T + V) time and
  O(|Q| + |E| + M) peak space. For DFA/NFA, V is O(|Q| + |E|); GNFA also
  parses retained regex labels, whose lengths are not counted by T.
- **ADR:** [ADR-0007](decisions/ADR-0007-automaton-restriction-policy.md)
  records the durable reconstruction and empty-language policies;
  [ADR-0005](decisions/ADR-0005-accessibility-analysis-layer.md) supplies
  the common layer.
- **Known limitations:** `trimmed.states == useful_states()` is necessarily
  false for an empty useful set. GNFA does not read words; an empty GNFA's
  `to_regex()` returns None at runtime despite its upstream str annotation.
  Upstream NFA word reading via NetworkX rejects None as a state name;
  trimming a None-state NFA is tested structurally, while word acceptance
  uses readable state names. No upstream behavior is patched.
- **Related requirements:** implements #8 using #7. Requirements #1–#7
  remain VERIFIED; #9–#62 remain TODO. No public `is_trim()` (#9) or
  `induced_subautomaton()` (#19) is added.
- **Git commit:** pending.

## #9 — Test whether an automaton is trim

- **Specification:** test whether all states are useful, as stated in the
  professor-source information supplied in the task prompt. The PDFs were
  not accessed.
- **Mathematical definition:** an automaton is trim exactly when every
  present state is both accessible from the initial state and able to reach
  a final state: `states == useful_states()`.
- **Public API:** `is_trim() -> bool`, with no parameters.
- **Implementation:** the common `AccessibilityMixin` compares `self.states`
  with one call to `self.useful_states()`. A private read-only Protocol types
  that dependency. No traversal, transition extraction, cache or mutation
  is added.
- **Empty-language representation consequence:** by ADR-0007, `trim()` must
  retain structural states when `useful_states()` is empty because upstream
  rejects zero-state automata. Those states are not useful, so the returned
  empty-language automaton has `is_trim() is False`. This follows the
  professor's literal definition; there is no empty-language special case.
- **Tests:** 11 new functions, 32 parametrized cases appended to
  `tests/fa/test_accessibility.py`. Cover fully trim and non-trim DFA/NFA/GNFA,
  accessible-only/coaccessible-only/neither states, accepting and nonfinal
  singletons including None, useful and useless cycles, partial DFA, NFA
  epsilon with heterogeneous states, GNFA absent/epsilon/regex edges and
  None final state, exact bool return, equality with useful-state comparison,
  results of nonempty and empty trim, one delegated query and immutability.
  **325 passed** in the full suite, including all 293 previous cases; one
  existing pydub/audioop deprecation warning. Strict mypy passes on 17
  source files.
- **Complexity:** useful_states() computes forward and reverse analyses in
  O(|Q| + T) time and O(|Q| + |E|) peak space; the final set comparison adds
  O(|Q|) expected time. Q includes all states, E all emitted transitions,
  and T exhausts iter_transitions, including empty NFA target entries and
  stored GNFA None labels. Total: O(|Q| + T) time and O(|Q| + |E|) peak
  space, assuming constant-time state hashing and equality.
- **Related requirements:** implements #9 using #7. Requirements #1–#8
  remain VERIFIED; #10–#62 remain TODO.
- **ADR:** [ADR-0005](decisions/ADR-0005-accessibility-analysis-layer.md)
  provides the common layer; [ADR-0007](decisions/ADR-0007-automaton-restriction-policy.md)
  explains mandatory structural states in empty-language trim results.
  Both are reused without changes; no new ADR is required.
- **Known limitations:** each call recomputes both accessibility sets with
  no cache. Dense GNFA scanning can be quadratic. A valid upstream
  empty-language representative cannot satisfy the literal trim predicate
  because it must contain a non-useful initial state.
- **Git commit:** pending.

## #10 - Strongly connected components

- **Specification:** compute every strongly connected component (SCC), also
  called a composante fortement connexe, using Tarjan or Kosaraju. The
  professor-source information was supplied in the task prompt; the PDFs
  were not accessed. Every state, including one unreachable from the initial
  state, belongs to exactly one maximal mutually reachable set.
- **Algorithm:** classic recursive Tarjan with discovery indices, lowlinks,
  a stack and on-stack membership. Search starts anew from every unvisited
  state; a singleton is valid even without a self-loop.
- **Public API:** `strongly_connected_components()`.
- **Return type:** `list[FrozenSet[FAStateT]]`; components are nonempty,
  disjoint, and together cover all states. Neither list order nor order
  within a component is promised.
- **Graph abstraction reused:** `_build_successors` builds adjacency once
  from upstream `FA.iter_transitions()`. No concrete transition parsing,
  cache, or source mutation is added.
- **DFA/NFA/GNFA behavior:** labels are ignored; NFA multiple destinations
  and epsilon transitions are edges; GNFA stored None labels are absent edges.
- **Tests:** 12 test functions, 17 parametrized cases in
  `tests/fa/test_scc.py` cover singletons, chains, cycles, one-way links,
  disconnected and unreachable states, mixed component sizes, partial DFA,
  heterogeneous/None states, NFA epsilon and multi-destinations, GNFA
  None/epsilon labels, partition invariants, source immutability, one graph
  scan, public inheritance and fresh results. The full suite has 342 passed,
  including all 325 previous cases. Strict mypy passes on 19 source files.
- **Complexity:** O(|Q| + T) time and O(|Q| + |E|) space, assuming
  constant-time hashing and equality. Q includes every state, E the emitted
  transitions including parallel edges, and T the cost of exhausting
  iter_transitions, including empty NFA target entries and GNFA None slots.
- **Recursion limitation:** a sufficiently deep graph may exceed Python's
  recursion limit. No recursion-limit change is made.
- **ADR:** [ADR-0008](decisions/ADR-0008-scc-analysis.md), reusing the
  [ADR-0004](decisions/ADR-0004-graph-traversal-foundation.md) graph layer.
- **Related requirements:** #11 and #12 concern cycle detection and remain
  TODO, as do all other requirements #11-#62. Neither cycle predicate nor
  `is_strongly_connected()` is implemented.
- **Git commit:** pending.

## #11 - Cycle existence detection

- **Specification / French meaning:** detect the existence of a directed
  cycle (detection d'existence de cycle) via a DFS back edge. The professor
  information came from the task prompt; the PDFs were not accessed.
- **Algorithm:** recursive DFS with WHITE (unseen), GRAY (active path), and
  BLACK (fully explored) states. An edge to GRAY is a back edge and proves a
  cycle. An edge to BLACK does not. A self-loop is a cycle.
- **Public API:** `has_cycle() -> bool`, without parameters.
- **Global graph semantics:** the search covers every state, including
  components inaccessible from the initial state. It builds adjacency once
  with `_build_successors` and does not delegate to SCC analysis.
- **DFA/NFA/GNFA behavior:** labels are ignored; NFA multiple destinations
  and epsilon transitions count as edges, while GNFA None-valued cells do not.
- **Tests:** 8 test functions, 22 parametrized cases in
  `tests/fa/test_cycle.py` cover one-state graphs, self-loop, chains, cycles
  of two and three states, DAG edges to BLACK, inaccessible cycles, partial
  DFA, NFA branching and epsilon, GNFA None/epsilon labels, None and
  heterogeneous states, exact bool result, immutability, fresh graph scans,
  shared inheritance and no SCC delegation. The full suite has 364 passed,
  including all 342 previous cases. Strict mypy passes on 21 source files.
- **Complexity:** O(|Q| + T) time and O(|Q| + |E|) space, assuming
  constant-time hashing and equality. Q includes all states, E all emitted
  transitions including parallel edges, and T exhausts iter_transitions,
  including empty NFA target entries and GNFA None slots.
- **Recursion limitation:** sufficiently deep graphs may exceed Python's
  recursion limit; the limit is not changed.
- **ADR:** [ADR-0009](decisions/ADR-0009-cycle-analysis.md), reusing the
  [ADR-0004](decisions/ADR-0004-graph-traversal-foundation.md) graph layer.
- **Related requirements:** #12 (cycle from a given state) and #13-#62 remain
  TODO. No `has_cycle_from()`, `is_empty()` or `is_finite()` is added.
- **Git commit:** pending.

## #12 - Cycle detection from a given state

- **Specification / French meaning:** detect whether a directed cycle is
  reachable from a given state (detection d'existence de cycle a partir d'un
  etat). The professor information came from the task prompt; the PDFs were
  not accessed. The cycle need not contain the starting state.
- **Difference from `has_cycle()`:** the global #11 query starts DFS from
  every unvisited state; this query starts only from the supplied state.
  Thus a cycle elsewhere makes the global result True but the local result
  False.
- **Public API:** `has_cycle_from(state: FAStateT) -> bool`. Explicit None
  denotes the actual None state when present. No default start is provided.
- **Invalid-state contract:** absent hashable and unhashable states raise
  upstream `InvalidStateError`, matching `dfs(start_state)`. A valid None
  state is accepted.
- **Algorithm / reachable-subgraph semantics:** a private `_has_back_edge`
  helper shares the WHITE/GRAY/BLACK recursive DFS with `has_cycle()`. An
  edge to GRAY proves a cycle; an edge to BLACK does not. One root restricts
  the DFS to its reachable subgraph. `_build_successors` still builds global
  adjacency once per call. No SCC shortcut, cache, mutation or public
  `reachable_states()` API is added.
- **DFA/NFA/GNFA behavior:** labels are ignored; NFA multiple destinations
  and epsilon transitions are edges; GNFA None-labelled cells are not.
- **Tests:** 9 new functions, 23 new parametrized cases added to
  `tests/fa/test_cycle.py`. They cover isolated states, self-loop, chain,
  start-containing and downstream cycles, global-but-unreachable cycles,
  DAG edges to BLACK, partial DFA, NFA branching and epsilon, GNFA, valid
  None and heterogeneous states, invalid and unhashable starts, exact bool,
  immutability, one adjacency build per call, MRO and no SCC delegation.
  The full suite has 387 passed, including all 364 previous cases. Strict
  mypy passes on 21 source files.
- **Complexity:** global adjacency construction is O(|Q| + T) time and
  O(|Q| + |E|) space. DFS on reachable states adds
  O(|Q_reached| + |E_reached|) time and O(|Q_reached|) space. Overall:
  O(|Q| + T) time and O(|Q| + |E|) space, assuming constant-time hashing
  and equality. T exhausts iter_transitions, including empty NFA target
  entries and GNFA stored None slots. Deep paths may hit Python's
  recursion limit.
- **ADR:** [ADR-0009](decisions/ADR-0009-cycle-analysis.md) supplies the
  CycleMixin and back-edge policy;
  [ADR-0004](decisions/ADR-0004-graph-traversal-foundation.md) supplies the
  graph and start-state conventions. Neither accepted ADR is rewritten.
- **Related requirements:** #13-#62 remain TODO. No #17 reachable-states
  method or language decision is implemented.
- **Git commit:** pending.

## #13 - Empty-language decision

- **Specification / French meaning:** decide whether the recognized language
  is empty (decision pour le probleme du langage vide). The professor
  information came from the task prompt; the PDFs were not accessed.
- **Mathematical criterion:** the language is empty exactly when no final
  state is accessible from the initial state, including by a zero-length
  path. Equivalently, `accessible_states() & final_states` is empty.
- **Public API:** `is_empty() -> bool`, without parameters.
- **Accepting-state representation:** DFA and NFA take `final_states` in
  their constructors. GNFA takes one `final_state`, but upstream GNFA 9.2.0
  also exposes `final_states` as a frozenset containing that state. The
  common criterion therefore needs no concrete-type branch.
- **Implementation:** `AccessibilityMixin` calls `accessible_states()`
  once and tests disjointness with `final_states`. No DFS/BFS duplication,
  upstream `isempty()` delegation, word enumeration, mutation, or cache.
- **Empty trim representation:** under ADR-0007, a trim result for an empty
  language retains mandatory structural states, but no accepting state is
  reachable. `is_empty()` correctly returns True for DFA, NFA and GNFA.
- **Tests:** 11 test functions, 25 parametrized cases in
  `tests/fa/test_language_analysis.py` cover accepting initial states,
  one-step and longer accepting paths, unreachable or absent final states,
  cycles with and without reachable finals, partial DFA, NFA epsilon, GNFA
  None slots and singular final state, None and heterogeneous states, exact
  bool, mathematical equivalence, immutability, empty-language trim
  representatives, one delegated query, no upstream `isempty()` delegation
  and common public inheritance. The full suite has 412 passed, including
  all 387 previous cases. Strict mypy passes on 22 source files.
- **Complexity:** O(|Q| + T) time and O(|Q| + |E|) peak space, assuming
  constant-time hashing and equality. Q includes all states, E emitted
  transitions including parallel edges, and T exhausts iter_transitions,
  including empty NFA target entries and GNFA stored None slots. The
  disjointness test adds at most O(|Q|) expected time.
- **Related requirements:** #14 (infinite-language decision) remains TODO,
  as do #15-#62. No `is_finite()` method is added.
- **ADR:** [ADR-0005](decisions/ADR-0005-accessibility-analysis-layer.md)
  supplies the common accessibility layer;
  [ADR-0007](decisions/ADR-0007-automaton-restriction-policy.md) explains
  empty-language trim representatives. No new ADR is needed.
- **Git commit:** pending.

## #14 - Finite/infinite language decision

- **Specification / terminology:** decide whether the recognized language
  is finite (langage fini) or infinite (langage infini). The professor
  information came from the task prompt; the PDFs were not accessed.
- **Professor criterion and semantic refinement:** an accessible and
  coaccessible cycle, equivalently a cycle among useful states, is relevant
  only when repetition can increase accepted word length. The user
  explicitly chose real language finiteness: an epsilon-only useful NFA
  cycle is finite, while a useful cycle with a consuming edge is infinite.
- **Public API / placement:** `is_finite() -> bool` in `CycleMixin` for
  ExtendedDFA and ExtendedNFA. ExtendedGNFA overrides the method to raise
  `NotImplementedError` by the user's explicit scope choice. No
  `is_infinite()` alias is added.
- **Useful-cycle definition / implementation:** compute `useful_states()`
  and the existing SCC partition. A consuming transition with both ends
  in the same useful SCC can be repeated on an accepting path, making the
  language infinite. The method returns the opposite boolean. It does not
  call `has_cycle()`, `trim()` or upstream `isfinite()`, and does not modify
  the private back-edge helper or the #11/#12 public contracts.
- **Induced useful-subgraph restriction:** only edges with both endpoints
  useful can establish an infinite accepted language. A useful state's
  outgoing edge into a dead cycle cannot create a false positive. SCC
  membership also prevents a one-time consuming exit from an epsilon cycle
  from being mistaken for repeatable consumption.
- **DFA/NFA/GNFA convention:** DFA transitions consume symbols; NFA
  transitions labeled `""` are epsilon and do not increase word length.
  GNFA regex labels can describe infinitely many words on one acyclic
  edge, such as `a*`; graph-only SCC analysis cannot decide their finitude.
  GNFA support is deliberately deferred rather than returning a wrong
  boolean. No regex conversion is implemented.
- **Tests:** 12 new functions, 26 new parametrized cases added to
  `tests/fa/test_language_analysis.py`. They cover acyclic and empty
  languages, useful consuming cycles and self-loops, accessible-only and
  coaccessible-only cycles, a dead cycle branching from a useful state,
  multiple cycles, partial DFA, epsilon-only NFA cycles, consuming edges
  within and outside SCCs, None/heterogeneous states, nonempty and empty
  trim results, exact bool, immutability, no upstream/trim/global-cycle
  delegation, and explicit GNFA rejection. The full suite has 438 passed,
  including all 412 previous cases. Strict mypy passes on 22 source files.
- **Complexity:** useful-state analysis, SCC computation and one labeled
  transition scan each cost O(|Q| + T) time and O(|Q| + |E|) peak space;
  together they retain those bounds at constant factors, assuming
  constant-time state hashing and equality. Q includes all states, E
  emitted edges, and T exhausts iter_transitions. Recursive Tarjan can
  reach Python's recursion limit. The GNFA rejection is O(1).
- **ADR:** [ADR-0010](decisions/ADR-0010-productive-cycles-and-language-finiteness.md)
  records the productive-cycle policy and GNFA scope. It reuses
  [ADR-0005](decisions/ADR-0005-accessibility-analysis-layer.md),
  [ADR-0008](decisions/ADR-0008-scc-analysis.md), and
  [ADR-0009](decisions/ADR-0009-cycle-analysis.md), without rewriting them.
- **Related requirements:** #15-#62 remain TODO. No word recognition,
  execution trace, reachable-states API, or conversion is implemented.
- **Git commit:** pending.

## #15 - Word recognition

- **Specification / French meaning:** decide whether a complete input word
  belongs to the automaton's language (reconnaissance d'un mot). The
  professor information came from the task prompt; the PDFs were not accessed.
- **Public API / placement:** `accepts(word: str) -> bool` in `WordMixin`,
  exposed through `ExtendedFA`. `str` matches upstream's `accepts_input`
  signature. `ExtendedGNFA` overrides the method solely to report its
  unsupported direct recognition clearly.
- **Delegation:** the common method returns `self.accepts_input(word)`.
  It does not reimplement simulation or call `read_input_stepwise` itself.
- **DFA:** upstream deterministically reads the word; a missing transition
  or invalid symbol is rejected with `False`, as observed in v9.2.0.
- **NFA / epsilon:** upstream manages branching and epsilon closures,
  including epsilon before or after consumption and acceptance of the
  empty word through epsilon.
- **GNFA limitation:** although GNFA inherits `accepts_input`, its
  `read_input_stepwise` unconditionally raises `NotImplementedError` in
  automata-lib 9.2.0. `ExtendedGNFA.accepts` therefore raises a descriptive
  `NotImplementedError`; no regex engine or conversion was added.
- **Invalid symbols / empty word:** the wrapper preserves upstream
  `accepts_input` behavior. Observed DFA/NFA invalid symbols return `False`;
  empty-word acceptance depends on the initial/final and epsilon structure.
- **Tests:** 10 new test functions, 29 parametrized cases in
  `tests/fa/test_word.py` cover DFA/NFA accepted and rejected words,
  multiple lengths, partial DFA, invalid symbols, empty word, NFA branching
  and epsilon, direct delegation, exact bool, immutability, common MRO and
  explicit GNFA rejection. The full suite has 467 passed, including all
  438 previous cases. Strict mypy passes on 24 source files.
- **Complexity:** the alias adds O(1) time and space beyond upstream
  simulation. DFA simulation is linear in word length; NFA simulation also
  depends on active-state sets and epsilon closures. GNFA rejection is O(1).
- **ADR:** [ADR-0002](decisions/ADR-0002-extension-strategy.md) establishes
  upstream delegation when functionality already exists. No new durable
  architectural decision or ADR was needed.
- **Related requirements:** #16-#62 remain TODO. No execution-trace API
  was introduced.
- **Git commit:** pending.

## #16 - Execution trace of a word

- **Specification / source precedence:** the professor asks for the
  succession of states (DFA) or active-state sets (NFA). This takes
  precedence over the mature reference's DFA transition-triplet format.
  The professor information came from the task prompt; the PDFs were not
  accessed.
- **Public API / placement:** `execution_trace(word: str)` in the existing
  `WordMixin` through `ExtendedFA`. It returns a list of configurations,
  without an acceptance flag or another public trace API.
- **DFA configurations:** upstream emits the initial state and one state
  per consumed symbol. On a partial DFA, a missing transition is emitted
  as `None`, which remains in the list. Thus the concrete shape is a list
  of states or `None` where upstream reports a missing transition.
- **NFA configurations / epsilon:** upstream emits immutable `frozenset`
  active-state configurations. The initial and subsequent sets already
  include epsilon closure. A missing path can yield `frozenset()`.
- **Rejected words:** DFA and NFA emit the last configuration before
  raising `RejectionException`. The wrapper collects each yield and catches
  only that upstream exception, returning the complete trace for a rejected
  word. Other errors propagate.
- **GNFA limitation:** automata-lib 9.2.0 GNFA's `read_input_stepwise`
  unconditionally raises `NotImplementedError`. `ExtendedGNFA` raises a
  descriptive error as for requirement #15; no GNFA simulation is added.
- **Delegation / implementation:** iterate `read_input_stepwise(word)` once
  and append its configurations to a list. No DFA/NFA simulation is copied.
- **Tests:** 10 new functions and 18 parametrized cases in
  `tests/fa/test_word.py` cover accepted/rejected and empty words, DFA
  partial transitions, NFA branching and epsilon before/after consumption,
  exact upstream agreement for accepted words, immutable NFA configurations,
  unrelated-error propagation, GNFA rejection and source immutability.
  The full suite has 485 passed, including all 467 prior cases. Strict mypy
  passes on 24 source files.
- **Complexity:** upstream simulation cost plus O(k) appends for k yielded
  configurations; O(k) list references in addition to configuration storage.
  For DFA, k = |word| + 1 and simulation is O(|word|). NFA simulation
  additionally depends on active sets and epsilon closures; storing all
  configurations can require O(k|Q|) space.
- **ADR:** [ADR-0002](decisions/ADR-0002-extension-strategy.md) supports
  delegation to upstream. The rejected-trace and partial-DFA conventions
  are recorded here; no new cross-feature architectural ADR was needed.
- **Related requirements:** #17-#62 remain TODO. No reachable-states API,
  transition-triplet trace, animation or visualization was introduced.
- **Deferred enhancement (outside professor requirements):** a future
  `execution_trace(word, *, format="transitions")` option, or equivalent
  separate API, could provide `(configuration_before, symbol,
  configuration_after)` events for web animation. This is backlog only:
  the current #16 API and its verified configuration-sequence contract are
  unchanged, with no implementation or tests for the proposed format.
- **Git commit:** pending.

## #17 - Reachable states from a given state

- **Specification / French meaning:** calculate all states reachable by a
  directed path from an arbitrary supplied state (etats atteignables depuis
  un etat donne). The starting state belongs by the length-zero path.
  The professor information came from the task prompt; the PDFs were not
  accessed.
- **Public API / placement:** `reachable_states(state) -> FrozenSet[FAStateT]`
  in `AccessibilityMixin` through `ExtendedFA`. The immutable set has no
  discovery-order or duplicate-state contract.
- **Relation to `accessible_states()`:** reaching from `initial_state`
  returns exactly `accessible_states()`. Unlike that query, an arbitrary
  start can belong to a component inaccessible from the initial state.
- **DFS reuse / implementation:** return `frozenset(self.dfs(state))` using
  the established iterative default. No adjacency builder, graph parsing,
  DFS loop, cache or source mutation is added.
- **Invalid-state behavior:** upstream `InvalidStateError` from `dfs(state)`
  covers absent hashable and unhashable starts. Explicit `None` selects the
  real state None when present; it never means the default initial state.
- **DFA/NFA/GNFA semantics:** directed DFA transitions, all NFA destinations
  including epsilon, and GNFA real labels including `""` follow the common
  DFS graph foundation. GNFA `None` labels do not create edges.
- **Tests:** 10 new functions and 25 parametrized cases in
  `tests/fa/test_accessibility.py` cover the initial/intermediate/isolated
  starts, branches, cycles and self-loops, inaccessible components,
  partial DFA, NFA branching and epsilon, GNFA present/absent edges,
  None and heterogeneous states, invalid inputs, exact frozenset type,
  no duplicates and immutability. The full suite has 510 passed,
  including all 485 prior cases; strict mypy passes on 24 source files.
- **Complexity:** delegated global adjacency construction plus DFS and
  freezing cost O(|Q| + T) time and O(|Q| + |E|) space, assuming constant-time
  hashing/equality. Q is all states, E emitted transitions, and T exhausts
  `iter_transitions`, including empty NFA targets and GNFA None slots.
- **ADR:** [ADR-0004](decisions/ADR-0004-graph-traversal-foundation.md)
  provides DFS and the start-state contract;
  [ADR-0005](decisions/ADR-0005-accessibility-analysis-layer.md) provides
  the common layer and immutable-set policy. No new ADR was needed.
- **Related requirements:** #18-#62 remain TODO. No public predecessor or
  induced-subautomaton API was added.
- **Git commit:** pending.

## #18 - Predecessors of a state

- **Specification / French meaning:** calculate the direct incoming
  neighbors of a state (predecesseurs directs), independently of transition
  labels. The professor information came from the task prompt; the PDFs
  were not accessed. Indirect ancestors are not included.
- **Public API / name choice:**
  `predecessors_graph(state) -> FrozenSet[FAStateT]`. The `_graph` suffix
  avoids shadowing upstream `DFA.predecessors(input_str, ...)`, which
  enumerates lexicographically preceding words rather than states.
- **Placement / inverse adjacency:** `GraphMixin` lives in the existing
  common `fa/fa_mixins/graph.py` and is composed through `ExtendedFA`.
  It validates state, calls the accepted `_build_predecessors(self)` once,
  and freezes only the tuple at that state. The private builders are not
  moved or reimplemented; there is no reverse DFS, cache or mutation.
- **DFA/NFA/GNFA semantics:** any real incoming edge counts. Parallel
  edges collapse to one source; self-loops include the queried state.
  NFA multi-destinations and epsilon transitions count as direct edges.
  GNFA real regex and empty-string labels count; None labels do not.
- **Invalid-state policy:** absent hashable and unhashable state values
  raise upstream `InvalidStateError`, matching the common traversal
  start-state contract. None is an ordinary valid state when present.
- **Tests:** 11 new functions and 23 cases in `tests/fa/test_graph.py`
  cover one/multiple/no predecessors, direct versus indirect ancestry,
  parallel edges, self-loops and cycles, inaccessible sources, DFA and
  partial DFA, NFA multi-destinations and epsilon, GNFA real/None labels,
  None and heterogeneous states, invalid inputs, immutable return type,
  source immutability, common MRO and intact upstream word enumeration.
  The full suite has 533 passed, including all 510 previous cases;
  strict mypy passes on 25 source files.
- **Complexity:** O(|Q| + T) time and O(|Q| + |E|) auxiliary space per
  call, including global inverse-adjacency construction and freezing the
  direct neighbors, with expected constant-time hashing and equality.
  Q is all states, E emitted edges and T exhausts `iter_transitions`,
  including empty NFA target entries and stored GNFA None slots.
- **ADR:** [ADR-0011](decisions/ADR-0011-direct-graph-neighborhood.md)
  records the new common GraphMixin domain and name-collision policy.
  It reuses [ADR-0003](decisions/ADR-0003-common-extended-fa-layer.md),
  [ADR-0004](decisions/ADR-0004-graph-traversal-foundation.md) and
  [ADR-0006](decisions/ADR-0006-reverse-graph-foundation.md).
- **Related requirements:** #19-#62 remain TODO. No public
  `successors_graph` or induced-subautomaton API was added.
- **Git commit:** pending.

## #19 - Induced subautomaton

- **Specification / French meaning:** extract the subautomaton induced by a
  requested state set (sous-automate induit). The result contains exactly
  that set and only transitions whose source and destination belong to it.
  The professor information came from the task prompt; the PDFs were not
  accessed.
- **Public API / placement:** `induced_subautomaton(states)` in
  `SubautomatonMixin` through `ExtendedFA`. It accepts an iterable once,
  materializes a frozenset, and returns a fresh automaton of the same
  Extended concrete type.
- **Relation to ADR-0007 / trim:** the three private `_restrict_to_states`
  reconstruction helpers established for trim are reused without
  duplicating their transition filtering. The helper contract is now
  declared abstractly on ExtendedFA for typing. Trim's exceptional
  empty-language representative remains unchanged; induction rejects an
  empty request and never adds states outside the requested set.
- **Validation / structural states:** unknown or unhashable requested
  states, an empty set, or a subset lacking `initial_state` raise upstream
  `InvalidStateError`. GNFA additionally requires its singular
  `final_state`; its concrete helper checks this explicitly. Other
  constructor validation errors are not hidden.
- **DFA reconstruction:** retain internal labeled transitions, original
  alphabet and `final_states & requested`. A complete source may yield a
  partial result with `allow_partial=True`; no sink state is created.
- **NFA reconstruction / epsilon:** retain sources in the set and filter
  each destination set, including epsilon transitions. Empty destination
  sets remain valid; no closure or determinization is performed.
- **GNFA reconstruction:** retain its initial and final states, remaining
  regex labels and None-valued cells in the required table shape. Missing
  final state is an error rather than an implicit addition.
- **Immutability / composability:** the source states, transitions, finals
  and alphabet remain unchanged. The fresh Extended result supports the
  existing DFS, accessibility, reachability and language analyses.
- **Tests:** 15 new functions and 33 parametrized cases in
  `tests/fa/test_subautomaton.py` cover full and proper subsets, exact
  states and same-type fresh results, missing/unknown/unhashable states,
  one-pass generators, complete-to-partial DFA, singleton/self-loop,
  filtered NFA destinations and epsilon, GNFA regex/None table and missing
  final, None/heterogeneous states, composition, source immutability and
  the distinction from trim's empty-language convention. The full suite
  has 566 passed, including all 533 prior cases. Strict mypy passes on
  27 source files.
- **Complexity:** conservative O(|Q| + T + V) time for materialization,
  validation, filtering and upstream reconstruction; Q is the source
  state set, T covers examined transition entries, and V includes
  constructor validation and GNFA regex parsing. Memory is proportional
  to requested states, retained transitions and validation temporaries.
- **ADR:** [ADR-0012](decisions/ADR-0012-exact-induced-subautomata.md)
  records exact-set semantics and the distinction from
  [ADR-0007](decisions/ADR-0007-automaton-restriction-policy.md), without
  changing that accepted trim policy.
- **Related requirements:** #20-#62 remain TODO. No completeness test,
  completion operation or other later feature was introduced.
- **Git commit:** pending.
