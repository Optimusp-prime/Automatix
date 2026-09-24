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

Current feature: Level 2 #50 complete and verified

Next planned feature: #51 - Regex -> NFA using Thompson construction (not started)

Current phase: Brzozowski automaton minimization verified

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
| 20 | Test whether an automaton is complete | `is_complete() -> bool` | `CompletenessMixin` via `ExtendedDFA` | VERIFIED | `tests/fa/test_completeness.py` | Checks actual DFA transition totality, independent of `allow_partial`; #21 remains TODO. |
| 21 | Completion | `complete(trap_state=None) -> ExtendedDFA` | `CompletenessMixin` via `ExtendedDFA` | VERIFIED | `tests/fa/test_completeness.py` | Delegates to upstream `to_complete`; fresh ExtendedDFA, optional collision-checked sink, same language. |
| 22 | Complement | `complement(*, retain_names=False, minify=False)` | `ComplementMixin` via `ExtendedDFA` | VERIFIED | `tests/fa/test_complement.py` | Complete then invert finals; default unminimized; minify=True now uses extension #32. |
| 23 | Cartesian product of two automata | `product(other, is_final)` | `ProductMixin` via `ExtendedDFA` | VERIFIED | `tests/fa/test_product.py` | Reachable tuple states only; caller selects finals; equal alphabets; upstream partial-trap convention. |
| 24 | Language inclusion | `is_included_in(other) -> bool` | `InclusionMixin` via `ExtendedDFA` | VERIFIED | `tests/fa/test_inclusion.py` | Tests empty language of self × complement(other); equal alphabets; partial DFA supported. |
| 25 | Language equality | `is_equivalent(other) -> bool` | `InclusionMixin` via `ExtendedDFA` | VERIFIED | `tests/fa/test_inclusion.py` | Mutual language inclusion; same-alphabet policy; no structural comparison. |
| 26 | Automaton isomorphism | `is_isomorphic_to(other) -> bool` | `IsomorphismMixin` via `ExtendedDFA` | VERIFIED | `tests/fa/test_isomorphism.py` | State bijection preserving initial state, finals and labeled transitions, including unreachable states. |
| 27 | Prefix-closed language test | `is_prefix_closed() -> bool` | `PrefixMixin` via `ExtendedDFA` | VERIFIED | `tests/fa/test_prefix.py` | Every useful state must be final; empty language is prefix-closed. |
| 28 | Greatest prefix-closed sublanguage | `prefix_closed_sublanguage() -> ExtendedDFA` | `PrefixMixin` via `ExtendedDFA` | VERIFIED | `tests/fa/test_prefix.py` | Fresh ExtendedDFA with final-to-final edges; states and finals retained. |
| 29 | Distinguishable states | `distinguishable_states() -> set[frozenset[FAStateT]]` | `MinimizationMixin` via `ExtendedDFA` | VERIFIED | `tests/fa/test_minimization.py` | Iterative table filling over all states; partial DFA uses analysis-only completion. |
| 30 | Myhill–Nerode equivalence classes | `equivalence_classes() -> list[frozenset[FAStateT]]` | `MinimizationMixin` via `ExtendedDFA` | VERIFIED | `tests/fa/test_minimization.py` | Partition all states by non-distinguishability, including unreachable states. |
| 31 | Test whether an automaton is minimal | `is_minimal() -> bool` | `MinimizationMixin` via `ExtendedDFA` | VERIFIED | `tests/fa/test_minimization.py` | Accessible states and singleton equivalence classes. |
| 32 | Minimization | `minimize(*, keep_original_names=False) -> ExtendedDFA` | `MinimizationMixin` via `ExtendedDFA` | VERIFIED | `tests/fa/test_minimization.py` | Restrict to accessible states, then quotient by equivalent states; both naming modes. |
| 33 | Test whether an automaton is deterministic | `is_deterministic() -> bool` | DeterminismMixin (DFA/NFA) | VERIFIED | tests/fa/test_determinism.py | No GNFA semantics; partial does not imply nondeterministic |
| 34 | Epsilon closure of a state or set of states | `epsilon_closure(state)`, `epsilon_closure_of_set(states)` | EpsilonMixin (NFA) | VERIFIED | tests/fa/test_epsilon.py | FrozenSet results; epsilon-only traversal; no cache |
| 35 | Determinization | `determinize()`, `to_dfa()` | DeterminizationMixin (NFA) | VERIFIED | tests/fa/test_determinization.py | Reachable frozenset states; omit empty destinations; ExtendedDFA result |
| 36 | Reverse | `reverse() -> ExtendedNFA` | ReverseMixin (DFA/NFA) | VERIFIED | tests/fa/test_reverse.py | Upstream NFA reversal; no GNFA semantics |
| 37 | Epsilon-transition elimination | `remove_epsilon_transitions()`, `eliminate_lambda()` | EliminationMixin (NFA) | VERIFIED | tests/fa/test_elimination.py | Reuses #34; retains all states; alias delegates |
| 38 | Universal-language decision | `is_universal() -> bool` | ComplementMixin (DFA) | VERIFIED | tests/fa/test_universality.py | Complement then emptiness; no minimization |
| 39 | State elimination on a normalized ε-NFA/GNFA-like automaton | inherited `to_regex()` | upstream GNFA via ExtendedGNFA | VERIFIED | tests/fa/test_state_elimination.py | Empty language returns upstream None despite str annotation; no DFA/NFA high-level conversion |
| 40 | DOT export | `dot() -> str` | VisualisationMixin (ExtendedFA) | VERIFIED | tests/fa/test_visualisation.py | Exact mature example; text-only, safe IDs and escaping |
| 41 | SVG/PDF/TikZ export | `graph() -> Source`, `svg()/pdf()/png() -> bytes`, `tikz()/latex() -> str` | VisualisationMixin (ExtendedFA) | VERIFIED | tests/fa/test_visualisation.py | Python graphviz dependency; system dot required only to render; one integration skip locally |

## Level 2

| # | Requirement | Planned public API | Layer / Mixin | Status | Tests | Notes |
| - | ----------- | ------------------ | ------------- | ------ | ----- | ----- |
| 42 | Union | `union(other, *, retain_names=False, minify=False)` (DFA); `union(other)` (NFA) | `DFASetOperationsMixin`, `NFASetOperationsMixin` | VERIFIED | `tests/fa/test_set_operations.py` | DFA reuses lazy product with OR finals; NFA delegates to upstream; Extended results |
| 43 | Intersection | `intersection(other, *, retain_names=False, minify=False)` (DFA); `intersection(other)` (NFA) | `DFASetOperationsMixin`, `NFASetOperationsMixin` | VERIFIED | `tests/fa/test_set_operations.py` | DFA reuses lazy product with AND finals; NFA delegates to upstream; Extended results |
| 44 | Difference | `difference(other, *, retain_names=False, minify=False)` (DFA) | `DFASetOperationsMixin` | VERIFIED | `tests/fa/test_set_operations.py` | Intersection with right complement; DFA-only; Extended result |
| 45 | Concatenation | `concatenation(other: DFA \| NFA) -> ExtendedNFA` | `LanguageOperationsMixin` on ExtendedDFA/ExtendedNFA | VERIFIED | `tests/fa/test_rational_operations.py` | DFA converts via ExtendedNFA.from_dfa; delegates epsilon construction to NFA.concatenate |
| 46 | Kleene star | `kleene_star() -> ExtendedNFA` | `LanguageOperationsMixin` on ExtendedDFA/ExtendedNFA | VERIFIED | `tests/fa/test_rational_operations.py` | DFA converts via ExtendedNFA.from_dfa; delegates new initial/final epsilon construction to NFA.kleene_star |
| 47 | Left quotient | `left_quotient_word(word: str) -> ExtendedDFA/ExtendedNFA` | `DFAQuotientMixin`, `NFAQuotientMixin` | VERIFIED | `tests/fa/test_word_quotient.py` | DFA changes initial state; NFA links a fresh initial state to the post-word epsilon-closed configuration |
| 48 | Right quotient | `right_quotient_word(word: str) -> ExtendedDFA/ExtendedNFA` | `DFAQuotientMixin`, `NFAQuotientMixin`; shared private helper | VERIFIED | `tests/fa/test_word_quotient.py` | Reverse, left quotient by reversed word, reverse; DFA determinizes result |
| 49 | Brzozowski derivatives | `Regex(expression, *, input_symbols=None).derivative(symbol) -> Regex` | `automata_extensions.regex` with private immutable AST | VERIFIED | `tests/regex/test_derivative.py` | Classical grammar only; ADR-0015 |
| 50 | Brzozowski automaton / minimization | `brzozowski_minimize() -> ExtendedDFA` | `BrzozowskiMixin` on ExtendedDFA/ExtendedNFA | VERIFIED | `tests/fa/test_brzozowski.py` | Double reversal/determinization with private reverse-start normalization; ADR-0016 |
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

## #20 - DFA completeness predicate

- **Specification / French meaning:** test whether a deterministic finite
  automaton is complete (automate complet). The professor information came
  from the task prompt; the PDFs were not accessed.
- **DFA-only scope / placement:** `CompletenessMixin` belongs to
  `fa/dfa_mixins/` and is exposed through `ExtendedDFA` only. Its MRO leaves
  `ExtendedNFA` and `ExtendedGNFA` unchanged.
- **Public API / definition:** `is_complete() -> bool` returns True exactly
  when every state has a defined transition for every input symbol. An empty
  alphabet satisfies this condition vacuously. The method reads the
  validated DFA transition table without mutating the automaton.
- **Difference from `allow_partial`:** that constructor option permits
  missing transitions; it does not imply that transitions are missing. A
  DFA with `allow_partial=True` may still be complete.
- **Integration:** an exact induced-subautomaton restriction may delete
  edges and produce a partial DFA. The predicate observes the resulting
  transitions rather than reconstructing or completing the automaton.
- **Tests:** 11 test functions, 13 parametrized cases in
  `tests/fa/test_completeness.py` cover complete and partial tables,
  missing edges on different states, self-loops, empty alphabet,
  `allow_partial` independence, None/heterogeneous states, induced
  restrictions, immutable source, concrete MRO and DFA-only exposure.
  The full suite has 579 passed, including all 566 previous cases;
  strict mypy passes on 30 source files.
- **Complexity:** O(|Q| × |Σ|) worst-case time and O(1) auxiliary space,
  assuming expected constant-time mapping membership. The first missing
  transition may cause an early return.
- **ADR reuse:** [ADR-0003](decisions/ADR-0003-common-extended-fa-layer.md)
  governs common versus specialized mixins;
  [ADR-0012](decisions/ADR-0012-exact-induced-subautomata.md) explains why
  restriction can create a partial DFA. No new ADR is needed.
- **Related requirements:** #21-#62 remain TODO. No completion or
  complement operation was introduced.
- **Git commit:** pending.

## #21 - DFA completion

- **Specification / French meaning:** complete a partial DFA (complétion)
  by adding a nonaccepting sink for missing transitions. The professor
  information came from the task prompt; the PDFs were not accessed.
- **DFA-only scope / public API:** `complete(trap_state=None) -> ExtendedDFA`
  in `CompletenessMixin` through `ExtendedDFA`. The optional argument follows
  automata-lib's `DFA.to_complete` convention: None selects an automatic
  collision-free negative integer; an explicit name is used only if a sink
  is required.
- **Upstream inspection / delegation:** automata-lib 9.2.0 `to_complete`
  checks the actual transition table, copies an already complete DFA, and
  otherwise calls its `_to_complete` constructor with `allow_partial=False`.
  It returns the concrete `Self`, observed as a fresh ExtendedDFA in both
  branches. `complete` delegates directly instead of duplicating that
  reconstruction. The existing upstream `to_complete` API remains intact.
- **Sink and collision policy:** the new state is nonfinal, loops on every
  symbol, and receives every missing transition. Existing edges, alphabet,
  initial state and final states remain unchanged. A requested name already
  in states raises upstream `InvalidStateError` when the sink is needed.
  A complete DFA gains no sink, even when `allow_partial=True`.
- **Language / immutability / composability:** formerly missing transitions
  still reject, so the language is preserved. The source is unchanged and
  the returned ExtendedDFA supports existing extension methods. An induced
  subautomaton that became partial can be completed and then satisfies
  `is_complete()`.
- **Tests:** 11 new functions and 20 parametrized cases in
  `tests/fa/test_completeness.py` cover multiple missing edges and symbols,
  sink self-loops and nonfinality, explicit and automatic sink naming,
  collisions, already complete DFAs, language preservation on nine words,
  empty alphabet, None/heterogeneous states, induced restriction,
  immutability, extension composition, MRO and the mature reference's
  executable completion example. The full suite has 599
  passed, including all 579 prior cases; strict mypy passes on 30 files.
- **Source compatibility:** verified against the documented `complete()`
  example with one state and a missing `b` transition.
- **Complexity:** O(|Q| × |Sigma| + V) worst-case time and
  O(|Q| × |Sigma| + M) auxiliary space, including upstream reconstruction
  and validation costs V and M. The already-complete branch copies the DFA.
- **ADR reuse:** [ADR-0003](decisions/ADR-0003-common-extended-fa-layer.md)
  places DFA-specific behavior, while
  [ADR-0007](decisions/ADR-0007-automaton-restriction-policy.md) and
  [ADR-0012](decisions/ADR-0012-exact-induced-subautomata.md) establish
  fresh same-type transformations and partial results after restriction.
  Upstream sink naming supplies the policy; no new ADR is required.
- **Related requirements:** #22-#62 remain TODO. No complement operation
  or other later feature was introduced.
- **Git commit:** pending.

## #22 - DFA complement

- **Professor specification:** complement a DFA by completing its transition
  function and then exchanging accepting and nonaccepting states. The source
  PDFs were not accessed; the task prompt supplies the professor contract.
- **Mature documentation compatibility / public API:**
  `complement(*, retain_names: bool = False, minify: bool = False)` in
  `ComplementMixin` through `ExtendedDFA` only. The default performs no
  minimization, unlike upstream `DFA.complement(minify=True)`.
  `retain_names` has no effect without minimization.
- **Algorithm / partial DFA:** call `self.complete()` first, then construct
  a fresh ExtendedDFA with the completed states, alphabet, transitions and
  initial state, but with `completed.states - completed.final_states` as
  final states. A sink introduced for a missing edge becomes final, so
  words rejected on that edge are accepted by the complement.
- **Language, type and immutability:** the result is complete, recognizes
  `Sigma*` minus the source language, and remains an ExtendedDFA exposing
  existing extension methods. Neither the source nor the intermediate
  completed DFA is mutated. Double complementation preserves the language.
- **Mature option resolved by #32:** `minify=True` now calls the
  extension's `minimize(keep_original_names=retain_names)` after completion
  and final-state inversion. The default remains `minify=False`.
  automata-lib 9.2.0 `DFA.minify()` remains rejected as a bridge: its
  retained names differ from the mature example, and it raised `KeyError`
  for a valid DFA whose initial state is None during #22 inspection.
- **Source compatibility regression:** a directly derived no-argument
  `d.complement()` case verifies `c1.accepts_input("a") is True` and the
  mature `minify=False` default by retaining an unreachable state. The
  exact mature fixture was not supplied; the test uses a minimal
  equivalent case. The documented `minify=True, retain_names=True` behavior
  is now covered on the shared three-state cycle analogue.
- **Tests:** 15 functions and 29 cases in `tests/fa/test_complement.py`
  cover complete and partial DFA, exact final-state inversion, accepting
  sink, seven representative words, empty word and alphabet, double
  complement, no/all final states, None/heterogeneous states, default
  versus explicit `minify=False`, optional `minify=True`, immutability,
  composition and DFA-only MRO. The full suite has 627 passed, including
  all 599 prior cases at initial #22 validation; #32 later added the named
  minification regression. The current full-suite validation is recorded
  in the #32 Feature note.
- **Complexity:** O(|Q| × |Sigma| + V) worst-case time and
  O(|Q| × |Sigma| + M) auxiliary space, including completion, copying and
  upstream constructor validation costs V and M. Inverting final states
  adds O(|Q|) work. With `minify=True`, the extension's #32 analysis adds
  expected O(|Q|² × |Sigma| + |Q|² × alpha(|Q|) + V) time and
  O(|Q|² × |Sigma| + M) auxiliary space.
- **ADR:** reuses the accepted DFA-specialization and immutable
  reconstruction policies in ADR-0003 and ADR-0007. The #32 integration
  changes no accepted ADR.
- **Related requirements:** #22 remains VERIFIED; the previously deferred
  option is resolved by VERIFIED requirement #32.
- **Git commit:** pending.

## #23 - Lazy synchronized DFA product

- **Professor contract / French meaning:** construct the cartesian product
  (produit cartésien) lazily: states are tuples of component states, and
  only pairs reachable from the pair of initial states are materialized.
  The professor PDFs were not accessed; the task prompt supplies the
  relevant specification and mature reference excerpt.
- **Mature compatibility / public API:** `product(other, is_final)` in
  `ProductMixin` through `ExtendedDFA` only. The callback receives the two
  component states separately and alone decides which reachable pairs
  are final. No implicit AND/OR finality rule is imposed.
- **Lazy construction:** reuse automata-lib 9.2.0 `_cross_product` and
  `_expand_dfa` with `retain_names=True` and `minify=False`. Their BFS
  expands only reachable pairs, preserves tuple names and returns a fresh
  ExtendedDFA; no full `Q1 × Q2` is built. The initial pair is
  `(self.initial_state, other.initial_state)`.
- **Alphabet policy:** require exactly equal `input_symbols` as upstream
  binary DFA operations do; mismatches raise `SymbolMismatchError`.
- **Partial DFA policy:** follow upstream's two-relevant-side product.
  If only one component defines a symbol, the other advances to a
  collision-free implicit trap state. If neither defines it, the product
  transition is absent, so the result can remain partial. Synthetic trap
  components appear only in reachable tuple states. The operands are not
  completed or mutated.
- **Source compatibility regression:** a three-state cycle reproduces
  `sorted(d.product(d, is_final=lambda s1, s2: s1 == s2).states)` as
  `[('0', '0'), ('1', '1'), ('2', '2')]`, with three states instead of all
  nine cartesian pairs. The exact mature fixture was not supplied.
- **Return type / immutability / composition:** the result is ExtendedDFA;
  both operands are unchanged. Existing completeness, reachability and
  complement APIs remain available on it. A raw upstream DFA is also a
  valid second operand.
- **Tests:** 10 new functions and 11 cases in `tests/fa/test_product.py`
  cover initial/tuple states, synchronized edges, lazy omission of
  unreachable pairs, constant and custom finality, cycles/self-loops,
  alphabet mismatch, partial implicit traps, None/heterogeneous states,
  source immutability, composition, DFA-only MRO and the mature example.
  The full suite has 638 passed, including all 627 prior cases; strict
  mypy passes on 34 source files.
- **Complexity:** O(|Q1| + |Q2| + R × |Sigma| + V) expected time and
  O(R × |Sigma| + M) auxiliary space, where R is the number of reachable
  pairs including implicit traps, and V/M cover upstream construction
  and validation. Callback evaluation and state hashing are assumed
  constant-time.
- **ADR:** no new ADR; the partial and alphabet rules follow the inspected
  fixed upstream version and are recorded here for future binary operations.
- **Related requirements:** #24-#62 remain TODO. No inclusion, union,
  intersection or difference operation was implemented.
- **Git commit:** pending.

## #24 - DFA language inclusion

- **Professor contract / mathematical meaning:** `L(self) ⊆ L(other)` iff
  `L(self) ∩ complement(L(other))` is empty. The professor PDFs were not
  accessed; the attached task text supplies the contract.
- **Mature compatibility / public API:** `is_included_in(other) -> bool`
  in DFA-only `InclusionMixin` through `ExtendedDFA`. The source example
  `d.is_included_in(d) is True` has a dedicated regression test using the
  same three-state cycle fixture shape as the product compatibility test.
- **Implementation:** call `other.complement()`, build the lazy product
  using `is_final(left, right)` iff left is final in self and right is
  final in the complement, then return the product's `is_empty()` result.
  No word enumeration or second product algorithm is introduced.
- **Alphabet / partial DFA policy:** differing input alphabets propagate
  `SymbolMismatchError` from product. The right operand's complement
  handles completion before inversion; product handles missing left-side
  transitions according to its established implicit-trap policy.
- **Immutability / type:** the method returns exactly bool and modifies
  neither operand. It accepts an ExtendedDFA as `other` so the project
  complement contract, including its `minify=False` default, is used.
- **Tests:** 10 new cases in `tests/fa/test_inclusion.py` cover source
  compatibility and reflexivity, strict inclusion and reverse failure,
  empty/nonempty languages, a three-symbol counterexample, partial DFAs,
  mismatched alphabets, None/heterogeneous states, composition, immutable
  operands and DFA-only MRO. The full suite has 648 passed, including all
  638 previous cases; strict mypy passes on 36 source files.
- **Complexity:** O((|Q1| + |Q2| + R) × |Sigma| + V) expected time and
  O((|Q2| + R) × |Sigma| + M) auxiliary space, including the right
  complement, reachable product construction and emptiness traversal.
  R counts reachable product pairs; V/M cover upstream validation costs.
- **ADR:** no new ADR; composition uses the accepted completion,
  complement, product and accessibility semantics.
- **Related requirements:** #25-#62 remain TODO. No `is_equivalent`,
  union, intersection or difference API was implemented.
- **Git commit:** pending.

## #25 - DFA language equality

- **Professor contract / mathematical meaning:** two DFA languages are equal
  exactly when each is included in the other. This is language equivalence,
  independent of state names, transition-table shape or unreachable states.
  The professor PDFs were not accessed; the attached task text supplies the
  relevant specification and mature example.
- **Mature compatibility / public API:** `is_equivalent(other) -> bool` in
  DFA-only `InclusionMixin` through `ExtendedDFA`. A source-compatibility
  regression checks `(d.is_included_in(d), d.is_equivalent(d)) == (True, True)`.
- **Implementation:** return `self.is_included_in(other) and
  other.is_included_in(self)`, preserving normal short-circuit evaluation.
  No structural equality check or new product/traversal algorithm is added.
- **Alphabet / partial DFA policy:** both inclusion calls retain #24's
  equal-alphabet requirement (`SymbolMismatchError` on mismatch) and its
  partial-DFA handling. Neither operand is modified.
- **Tests:** nine new cases in `tests/fa/test_inclusion.py` cover reflexivity,
  distinct structures with equal languages, strict one-way inclusion,
  two empty languages, empty versus nonempty, partial DFA, alphabet mismatch,
  None/heterogeneous states, immutability, DFA-only MRO and the supplied
  mature example. The full suite has 657 passed, including all 648 previous
  cases; strict mypy passes on 36 source files.
- **Complexity:** at most two inclusion checks: expected
  O((|Q1| + |Q2| + R) × |Sigma| + V) time and
  O((|Q1| + |Q2| + R) × |Sigma| + M) peak auxiliary space, with R bounding
  reachable product pairs in either direction and V/M covering upstream
  reconstruction and validation. The second check is skipped on first failure.
- **ADR:** no new ADR; reuses the accepted DFA specialization and the
  established complement, product and inclusion policies.
- **Related requirements:** #26-#62 remain TODO. Automaton isomorphism (#26)
  is distinct from language equivalence and was not implemented.
- **Git commit:** pending.

## #26 - DFA isomorphism

- **Professor contract / mathematical meaning:** two DFA are isomorphic iff
  a bijection between all their states preserves the initial state, final
  states and every labeled transition, including whether a transition is
  absent. This compares automaton structure, unlike #25 language equality.
  The professor PDFs were not accessed; the attached task text supplies
  the relevant contract and mature reference excerpt.
- **Mature compatibility / public API:** `is_isomorphic_to(other) -> bool`
  lives in DFA-only `IsomorphismMixin` through `ExtendedDFA`. An explicitly
  renamed three-state cycle provides the mature-example analogue. With
  requirement #32 now implemented, the exact
  `d.is_isomorphic_to(d.minimize(keep_original_names=True))` regression also
  runs on this cycle.
- **Algorithm:** reject differing state counts, alphabets or final-state
  counts; force initial-state correspondence; propagate each mapped state's
  finality, defined symbols and labeled destinations. For remaining
  unreachable components, try injective candidates with matching finality,
  outgoing-symbol sets and self-loop symbols, backtracking on conflict.
  No state names are sorted or compared. Partial DFA are not completed.
- **Input / immutability:** accepts another DFA and returns exactly bool.
  Different alphabets return False because this is a structural predicate.
  Both automata remain unchanged; no cache is added.
- **Tests:** nine new tests in `tests/fa/test_isomorphism.py` cover
  reflexivity, renamed cycles, equal languages with different structures,
  state/final/initial/edge mismatches, alphabet mismatch, partial edges,
  self-loops, unreachable components, None/tuple/heterogeneous states,
  immutability, DFA-only MRO and the source-compatibility analogue. A
  separate development check matched 200 randomly generated three-state
  pairs against exhaustive bijection enumeration. The full suite has
  666 passed, including all 657 previous cases; strict mypy passes on
  38 source files.
- **Complexity:** one mapping propagation is O(|Q| × |Sigma|). The
  backtracking worst case is combinatorial, bounded here by
  O(|Q|! × |Q|² × |Sigma|) time and O(|Q|² + |Q| × |Sigma|) auxiliary
  space. Recursive search remains subject to Python's recursion limit.
- **ADR:** no new ADR; this is a DFA-specific analysis consistent with
  ADR-0003 and does not change an accepted architectural policy.
- **Related requirements:** #27-#62 remain TODO, including #30-#32.
  No prefix or minimization APIs were introduced.
- **Git commit:** pending.

## #27 - Prefix-closed DFA language predicate

- **Professor criterion / mathematical meaning:** a DFA language is
  prefix-closed exactly when every useful state is final. Useful states
  are those on some accepting path; accessible dead states and unreachable
  states do not affect the answer. The professor PDFs were not accessed;
  the attached task text supplies this criterion and the mature excerpt.
- **Mature API / placement:** `is_prefix_closed() -> bool` in DFA-only
  `PrefixMixin` through `ExtendedDFA`. The related
  `prefix_closed_sublanguage()` transformation belongs to #28 and is absent.
- **Implementation:** reuse `useful_states()` and test whether its
  `frozenset` is a subset of `final_states`. No word enumeration, new
  automaton, graph traversal, cache or mutation is introduced.
- **Boundary semantics:** the empty language has no useful states and is
  prefix-closed vacuously. Every nonempty prefix-closed language contains
  epsilon; a useful but nonfinal initial state makes the predicate False.
- **Source compatibility / tests:** a three-state cycle reproduces the
  mature `d.is_prefix_closed() is False` observation on an equivalent
  fixture. Seven tests in `tests/fa/test_prefix.py` cover this, a useful
  nonfinal state, empty language and empty trim representative, epsilon
  only, an accessible nonuseful sink, unreachable nonfinal state, partial
  DFA with a cycle, None/heterogeneous states, exact bool, immutability
  and DFA-only MRO. The full suite has 673 passed, including all 666
  previous cases; strict mypy passes on 40 source files.
- **Complexity:** O(|Q| + T) expected time and O(|Q| + |E|) auxiliary
  space, including both analyses inside `useful_states()` and the final
  O(|Q|) subset test. No result is cached.
- **ADR:** no new ADR; reuses the accepted DFA specialization and
  accessibility analysis policies.
- **Related requirements:** #28-#62 remain TODO. No #28 API was added.
- **Git commit:** pending.

## #28 - Greatest prefix-closed DFA sublanguage

- **Professor specification / mathematical meaning:** return the greatest
  prefix-closed language contained in the source language: a word remains
  exactly when the source accepts it and all its prefixes. The professor
  PDFs were not accessed; the attached task text supplies this contract.
- **Mature compatibility / public API:**
  `prefix_closed_sublanguage() -> ExtendedDFA` is added to the existing
  DFA-only `PrefixMixin`. A source-compatibility analogue verifies
  `(d.is_prefix_closed(), d.prefix_closed_sublanguage().accepts_input(""))`
  is `(False, True)` using a source that accepts epsilon but also accepts
  a word with a rejected prefix. The exact mature fixture was not supplied;
  the #27 three-state cycle cannot reproduce this particular observation
  because its initial state is nonfinal.
- **Transition filtering:** retain `q --a--> r` exactly when both `q` and
  `r` are final. The source must be final because the prefix ending at q
  must be accepted; the destination must be final because the next prefix
  must be accepted. Preserve all states, final states, input symbols and
  initial state, including states made unreachable by filtering.
- **Empty / already closed cases:** a nonfinal initial state has no
  surviving accepted word, so the result is an ordinary valid DFA for the
  empty language, without dropping structural states. A source already
  prefix-closed yields the same language in a fresh object, though some
  irrelevant edges may be removed.
- **Reconstruction / immutability:** build a new `type(self)` DFA from
  filtered transition rows. Set `allow_partial=True` if filtering removes
  required edges; otherwise retain the source setting. Never mutate self,
  call `trim()` or `minimize()`, or complete the filtered result.
- **Tests:** seven new tests in `tests/fa/test_prefix.py` cover the mature
  analogue, all four finality combinations for edges, exact preservation
  of structure other than transitions, good and bad branches, the greatest
  property for every word of length at most four over a two-symbol
  alphabet, empty result, empty source, already closed source, partial DFA,
  cycles, None/heterogeneous states, language inclusion in the source,
  prefix closure, composability and immutability. The full suite has
  680 passed, including all 673 previous cases; strict mypy passes on
  40 source files.
- **Complexity:** O(|Q| + T + V) time and O(|Q| + T_kept + M) auxiliary
  space, where T covers inspected transitions, T_kept the retained table,
  and V/M upstream constructor and validation work/memory.
- **ADR:** no new ADR; follows the accepted immutable ExtendedDFA
  reconstruction policy and does not change ADR-0007.
- **Related requirements:** #29-#62 remain TODO. No distinguishability,
  equivalence-class or minimization API was added.
- **Git commit:** pending.

## #29 - DFA distinguishable states

- **Professor contract / mathematical meaning:** two distinct DFA states
  are distinguishable when some word is accepted from exactly one of them.
  Analyze every original state, including unreachable states. The professor
  PDFs were not accessed; the attached task text supplies the contract.
- **Mature compatibility / public API:**
  `distinguishable_states() -> set[frozenset[FAStateT]]` in DFA-only
  `MinimizationMixin`. Each returned pair is unordered and has exactly two
  distinct original states. A three-state cycle reproduces the mature
  example's exact three-pair result.
- **Algorithm:** private `_distinguishability_table` marks final/nonfinal
  pairs immediately (epsilon witness), then uses a worklist of marked pairs
  and reverse pair-symbol dependencies to propagate distinctions until a
  fixed point. This is iterative table filling, with no state sorting or
  public pair-table API.
- **Partial DFA:** call existing `complete()` only for analysis. Its
  collision-free nonfinal trap represents missing transitions. Filter the
  final set of marked pairs to pairs made solely of original states; the
  trap never appears publicly. Neither source states nor transitions change.
- **Tests:** nine new tests in `tests/fa/test_minimization.py` cover the
  mature example, epsilon marking, one- and two-symbol witnesses, equivalent
  pairs, all/none marked, unreachable states, cycles, partial missing-edge
  semantics, None/heterogeneous states, exact pair shape, immutability and
  DFA-only MRO. An independent development oracle agreed for 150 randomly
  generated four-state partial DFA. The full suite has 689 passed,
  including all 680 previous cases; strict mypy passes on 42 source files.
- **Complexity:** O(|Q|² × |Sigma| + V) expected time and
  O(|Q|² × |Sigma| + M) auxiliary space. Analysis-only completion adds at
  most one state; V/M include its upstream reconstruction and validation.
- **ADR:** no new ADR; reuses the accepted immutable DFA completion policy
  and keeps the table helper private for possible future #30 reuse.
- **Related requirements:** #30-#62 remain TODO. No public equivalence
  classes, minimality test or minimization method was added.
- **Git commit:** pending.

## #30 - Myhill-Nerode equivalence classes

- **Professor specification / mathematical meaning:** partition every DFA
  state, including unreachable states, by indistinguishability: two states
  share a class exactly when no future word gives different acceptance
  outcomes. The professor PDFs were not accessed; the attached task text
  supplies the specification and mature example.
- **Mature compatibility / public API:** `equivalence_classes() ->
  list[frozenset[FAStateT]]` in the existing DFA-only `MinimizationMixin`.
  The returned list has no meaningful order and states are never sorted.
  The three-state cycle reproduces the mature three-singleton example
  when classes are compared without ordering.
- **Relation to #29 / construction:** call `distinguishable_states()` once;
  examine each unordered pair of original states and union those not marked
  distinguishable. Union-find with path compression and rank groups each
  state into exactly one nonempty immutable class. No table filling is
  duplicated and no states are merged in the source automaton.
- **Partial DFA / immutability:** #29 already interprets missing transitions
  through an analysis-only implicit trap; #30 consumes its resulting
  relation without completing again. The source remains unchanged.
- **Tests:** seven new tests in `tests/fa/test_minimization.py` cover the
  mature example, all-singleton and all-in-one partitions, mixed classes,
  disjointness and coverage, pairwise equivalence with #29, unreachable
  states, partial DFA with two missing transitions, None/heterogeneous
  states and immutability. The full suite has 696 passed, including all
  689 previous cases; strict mypy passes on 42 source files.
- **Complexity:** O(|Q|² × |Sigma| + |Q|² × alpha(|Q|) + V) expected time
  and O(|Q|² × |Sigma| + M) auxiliary space. V/M include #29's
  analysis-only completion and upstream validation; union-find examines
  O(|Q|²) pairs with inverse-Ackermann amortized operations.
- **ADR:** no new ADR; the method composes #29 with a local partition
  structure and changes no accepted architectural policy.
- **Related requirements:** #31-#62 remain TODO. No `is_minimal()` or
  extension `minimize()` was added.
- **Git commit:** pending.

## #31 - DFA minimality predicate

- **Professor criterion / mature clarification:** a DFA is minimal exactly
  when every state is accessible and every Myhill–Nerode class is a
  singleton. The accessibility condition excludes unreachable states even
  when all states are pairwise distinguishable. The professor PDFs were not
  accessed; the attached task text supplies the contract and reference.
- **Public API / implementation:** `is_minimal() -> bool` in the existing
  DFA-only `MinimizationMixin`. It compares `accessible_states()` with
  `states` and checks the sizes of `equivalence_classes()`. It does not
  call `minimize()`, mutate the source or add a cache.
- **Source compatibility / tests:** the three-state mature cycle returns
  True. Tests also cover an inaccessible state with singleton classes,
  equivalent accessible states, a minimal partial DFA and exact bool.
  The full suite has 706 passed; strict mypy passes on 42 source files.
- **Complexity:** O(|Q| + T + |Q|² × |Sigma| + |Q|² × alpha(|Q|) + V)
  expected time and O(|Q|² × |Sigma| + |Q| + |E| + M) auxiliary space,
  including delegated accessibility and #30 class computation.
- **ADR:** reuses accepted accessibility and partition decisions; no new
  minimality-specific architectural decision.
- **Related requirements:** #32 was implemented in the same authorized
  pass; #33-#62 remain TODO.
- **Git commit:** pending.

## #32 - DFA minimization

- **Professor contract / mature API:** `minimize(*,
  keep_original_names=False) -> ExtendedDFA` in `MinimizationMixin`.
  Remove unreachable states, merge equivalent accessible states and return
  a fresh language-equivalent minimal DFA. This is the extension API,
  independent of upstream `DFA.minify()`, whose naming and None-state
  behavior were unsuitable during #22 inspection.
- **Accessible quotient:** call `accessible_states()`, then
  `induced_subautomaton(accessible)` and `equivalence_classes()` on that
  restricted automaton. Build a state-to-class map, quotient transitions,
  initial class and final classes. All original-state classes in the
  quotient are reachable; no analysis-only trap is exported.
- **Naming modes:** by default, each state name is the class itself as a
  frozenset. With `keep_original_names=True`, use a member of each class,
  preferring the original initial state for its class; no states are sorted
  or assumed comparable. Both modes return a new ExtendedDFA even when
  the source is already minimal.
- **Partial DFA policy:** defined edges from equivalent class members are
  combined by symbol, while symbols undefined for every member remain
  absent. This preserves language and quotient reachability in cases where
  one member lacks an edge and another leads to an empty-language class.
  Set `allow_partial` appropriately; never expose the temporary trap from
  #29. [ADR-0013](decisions/ADR-0013-partial-dfa-quotient-transitions.md)
  records the durable policy.
- **Language / immutability:** representative cases satisfy
  `source.is_equivalent(source.minimize())` and the named variant;
  both results satisfy `is_minimal()`. States, transitions and finals of
  the source remain unchanged. Tests also check quotient initial/final
  classes, exact transitions and extension composability.
- **Source compatibility / cross-feature regressions:** the mature
  three-state cycle returns three singleton frozensets by default and
  `['0', '1', '2']` with original names, with `is_minimal() is True`.
  The exact #26 `d.is_isomorphic_to(d.minimize(keep_original_names=True))`
  regression now passes. #22 `complement(minify=True,
  retain_names=True)` now uses extension minimization and reproduces the
  named three-state result; its default remains unminimized.
- **Tests:** eight new tests in `tests/fa/test_minimization.py` plus the
  #22 and #26 regressions cover merging, inaccessible removal, both names,
  complete/partial DFA, different missing edges, None/heterogeneous states,
  language preservation, minimality, immutability and source examples.
  An additional development check minimized 150 random four-state partial
  DFA equivalently in both modes, with all results minimal. The full suite
  has 706 passed, including all 696 prior cases; strict mypy passes on
  42 source files.
- **Complexity:** O(|Q| + T + |R|² × |Sigma| +
  |R|² × alpha(|R|) + V) expected time and
  O(|R|² × |Sigma| + |Q| + |E| + M) auxiliary space. R is the accessible
  state set; V/M cover restrictions, quotient construction and validation.
- **Related requirements:** #33-#62 remain TODO. No NFA determinization
  or other future algorithm was added.
- **Git commit:** pending.

## #33 - Determinism predicate

- **Professor definition / mature API:** `is_deterministic() -> bool`
  checks uniqueness of symbol targets and absence of epsilon transitions.
  Deterministic does not mean complete: every valid DFA, including a
  partial DFA, returns True. The supplied excerpts are the source;
  the professor PDFs and full mature documentation were not accessed.
- **Placement / DFA and NFA:** `fa/fa_mixins/determinism.py` contains
  `DeterminismMixin`, attached to ExtendedDFA and ExtendedNFA. The DFA
  branch relies on constructor guarantees. The NFA branch inspects every
  stored symbol/destination-set entry, including inaccessible states:
  a nonempty epsilon target set or more than one target returns False.
  Empty target sets represent no actual edge, even under an epsilon key.
- **GNFA policy:** the mixin is not attached to ExtendedFA or ExtendedGNFA.
  No determinism semantics for regex labels is invented; GNFA has no new
  `is_deterministic` API. DFA/NFA use the same public method without
  changing existing graph conventions or prior requirements.
- **Upstream / ADR reuse:** inspected automata-lib 9.2.0 DFA/NFA transition
  representations and checked for name collisions (none). Placement follows
  ADR-0002/0003 specialization rules; no new durable policy needs an ADR.
- **Tests / source compatibility:** 13 cases in
  `tests/fa/test_determinism.py`: complete/partial DFA, single/multiple NFA
  targets, epsilon edges, empty rows/targets, inaccessible nondeterminism,
  None and heterogeneous states, frozenset-valued DFA states, exact bool,
  source/cache immutability, MRO and GNFA scope. The mature call
  `d.is_deterministic() is True` is a named source-compatibility regression.
- **Complexity:** DFA O(1) time; NFA O(T) time, where T includes stored
  source rows and symbol entries; O(1) auxiliary space. No graph or cache.
- **Validation:** all 757 tests pass, including #1-#32; strict mypy passes
  on 49 source files. Requirements #36-#62 remain TODO.
- **Git commit:** pending.

## #34 - Epsilon closure of a state or state set

- **Professor specification / French meaning:** epsilon-closure
  (epsilon-fermeture) follows only transitions labeled `""`, with the
  starting states included by zero-length paths. Consuming edges are ignored.
- **Mature APIs / placement:** NFA-only `EpsilonMixin` in
  `fa/nfa_mixins/epsilon.py` exposes
  `epsilon_closure(state: FAStateT) -> FrozenSet[FAStateT]` and
  `epsilon_closure_of_set(states: Iterable[FAStateT]) -> FrozenSet[FAStateT]`.
- **Implementation:** the single-state API delegates to the set API with
  one seed. Validate seeds while consuming the iterable once, then perform
  an iterative multi-source epsilon traversal. Mark each state when queued
  to terminate on cycles. Absent source rows mean no outgoing edges, as
  allowed by upstream NFA. Empty input returns an empty frozenset.
- **Invalid states:** an absent or unhashable seed raises upstream
  `InvalidStateError`, following ADR-0004. Explicit None is an ordinary
  state when present. No new sentinel or exception hierarchy is introduced.
- **Upstream / reuse:** inspected NFA's cached `_get_lambda_closures` and
  transition validation. The requested traversal is implemented without its
  global cache or NetworkX dependency, and is reused by #35. No source
  mutation or persistent state is added. ADR-0002/0003/0004 remain unchanged.
- **Tests / source compatibility:** 21 cases in `tests/fa/test_epsilon.py`
  cover zero-edge closure, chain, cycle, branching, ignored consuming edges,
  multi-source union, empty input, duplicates, a single-use generator,
  absent/unhashable seeds, None/heterogeneous states, immutable results and
  source/cache immutability. A minimal fixture reproduces the supplied
  `(sorted(n.epsilon_closure("p")),
  sorted(n.epsilon_closure_of_set({"p"}))) == (["p", "r"], ["p", "r"])`
  example; the unavailable original fixture is not claimed to be reproduced.
- **Complexity:** O(k + |Q_e| + |E_e|) time and O(|Q_e|) space, where k is
  the number of input items and Q_e/E_e the reached epsilon subgraph.
  Single-state closure has k=1. Expected constant-time hashing/lookups.
- **Validation:** all 757 tests pass; strict mypy passes on 49 source files.
  No epsilon elimination (#37) or other future API is implemented.
- **Git commit:** pending.

## #35 - NFA determinization

- **Professor contract / mature APIs:** construct only accessible subsets.
  NFA-only `DeterminizationMixin` in `fa/nfa_mixins/determinization.py`
  exposes `determinize() -> ExtendedDFA`; `to_dfa() -> ExtendedDFA` simply
  delegates to it. No duplicate algorithm, minimization or state renaming.
- **Initial / transition / final subsets:** begin with #34's epsilon
  closure of the original initial state. For each discovered subset S and
  alphabet symbol a, compute the union of direct a-destinations and call
  `epsilon_closure_of_set` on that move. A subset is final iff it intersects
  the original final states. The alphabet is preserved; epsilon is not a
  consumed input symbol.
- **Lazy construction:** a queue processes each discovered subset once.
  Transition rows also identify discovered subsets. The full powerset is
  never enumerated, and inaccessible original states cannot appear.
  Every result state is a frozenset of original states, with None and
  heterogeneous values retained without sorting or string conversion.
- **Empty-subset policy / upstream inspection:** inspected and exercised
  automata-lib 9.2.0 `DFA.from_nfa`, `_expand_dfa` and NFA's
  `_iterate_through_symbol_path_pairs`. They omit empty destinations.
  Follow that convention: omit the corresponding DFA edge and do not create
  an empty-subset sink; set `allow_partial` from the actual resulting table.
  With no accepting path the nonempty initial subset still represents a
  valid empty-language DFA. An empty alphabet yields a complete DFA by
  vacuity. A test compares the structure with upstream using
  `retain_names=True, minify=False`.
- **Why not delegate conversion:** the task explicitly requests visible
  pedagogical subset construction reusing the new #34 operations. Upstream
  uses cached closures and defaults to renaming/minimizing; those defaults
  are not the supplied mature contract. No upstream source is changed.
- **Result / immutability / composition:** a fresh ExtendedDFA retains
  `is_deterministic`, `complete`, `trim`, `minimize` and equivalence APIs.
  No source states, transitions, final states or caches are modified.
  The known upstream NFA word-reading limitation for None (ADR-0007) is
  not patched; structural tests cover None and the produced DFA is readable.
- **Tests / source compatibility:** 17 cases in
  `tests/fa/test_determinization.py` cover deterministic and branching NFAs,
  epsilon before/after consumption, epsilon cycles, empty-word acceptance,
  multiple finals, exact reachable subsets/edges, no implicit minimization,
  empty alphabet/language, partial output, immutability, None/heterogeneous
  states, types, MRO and composition. All words of lengths 0-4 over {a,b}
  are compared against the branching epsilon NFA. The supplied mature
  `(n.determinize().accepts_input("a"), n.to_dfa().accepts_input("a"))`
  returns `(True, True)` on a minimal compatible fixture; both outputs
  are also checked language-equivalent.
- **Complexity:** let n=|Q|, s=|Sigma|, R be discovered subsets, M the
  maximum total destinations inspected for one symbol over Q, e all epsilon
  edges, and V constructor freezing/validation. Time is
  O(n + e + R*s*(n + M + e) + V). Peak space is
  O(R*n*(1+s) + n + V_space), including freshly allocated target frozensets
  on transitions; equal subsets need not share object identity. R can reach
  2^n, so worst-case determinization is exponential, not polynomial in n.
- **ADR / validation:** reuses ADR-0002/0003 specialization and immutable
  transformation principles; no accepted ADR is modified or new one needed.
  All 757 tests pass, including the #22 `complement(minify=True)` regression;
  strict mypy passes on 49 source files. #36-#62 remain TODO.
- **Git commit:** pending.

## #36 - Language reversal

- **Professor definition / mature API:** `reverse() -> ExtendedNFA`
  recognizes the mirror language: w is accepted by the source exactly when
  reversed(w) is accepted by the result. Reverse edges and exchange the roles
  of initial/final states. The supplied mature excerpt names `ReverseMixin`;
  no unavailable PDF or full reference document was accessed.
- **Placement / scope:** `fa/fa_mixins/reverse.py` supplies one shared
  `ReverseMixin` attached specifically to ExtendedDFA and ExtendedNFA.
  ExtendedGNFA receives no reverse method: regex-label reversal has no
  supplied contract and is not approximated by reversing graph edges.
- **Upstream inspection / delegation:** automata-lib 9.2.0 has no DFA.reverse.
  For a DFA, `ExtendedNFA.from_dfa` preserves the graph with singleton
  destination sets; then call `NFA.reverse` explicitly. For an ExtendedNFA,
  call that upstream method directly, bypassing recursive wrapper dispatch.
  Upstream uses `self.__class__` to construct the result, preserving
  ExtendedNFA and its extension methods without ad-hoc representations.
- **Structural convention:** upstream reverses all actual edges with their
  labels, including epsilon, and always adds a fresh initial state. Its
  epsilon targets are the old final states (possibly none); the old initial
  is the sole new final. `FA._add_new_state` chooses the first unused
  nonnegative integer, respecting ordinary set membership/collisions. The
  alphabet and all original states are preserved, including None and
  heterogeneous states. No source mutation or cache is introduced.
- **Known limitation:** reversal itself supports None. Upstream NFA word
  reading still rejects None through NetworkX, as recorded in ADR-0007;
  structural tests and subsequent extension determinization cover that case.
  No upstream simulation patch is introduced.
- **Tests / source compatibility:** 22 cases in `tests/fa/test_reverse.py`
  cover ab/ba, rejection, palindromes, empty words/alphabets, zero/multiple
  finals, nondeterminism, reversed epsilon edges, cycles/self-loops,
  collision-free initial naming, None/heterogeneous states, immutability,
  ExtendedNFA result, double reversal and determinization composition.
  All words of lengths 0-4 over {a,b} validate mirror/double-mirror semantics
  on DFA/NFA fixtures. A three-state cycle consistent with the supplied
  mature example checks `d.reverse().accepts_input("aaa") is True`.
- **Complexity:** O(|Q| + T + V) time and O(|Q| + |E| + V_space) peak
  space. T includes stored rows, symbol entries and examined destinations;
  E is actual edges. V/V_space include freezing/validation and the optional
  DFA-to-NFA construction, with expected constant-time state hashing.
- **ADR / validation:** reuses ADR-0002 delegation, ADR-0003 specialization
  and ADR-0007's existing None limitation. No accepted ADR is modified or
  new ADR needed. All 803 tests pass; strict mypy passes on 54 source files.
- **Git commit:** pending.

## #37 - Epsilon-transition elimination

- **Professor specification / mature API:** propagation through epsilon
  closures produces an equivalent NFA without any `""` transition key.
  `EliminationMixin` in `fa/nfa_mixins/elimination.py` exposes
  `remove_epsilon_transitions() -> Self` on ExtendedNFA, returning a new
  ExtendedNFA (or the same concrete subclass). This is epsilon suppression,
  not determinization, trimming or minimization.
- **Reuse / transition rule:** for each q, call #34 `epsilon_closure(q)`
  once. For each input symbol, union direct destinations from that closure
  and call #34 `epsilon_closure_of_set(move)` for the new target set.
  Do not duplicate epsilon traversal or populate a persistent cache.
  Empty destination sets are omitted; no epsilon key is constructed.
- **Final-state propagation:** q is final iff its original epsilon closure
  meets the old final set. This preserves acceptance of the empty word,
  including through epsilon chains and cycles.
- **State preservation / immutability:** retain exactly all source states,
  input symbols and initial state, including inaccessible or useless states.
  Build a new transition table and final set; never mutate the source.
  None and heterogeneous states are supported by the extension closures.
- **eliminate_lambda compatibility:** upstream's inspected signature is
  `eliminate_lambda(self) -> Self`, so the mixin intentionally overrides it
  with the same signature and a one-line delegation to
  `remove_epsilon_transitions()`. This is the supplied mature compatibility
  alias, not another professor requirement. No upstream algorithm is copied.
- **Upstream findings:** direct `NFA.eliminate_lambda` on the current
  ExtendedNFA works for the inspected string-state example, but removes
  unreachable states, contrary to #37's state-preservation contract. With a
  None state it raises `ValueError: None cannot be a node` through cached
  NetworkX closures. Thus the supplied historical warning is not claimed
  to be a universal failure in this hierarchy; concrete differences justify
  using #34 instead. Upstream source and private methods remain untouched.
- **Tests / source compatibility:** 13 cases in
  `tests/fa/test_elimination.py` cover no epsilon, epsilon before/after
  consumption, chains/cycles/branching, propagated finals and empty-word
  acceptance, no epsilon keys, preserved states/alphabet/initial, None,
  heterogeneous states, immutable source/cache, type and alias MRO.
  All words of lengths 0-4 over {a,b} agree before/after elimination;
  `remove_epsilon_transitions().determinize()` is equivalent to
  `determinize()`. A minimal compatible fixture verifies the supplied
  `n.remove_epsilon_transitions().accepts_input("a") is True` and the alias.
- **Complexity:** for n=|Q|, s=|Sigma|, e epsilon edges and M the maximum
  total destinations for one symbol over Q, time is
  O(n*(n+e) + n*s*(n+M+e) + V). Closures are recomputed per source/move;
  no optimistic linear bound or persistent cache is claimed. Peak space
  is O(n + n*n*s + V_space), including the potentially dense result and
  constructor freezing/validation V/V_space.
- **ADR / validation:** reuses the accepted immutable transformation and
  NFA specialization rules (ADR-0002/0003), and #34's closure contract.
  No accepted ADR is changed. All 803 tests pass, including #34/#35 and
  #22 optional minimization; strict mypy passes on 54 source files.
- **Git commit:** pending.

## #38 - Universal-language decision

- **Professor criterion / mature API:** `is_universal() -> bool` means
  L(A)=Sigma*. The implementation follows the required complement-then-empty
  criterion exactly, in the existing DFA-only `ComplementMixin`.
- **Implementation / dependencies:** `return self.complement().is_empty()`
  reuses #22 and #13. The default `minify=False` avoids unnecessary
  minimization. No separate reachability or word-enumeration algorithm,
  source mutation or cache is introduced. NFA/GNFA receive no such API.
- **Partial DFA semantics:** completion before complement correctly accounts
  for missing transitions. A reachable missing edge can disprove universality
  even if all original states are final; missing edges only in unreachable
  components need not do so. No special partial-DFA branch is needed here.
  For an empty alphabet, Sigma* contains epsilon, so universality holds
  exactly when the initial state is final; the empty language is not universal.
- **Tests / source compatibility:** 11 cases in
  `tests/fa/test_universality.py` cover universal/nonuniversal/empty languages,
  one/multiple/zero symbols, partial transitions, inaccessible nonfinal states,
  None/heterogeneous states, exact bool, source/cache immutability and DFA-only
  placement. Tests verify equality with `complement().is_empty()` and prohibit
  minimization during the predicate. A compatible three-state cycle reproduces
  the mature `d.is_universal() is False` example.
- **Complexity:** O(n + (n+1)*|Sigma| + V) time and
  O(n + (n+1)*|Sigma| + V_space) peak space, including completion/inversion,
  freezing/validation and accessibility on the completed DFA with at most
  n+1 states. No minimization cost is incurred.
- **ADR / validation:** reuses existing complement, accessibility and
  immutable-construction decisions; no new ADR. All 803 tests pass,
  including #1-#35; strict mypy passes on 54 source files. Imports, MRO and
  upstream constructors remain valid; reference/automata-lib is unchanged.
  Requirements #39-#62 remain TODO; no Brzozowski minimization or future API
  is introduced.
- **Git commit:** pending.

## #39 - State elimination on normalized epsilon-NFA/GNFA structure

- **Professor specification / placement:** eliminate intermediate states of
  the normalized GNFA representation. This low-level operation is already
  `automata.fa.gnfa.GNFA.to_regex()`, inherited intact by ExtendedGNFA.
  Requirement #53 remains the separate high-level DFA-to-regex conversion;
  no new DFA/NFA `to_regex()` API is introduced here.
- **Upstream inspection / delegation:** automata-lib 9.2.0 `GNFA.from_dfa`
  creates distinct structural initial/final states and regex/None cells;
  its `to_regex()` copies states and transition rows locally, then eliminates
  intermediate states. `ExtendedGNFA.from_dfa(d)` returns ExtendedGNFA.
  Existing inheritance provides a sufficient wrapper through the extension
  type, so no redundant elimination algorithm or public override was added.
- **Output and limitation:** nonempty-language examples return regex strings;
  direct epsilon returns `""`. Upstream returns `None` for a GNFA with no
  initial-to-final path, despite annotating `to_regex()` as `str`. This
  observed upstream convention is documented rather than silently mapped to
  epsilon or changed by a global compatibility patch. The source remains
  unchanged.
- **Tests / source compatibility:** nine tests in
  `tests/fa/test_state_elimination.py` cover direct paths, union, star,
  epsilon, empty language, multiple intermediates, None/heterogeneous
  states, immutability and inherited method identity. The transition table
  supplied for the mature DOT example yields the exact mature regex:
  `GNFA.from_dfa(d).to_regex() == '(ab*ab*a|b)*'`; the ExtendedGNFA variant
  matches. Upstream `NFA.from_regex` checks representative accepted words.
- **Complexity:** for k intermediate states, upstream performs k elimination
  steps and up to O(k²) pair updates at each step, hence O(k³) structural
  updates. Regex concatenation/copying can grow very large; total runtime
  and space depend on the lengths of intermediate expressions, potentially
  exponential in k. The inherited extension adds no algorithmic overhead.
- **ADR / validation:** reuses ADR-0002 upstream delegation and ADR-0003
  concrete specialization; no new decision for #39. All 826 runnable tests
  pass, with one separate renderer integration test skipped. Strict mypy
  passes on 56 source files. Git commit: pending.

## #40 - Graphviz DOT export

- **Professor specification / mature API:** `dot() -> str` produces plain
  Graphviz source on ExtendedDFA, ExtendedNFA and ExtendedGNFA through the
  existing common `VisualisationMixin`. It launches no renderer and works
  without the Python graphviz package or system `dot` binary.
- **Shared graph / IDs:** a fresh private immutable description uses
  `iter_transitions()` and the original state/final sets. The initial state
  gets `s0`; remaining states use safe IDs by type/repr order, avoiding
  direct comparisons of heterogeneous state objects. True state values are
  labels. Edges are grouped by this node order and otherwise retain the
  upstream iteration order for a given automaton. NFA epsilon and GNFA empty
  regex labels display ε; GNFA None cells do not create edges.
- **DOT semantics / escaping:** invisible `__start__` pointer, LR layout,
  double circles for finals, circles otherwise. Quotes, backslashes,
  newlines and tabs are escaped in labels; DOT keywords are quoted when used
  as labels. Partial DFA, self-loops, multiple NFA targets, regex GNFA edges,
  None, integers, tuples and heterogeneous states are covered.
- **Exact source compatibility:** the verified three-state fixture yields
  exactly the supplied mature `d.dot().splitlines()` list, including node
  numbering and transition order. Tests prove stable repeated output and
  that text generation invokes no external renderer.
- **Complexity:** O(|Q| log |Q| + T + C) time and
  O(|Q| + |E| + C) space, treating ordering-key comparisons as constant
  cost; long representations add comparison cost. T scans upstream
  transitions; E counts emitted actual edges and C label/output characters.
  No cache or source mutation.
- **Architecture / tests:** `tests/fa/test_visualisation.py` shares 15
  test cases with #41. [ADR-0014](decisions/ADR-0014-shared-visualization-source.md)
  records the common model and renderer boundary. All 826 runnable tests
  pass; strict mypy passes on 56 source files. Git commit: pending.

## #41 - SVG, PDF, PNG, TikZ and LaTeX export

- **Professor / mature contract:** SVG/PDF/TikZ export is provided by the
  same `VisualisationMixin`. Thin mature compatibility helpers add
  `graph() -> graphviz.Source`, `png() -> bytes` and `latex() -> str`.
  `svg()` and `pdf()` each return `bytes`; `tikz()` returns `str`.
- **Graphviz path:** `graph()` constructs `Source(self.dot())` exactly.
  `svg()/pdf()/png()` call `graph().pipe(format=...)`, returning output in
  memory without file side effects. The Python dependency
  `graphviz>=0.21,<1` is declared in `pyproject.toml`; editable install was
  verified. The system `dot` executable is required only for binary
  rendering. Missing/failed renderers propagate the package's clear
  `ExecutableNotFound`/`CalledProcessError` rather than returning bad data.
  No executable path is hardcoded.
- **TikZ/LaTeX path:** TikZ uses the same private state/edge description as
  DOT, directly in Python. It marks initial and accepting nodes, loops and
  epsilon edges and escapes LaTeX special characters. `latex()` wraps that
  text in a standalone document loading TikZ's automata library. Neither
  textual exporter starts Graphviz or writes a file. Literal alphabet symbol
  `ε` remains distinct from an actual empty-string epsilon edge in TikZ.
- **GNFA policy:** render actual regex labels as edge text, render empty
  string labels as ε, and omit absent None cells. No regex evaluation or
  word-reading behavior is introduced.
- **Tests / source compatibility:** the 15 visualization tests cover
  `len(d.tikz()) > 0`, `len(d.latex()) > 0`, exact `graph().source == dot()`,
  format-specific `Source.pipe` delegation, returned bytes, no output files,
  missing-binary error, shared DFA/NFA/GNFA behavior, labels/escaping,
  immutability, imports and MRO. The real SVG/PDF/PNG integration test now
  runs with Graphviz 14.1.2 (`dot.exe`) and Python graphviz 0.21 in
  `automate-env-clean`; pytest: 827 passed. Manual ExtendedDFA checks
  confirmed valid SVG and PNG bytes, PDF bytes beginning `%PDF-1.7`, and
  successful opening of SVG and PDF files written from those bytes.
  MiKTeX/pdflatex and PGF/TikZ were also verified by compiling and viewing
  a TikZ test PDF. MiKTeX is needed to compile the generated text, not to
  call `tikz()` or `latex()`.
- **Typing / complexity / ADR:** graphviz 0.21 lacks a `py.typed` marker,
  so a narrow local stub in `typings/graphviz` types exactly the Source API
  used; strict mypy passes on 56 source files. DOT/TikZ generation has
  #40's ordering/scan/label cost; binary rendering adds Graphviz's own
  layout cost plus output-size memory. See [ADR-0014](decisions/ADR-0014-shared-visualization-source.md).
  No source mutation, cache or hardcoded system path. Git commit: pending.

**Level 1 completion:** every requirement #1-#41 is VERIFIED; #42-#62
remain TODO. Validation: 826 passed, one renderer integration skip, strict
mypy on 56 source files, `git diff --check` clean, editable install and public
imports/MRO verified. `reference/automata-lib` remains unchanged.

## #42 - Union of automaton languages

- **Professor specification / meaning:** construct an automaton for
  `L(self) ∪ L(other)` using a product or a fresh initial state. The source
  PDFs were not accessed; the attached task supplies the specification.
- **Mature compatibility:** the DFA source example
  `d.union(d).accepts_input("aaa") is True` is reproduced with a three-state
  cycle accepting `"aaa"`. The mature extension distinguishes DFA product
  union from generic NFA rational union.
- **Public API / placement / result:** DFA
  `union(other, *, retain_names=False, minify=False)` in
  `DFASetOperationsMixin` returns `ExtendedDFA`. NFA `union(other)` in
  `NFASetOperationsMixin` returns `ExtendedNFA`. Optional DFA keyword names
  preserve upstream override compatibility; the default never minimizes.
  Explicit `minify=True` uses already-verified extension requirement #32.
- **Construction / alphabets:** DFA delegates to #23 `product()` with OR
  finality, retaining only reachable pairs and its implicit-trap behavior
  for partial operands. DFA alphabets must match; mismatch raises
  `SymbolMismatchError`. NFA wraps upstream 9.2.0 `NFA.union`, which adds
  an epsilon-branching initial state and uses the union of alphabets. Its
  `self.__class__` reconstruction retains the ExtendedNFA type. Neither
  operand changes; no second product engine or determinization is added.
- **Tests / complexity / limits:** `tests/fa/test_set_operations.py` covers
  source compatibility, all acceptance combinations, partial DFA, epsilon,
  mismatched alphabets, unreachable pairs, return types, immutability and
  composition. DFA has expected O(|Q1| + |Q2| + R × |Sigma| + V) time and
  O(R × |Sigma| + M) space, with R reachable pairs and V/M upstream
  construction/validation. NFA union copies states and edges in
  O(|Q1| + |Q2| + T1 + T2 + V) time and corresponding space. Explicit
  minimization adds #32's cost. GNFA union is outside this requirement's
  supported scope. Reuses ADR-0002 and the accepted #23 product policy;
  no new ADR. Git commit: pending.

## #43 - Intersection of automaton languages

- **Professor specification / meaning:** synchronized Cartesian product
  accepting exactly `L(self) ∩ L(other)`. The source PDFs were not accessed.
- **Mature compatibility:** the exact DFA source assertion
  `d.intersection(d) == d` passes; automata-lib 9.2.0 DFA equality compares
  languages, so reachable tuple states do not contradict it. The supplied
  regex NFA example also passes:
  `n1.intersection(n2).accepts_input("ab") is False` for
  `(a|b)*a` and `(a|b)*b`.
- **Public API / placement / result:** DFA
  `intersection(other, *, retain_names=False, minify=False)` in
  `DFASetOperationsMixin` returns `ExtendedDFA`. NFA `intersection(other)`
  in `NFASetOperationsMixin` returns `ExtendedNFA`. The DFA default is
  unminimized; explicit minimization reuses #32.
- **Construction / alphabets:** DFA reuses #23 `product()` with AND finality,
  preserving its equal-alphabet `SymbolMismatchError` and partial-DFA
  implicit-trap policy. NFA delegates to upstream 9.2.0
  `NFA.intersection`: reachable pairs synchronize symbol edges and allow
  epsilon moves in either component; the output alphabet is the union of
  operand alphabets. Neither operand changes.
- **Tests / complexity / limits:** the same focused file tests all four
  acceptance combinations, partial DFA, epsilon NFA, alphabet policies,
  exact return types, immutability and mature examples. DFA cost is
  O(|Q1| + |Q2| + R × |Sigma| + V) expected time and
  O(R × |Sigma| + M) space. NFA cost is O(R × |Sigma1 ∪ Sigma2| + G + V)
  time and O(R + G + M) space, with G generated edges. V/M include upstream
  construction and validation. GNFA intersection is not added. Reuses
  ADR-0002 and #23; no new ADR. Git commit: pending.

## #44 - Difference of DFA languages

- **Professor specification / meaning:** construct `L(self) - L(other)`
  by intersection with the complement of the right operand. The source
  PDFs were not accessed.
- **Mature compatibility:** the exact assertion
  `d.difference(d).is_empty() is True` has a regression test.
- **Public API / placement / result:**
  `difference(other, *, retain_names=False, minify=False)` in the DFA-only
  `DFASetOperationsMixin` returns a fresh `ExtendedDFA`. The default does
  not minimize; optional explicit minimization uses #32.
- **Construction / alphabets:** call `other.complement(minify=False)`, then
  the extension `self.intersection(...)`. For an ExtendedDFA right operand
  this is verified #22 completion then final inversion; for an upstream
  DFA operand its 9.2.0 complement is invoked with minimization disabled.
  The subsequent product enforces the existing equal-alphabet
  `SymbolMismatchError` and handles a partial left operand. No independent
  difference product or hidden NFA determinization is introduced.
- **Tests / complexity / limits:** tests cover the source example, each
  acceptance combination, `A - A`, subtraction of an empty language,
  partial transitions, alphabet mismatch, ExtendedDFA type, immutability,
  and composition. Expected time is
  O(|Q2| × |Sigma| + |Q1| + R × |Sigma| + V), with space
  O((|Q2| + R) × |Sigma| + M); this includes right completion, product,
  and upstream construction/validation V/M. No ExtendedNFA or GNFA
  difference API is added. Reuses ADR-0002, #22, #23 and #43; no new ADR.
  Git commit: pending.

**Level 2 #42-#44 validation:** 26 focused tests pass. With Graphviz `dot`
available, the full suite has 853 passed, including all #1-#41 regressions
and the four executable mature examples. Strict mypy passes on
`automata_extensions` and `tests/fa` (60 source files); public imports/MRO
and `git diff --check` pass. #45-#62 remain TODO.

## #45 - Concatenation

- **Professor construction / meaning:** `L(result) = L(self) · L(other)`;
  epsilon transitions connect the left accepting states to the right
  initial state. The source PDFs were not accessed; the attached request
  supplies the professor specification.
- **Mature compatibility / public API:** `concatenation(other: DFA | NFA)`
  in `LanguageOperationsMixin` is available on ExtendedDFA and ExtendedNFA
  and returns a fresh ExtendedNFA. The existing mature DFA fixture from
  `tests/fa/test_state_elimination.py` reproduces
  `d.concatenation(d).accepts_input("aaaaaa") is True`. An equivalent
  explicit ExtendedNFA construction also reproduces upstream's
  `"a"` concatenated with `"b"` accepting `"ab"`.
- **Delegation / collisions / alphabets:** a DFA operand is converted once
  with `ExtendedNFA.from_dfa`; an NFA operand is used directly. Then the
  wrapper calls automata-lib 9.2.0 `NFA.concatenate` on an ExtendedNFA.
  Upstream maps the two state sets to disjoint integer identifiers, copies
  their transitions and adds the required epsilon edges. It takes the
  **union** of input alphabets, including when they differ. No DFA product,
  determinization, minimization or source mutation is introduced. The
  inherited upstream `concatenate()` name remains unchanged.
- **Tests / complexity / limits:** tests cover DFA and NFA operands,
  prefixes/suffixes, epsilon-language and empty-language operands,
  pre-existing epsilon edges, colliding names, different alphabets,
  immutability, return type and chained determinization/minimization.
  O(|Q1| + |Q2| + T1 + T2 + V) time and corresponding space include optional
  DFA conversion, transition copying and upstream validation V. T1/T2
  count stored transition entries and destinations. GNFA has no direct
  word-language construction here; upstream NFA reading of a state named
  None retains the limitation recorded in ADR-0007. Reuses ADR-0002 and
  ADR-0003; no new ADR. Git commit: pending.

## #46 - Kleene star

- **Professor construction / meaning:** `L(result) = L(self)*`, including
  epsilon. Add a new initial/final state, an epsilon entry into the old
  initial state, and epsilon repetition edges from former accepting states.
  The source PDFs were not accessed.
- **Mature compatibility / public API:** `kleene_star() -> ExtendedNFA`
  in the same `LanguageOperationsMixin` works on ExtendedDFA and ExtendedNFA.
  The existing mature DFA fixture reproduces
  `d.kleene_star().accepts_input("") is True`. An explicit ExtendedNFA
  for `"ab"` reproduces upstream's star example accepting `"abab"`.
- **Delegation / state safety:** convert DFA with `ExtendedNFA.from_dfa`
  when needed, then call automata-lib 9.2.0 `NFA.kleene_star` on the
  ExtendedNFA. Upstream selects the first unused nonnegative integer as
  the new state, preserving all old states and their epsilon edges, and
  preserves the input alphabet. No source mutation, determinization or
  minimization occurs.
- **Tests / complexity / limits:** tests cover zero, one and multiple
  repetitions; malformed words; stars of empty and epsilon languages;
  existing epsilon edges; collision-free new state; immutability; exact
  ExtendedNFA type; and composition with epsilon elimination. Expected
  O(|Q| + T + |F| + V) time and O(|Q| + T + |F| + M) space include optional
  DFA conversion and upstream construction/validation V/M. GNFA is not
  exposed. Reuses ADR-0002 and ADR-0003; no new ADR. Git commit: pending.

**Level 2 #45-#46 validation:** 25 focused tests and 878 full-suite tests
pass with Graphviz `dot` available, including every previously verified
#1-#44 test and all four supplied source examples. Strict mypy passes on
`automata_extensions` and `tests/fa` (62 source files); public imports,
MRO and `git diff --check` pass. #47-#62 remain TODO.

## #47 - Left quotient by a word

- **Professor requirement / mathematics:** calculate the states reached
  after reading a word. For word `w`, the result recognizes
  `w^{-1}L = {u | wu in L}`. The source PDFs were not accessed; the attached
  request supplies this specification.
- **Mature compatibility / API:** the public name is
  `left_quotient_word(word: str)`, avoiding upstream
  `NFA.left_quotient(other_automaton)`. The mature source fixture `d` from
  `tests/fa/test_state_elimination.py` verifies
  `d.left_quotient_word("a").accepts_input("aa") is True`. The return type
  is ExtendedDFA for ExtendedDFA, ExtendedNFA for ExtendedNFA. Separate
  `DFAQuotientMixin` and `NFAQuotientMixin` preserve concrete semantics;
  neither is installed on ExtendedGNFA.
- **DFA strategy:** follow the word's defined transitions and construct a
  fresh DFA with the reached state as initial, retaining states, alphabet,
  transitions, finals and `allow_partial`. A missing transition, including
  one for an unknown symbol, returns the existing same-type empty-language
  representative via `_restrict_to_states(frozenset())`; no trimming or
  minimization is implicit. The empty word preserves the language.
  Upstream DFA reading treats `None` as its missing-edge sentinel even
  when it is a structural state; the method follows that reading behavior.
- **NFA strategy:** reuse the last configuration of #16
  `execution_trace(word)`, including epsilon closure even for a rejected
  word. Add a collision-free initial state with epsilon edges to those
  active states; if the set is empty, add no edge. Clone transition rows
  and retain the original finals and alphabet. No determinization or
  source mutation occurs. Upstream NFA word reading with a state named
  `None` retains the limitation recorded in ADR-0007.
- **Tests / complexity / ADR:** `tests/fa/test_word_quotient.py` verifies
  `result.accepts_input(u) == source.accepts_input(w + u)` for many DFA/NFA
  words, partial/missing transitions, unknown symbols, epsilon moves,
  multiple NFA active states, one-state and empty languages, fresh types,
  immutability and composition. DFA costs O(|w| + |Q| + T + V) time and
  O(|Q| + T + M) space including reconstruction/validation V/M. NFA cost
  includes upstream trace simulation (up to O(|w| × |Q|) trace space),
  O(|Q| + T) graph copying and validation. Reuses ADR-0002, ADR-0003 and
  the established empty-language reconstruction policy; no new ADR.
  Git commit: pending.

## #48 - Right quotient by a word

- **Professor requirement / mathematics:** use the dual construction
  through reversal. For word `w`, the result recognizes
  `Lw^{-1} = {u | uw in L}`. The common private helper applies #36
  `reverse()`, #47 `left_quotient_word(w[::-1])`, then `reverse()` again.
- **Mature compatibility / API:** the public name is
  `right_quotient_word(word: str)`, distinct from upstream
  `NFA.right_quotient(other_automaton)`, whose behavior is untouched.
  The same mature source fixture verifies
  `d.right_quotient_word("a").accepts_input("aa") is True`; together with
  #47 the observable pair is exactly `(True, True)`.
- **Types / construction:** NFA returns the reversed composition directly
  as a fresh ExtendedNFA. Reversing a DFA produces an NFA, so the DFA
  specialization determinizes the result with verified #35 to return a
  fresh ExtendedDFA. This is the only type-restoring conversion; no
  minimization or unrelated right-quotient algorithm is introduced.
  Both preserve the source alphabet and language under the empty word.
  An unknown symbol yields an empty quotient, consistent with upstream
  word rejection and the #47 construction. Sources remain unchanged.
- **Tests / complexity / limits:** tests check
  `result.accepts_input(u) == source.accepts_input(u + w)` for multiple
  DFA/NFA words, including partial DFA, epsilon transitions, empty and
  unknown words, one-state languages, a two-symbol suffix that requires
  reversing the word, return types, immutability, composability, public
  imports and MRO. The NFA cost is two graph reversals plus #47 simulation
  and reconstruction, including intermediate validation. DFA adds #35
  subset construction, which can discover up to `2**N` states for an
  intermediate N-state NFA; worst-case time and space are exponential.
  The upstream `None`-state word-reading limits noted for #47 also apply.
  Reuses ADR-0002 and ADR-0003; no new ADR. Git commit: pending.

**Level 2 #47-#48 validation:** 134 focused tests and 1012 full-suite tests
pass with Graphviz `dot` available, including all #1-#46 regressions and
the mandatory mature `(True, True)` example. Strict mypy passes on
`automata_extensions` and `tests/fa` (66 source files); editable import,
MRO and `git diff --check` pass. #49-#62 remain TODO.

## #49 - Brzozowski derivatives of regular expressions

- **Professor requirement / recursive rules:** calculate derivatives of
  rational expressions by structural recursion: ∅ and ε differentiate to
  ∅; a literal differentiates to ε on a match and ∅ otherwise; union
  differentiates componentwise; concatenation adds the right derivative
  exactly when the left operand is nullable; a star differentiates to the
  operand derivative followed by the original star. For one symbol `a`,
  `L(D_a(R)) = a⁻¹L(R)`, the semantic counterpart of #47. No automaton
  quotient is called. The source PDFs were not accessed.
- **Public API / placement:** `from automata_extensions.regex import Regex`;
  `Regex(expression: str, *, input_symbols: AbstractSet[str] | None = None)`
  and `Regex.derivative(symbol: str) -> Regex`. The object and its private
  typed AST are immutable; each call returns a new object. A symbol must
  be one character. An unknown character yields the empty language; an
  empty or multi-character argument raises `ValueError`. A non-string
  argument raises `TypeError`. No `ExtendedRegex` upstream class exists.
- **Grammar / limits:** input accepts ordinary literal characters, `|`,
  implicit concatenation, `*`, grouping parentheses, and ε as `""` or
  `()`. Precedence is star, concatenation, then union. The explicit
  alphabet, when supplied, contains single characters and includes all
  input literals. Malformed regexes and unsupported `+`, `?`, `&`, `^`,
  `.`, classes, quantifiers and escapes raise upstream
  `InvalidRegexError`. This deliberately does not claim full automata-lib
  regex syntax compatibility.
- **Empty language / normalization:** the private `EmptyLanguage` node
  represents ∅; there is no special input token, so input `∅` remains a
  literal. `__str__` uses `∅` for diagnostic display and is not guaranteed
  to round-trip through the constructor. Private `nullable` supports the
  recursive concatenation rule. Private constructors absorb empty union
  operands, duplicate union operands, epsilon/empty concatenation, stars
  of empty/epsilon, and nested stars. No public `nullable()`, `simplify()`,
  word derivative, `to_nfa()`, or `to_dfa()` is added.
- **Tests / complexity / architecture:** `tests/regex/test_derivative.py`
  covers the recursive cases, precedence, nullable concatenation, malformed
  and unsupported syntax, explicit/empty alphabets, unknown symbols,
  immutability, normalization and independent NFA language checks over
  representative words. There is **no executed mature-reference derivative
  example** to reproduce. Parsing visits the source once, with additional
  structural-comparison costs from normalization. A derivative recursively
  visits AST nodes and builds an output that may grow with repeated calls;
  Python recursion depth bounds deeply nested input. ADR-0015 documents the
  owned AST and limited grammar. #50 is automaton Brzozowski minimization,
  distinct from #49; #51 may later reuse the AST for Thompson construction.
  Git commit: pending.

**#49 validation:** 49 focused tests pass. The full suite has 1060 passed
and 1 environment-dependent Graphviz test skipped (1061 collected), including
all #1-#48 regressions. Strict mypy passes on `automata_extensions`,
`tests/fa` and `tests/regex` (70 source files). Editable installation,
public Regex/FA imports and `git diff --check` pass. #50-#62 remain TODO.

## #50 - Brzozowski automaton minimization

- **Professor algorithm / API:** `brzozowski_minimize() -> ExtendedDFA`
  applies reverse, determinize, reverse, determinize. `BrzozowskiMixin`
  exposes the operation on ExtendedDFA and ExtendedNFA; GNFA's regex
  labels and absent word-reading semantics do not support it. Both source
  types produce a fresh minimal ExtendedDFA of the same language. #49 regex
  derivatives remain separate and untouched. The source PDFs were not
  accessed.
- **Reverse representation bridge:** verified #36 `reverse()` represents
  the old final-state set with a fresh epsilon-only NFA initial state.
  Verified #35 `determinize()` correctly retains it in the first subset,
  which can create an equivalent duplicate of the logical initial subset.
  After each determinization, a private helper removes only that exact
  reverse-created state from subset identity, merges only identical
  resulting subsets, checks transition/finality agreement, and builds a
  fresh ExtendedDFA. It does not search for equivalent states or call
  ordinary `minimize()`. The public #35/#36 behavior is unchanged.
  Partial DFA edges remain partial where the subset construction omits
  empty destinations. The source is never mutated. ADR-0016 records this
  compatibility decision.
- **Mature compatibility / tests:** the executed reference fixture satisfies
  `d.brzozowski_minimize() == d.minimize()` exactly (`True`). Upstream DFA
  equality compares languages, so tests also require `is_minimal() is True`:
  the mature fixture has three result states rather than the four produced
  by unnormalized composition; a one-state accepting DFA stays at one state.
  `tests/fa/test_brzozowski.py` covers complete and partial DFA, equivalent
  and inaccessible states, empty and universal languages, finite and cyclic
  languages, epsilon acceptance, ordinary and epsilon NFA, multiple active
  NFA states, immutability, repeat calls, ExtendedDFA composition and MRO.
  An additional read-only enumeration checked 360 two-state complete or
  partial DFA structures for language preservation and minimality, plus
  1024 two-state NFA structures (including epsilon edges) for sampled-word
  preservation and minimality.
- **Complexity / limitations:** two reversals and two reachable-subset
  constructions dominate. Either determinization may have exponentially
  many subsets of its input NFA, and the second input may itself have grown
  exponentially. The private normalization copies each resulting transition
  graph and invokes constructor validation; no cache is added. Upstream
  word-reading limitations for NFA states named `None` remain unchanged.
  Git commit: pending.

**#50 validation:** 14 focused tests pass. The full suite has 1074 passed
and 1 existing environment-dependent Graphviz test skipped (1075 collected),
including all #1-#49 regressions. Strict mypy passes on
`automata_extensions`, `tests/fa` and `tests/regex` (72 source files).
Public imports, MRO and `git diff --check` pass. #51-#62 remain TODO.
