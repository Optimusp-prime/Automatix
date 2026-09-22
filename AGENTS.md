# AGENTS.md — Automatix

## 1. Project purpose

Automatix is a pedagogical Python project that extends `automata-lib`
without modifying the upstream library.

Target upstream version:

    automata-lib == 9.2.0

All new functionality belongs to:

    automata_extensions/

The upstream reference source is available locally under:

    reference/automata-lib/

That directory is READ-ONLY reference material.

Never modify upstream source code, either in:

    reference/automata-lib/

or in the installed Conda environment / site-packages.


# 2. Sources of truth and precedence

When making technical or architectural decisions, use the following
sources in this order.

## 2.1 Project specification

The professor's project specification is the authoritative source for:

- required features;
- pedagogical objectives;
- architectural constraints;
- algorithm requirements;
- naming;
- immutability;
- testing requirements;
- documentation requirements;
- expected project philosophy.

If another source conflicts with the project specification, the project
specification wins.

## 2.2 automata-lib 9.2.0 source code

The real source code under:

    reference/automata-lib/

is authoritative for facts about the actual upstream API:

- class hierarchy;
- method signatures;
- constructors;
- transition representations;
- inheritance;
- abstract methods;
- types;
- exceptions;
- behavior;
- MRO;
- existing algorithms.

Never guess an automata-lib API.

Inspect the actual 9.2.0 source before relying on an upstream method.

## 2.3 automata_extensions reference documentation

The professor-provided automata_extensions documentation is an important
implementation reference.

It contains implementations and examples that were executed and verified.

Use it to understand:

- appropriate mixin decomposition;
- known API naming decisions;
- known upstream name collisions;
- known implementation pitfalls;
- expected behavior;
- sensible dependency relationships between algorithms;
- already discovered compatibility problems.

However, do not blindly copy code or architecture.

First verify that it respects the project specification and the actual
automata-lib 9.2.0 API.


# 3. Fixed architectural decisions

The following decisions are project-wide contracts.

## 3.1 Upstream dependency

The supported upstream version is fixed:

    automata-lib == 9.2.0

Do not attempt to support arbitrary future versions unless explicitly
requested.

## 3.2 No upstream modification

Never modify automata-lib.

If automata-lib already implements the required operation adequately,
prefer:

- a wrapper;
- delegation;
- composition;

instead of duplicating the implementation.

## 3.3 Extension strategy

Use inheritance and mixins.

Monkey patching is NOT the default architecture.

Only introduce monkey patching if a concrete compatibility problem
requires it and the decision has been explicitly justified.

## 3.4 Common finite-automaton layer

Shared finite-automaton behavior should be exposed through `ExtendedFA`
whenever technically possible.

The intended hierarchy is conceptually:

    FA
    |
    ExtendedFA
      |
      +-- ExtendedDFA
      +-- ExtendedNFA
      +-- ExtendedGNFA

The actual Python MRO must always remain valid.

Algorithms that depend only on general finite-automaton concepts such as:

    states
    transitions
    input_symbols
    initial_state
    final_states

should normally be implemented once at the common FA extension layer.

Do not duplicate the same algorithm independently in DFA and NFA unless
their semantics or transition representation genuinely require different
implementations.

## 3.5 Specialization

Only functionality intrinsically dependent on concepts such as:

- deterministic transition functions;
- partial DFA behavior;
- epsilon transitions;
- NFA state sets;
- determinization;

should live in DFA- or NFA-specific mixins.


# 4. Mixin design rules

Mixins must represent coherent functional domains.

A mixin:

- must be named `SomethingMixin`;
- must not define `__init__`;
- must not introduce persistent mutable instance state;
- must not mutate the source automaton;
- may construct and return new automata when implementing transformations;
- should provide a coherent family of related methods;
- must appear before the upstream main class in multiple inheritance where
  required by the architecture.

Avoid giant catch-all mixins.

The initial files such as:

    analyse.py
    conversions.py
    grammaire.py
    visualisation.py

are architectural scaffolding, not an obligation to place every future
method into four huge files.

When implementing a feature family, inspect the reference documentation
before deciding the final mixin.

For example, the reference architecture identifies coherent domains such
as:

    GraphMixin
    TraversalMixin
    AccessibilityMixin
    CycleMixin
    SCCMixin
    SubautomatonMixin

and DFA-specific domains such as:

    CompletenessMixin
    ComplementMixin
    MinimizationMixin
    ProductMixin
    InclusionMixin

and NFA-specific domains such as:

    DeterminizationMixin
    EpsilonMixin
    EliminationMixin

Prefer a specialized coherent mixin when doing so prevents unrelated
algorithms from accumulating in a single file.


# 5. Mandatory feature-design procedure

DO NOT immediately implement a requested algorithm.

Before writing production code for every new feature, perform a design
check.

The design check must answer all of the following.

## 5.1 Specification

Identify exactly what the professor's specification requires.

Determine:

- mathematical meaning;
- required public method name;
- required behavior;
- expected result;
- relevant edge cases.

Do not silently invent semantics that are not defined.

## 5.2 Existing upstream functionality

Inspect automata-lib 9.2.0.

Determine whether:

- the functionality already exists;
- a lower-level primitive already exists;
- a wrapper is sufficient;
- the upstream implementation has different semantics;
- using the upstream implementation would violate the pedagogical goal.

Reuse upstream functionality where appropriate.

Do not reimplement existing behavior without a reason.

## 5.3 Reference implementation

Inspect the professor-provided automata_extensions documentation for the
same feature.

Determine:

- the documented public method name;
- its mixin;
- its return type;
- related helper methods;
- known name collisions;
- known bugs or compatibility issues;
- relationships with later algorithms.

Use this information to avoid rediscovering already known architectural
problems.

## 5.4 Dependency analysis

Before implementing the feature, identify which later algorithms are
likely to reuse it.

Prefer building reusable foundations rather than implementing isolated
one-off logic.

For example:

    graph-neighbor primitives
        -> traversal
        -> accessibility
        -> cycle analysis
        -> SCC / language properties

Do not duplicate traversal logic inside several later algorithms when a
shared primitive should exist.

## 5.5 Placement

Decide whether the feature belongs to:

- common FA functionality;
- DFA-specific functionality;
- NFA-specific functionality;
- GNFA-specific functionality;
- language/grammar functionality;
- visualization functionality.

Make this decision before implementing the algorithm.

## 5.6 Public API

Define before coding:

- method name;
- parameters;
- defaults;
- return type;
- exceptions;
- mutability behavior.

Avoid changing a public signature later unless a genuine specification
problem is discovered.

## 5.7 Name-collision check

Before introducing any public method, search automata-lib 9.2.0 for the
same name.

Do not accidentally change the meaning of an upstream method.

When a collision exists but the semantic operation is different, choose a
clear distinct name.

Examples from the reference architecture include names such as:

    predecessors_graph()
    successors_graph()

instead of colliding with automata-lib's word-oriented
`predecessors()` / `successors()` methods.

Likewise, quotient methods may require explicit names such as:

    left_quotient_word()
    right_quotient_word()

when upstream uses similar names for different arguments or semantics.


# 6. Immutability contract

Automata are immutable mathematical objects.

Never mutate `self`.

A method representing a transformation must return a new automaton.

Correct style:

    dfa2 = dfa.trim()
    dfa3 = dfa.complete()
    dfa4 = dfa.minimize()

Incorrect style:

    dfa.trim()  # mutating dfa internally

Queries may return sets, booleans, traces, partitions, strings or other
values as appropriate.

When a transformation returns another automaton, prefer an appropriate
automata-lib / automata_extensions object rather than an ad-hoc structure.


# 7. Composability

Transformation methods should be designed to compose naturally.

The architecture should support expressions such as:

    dfa.trim().minimize().to_regex()

or:

    dfa.reverse().determinize().minimize()

A method must not leave hidden mutations that break later chained calls.

Return types must therefore be chosen with future composition in mind.


# 8. Algorithm style

This is a pedagogical library.

Prefer algorithms that are:

- mathematically clear;
- readable;
- close to textbook definitions;
- straightforward to explain;
- straightforward to test.

Do not introduce premature optimization.

A clear BFS/DFS is preferable to a compact but obscure implementation.

Optimize only when there is a demonstrated reason and the optimization
does not harm pedagogical clarity.


# 9. Caching policy

Do NOT introduce algorithm-result caching by default.

Caching reachable states, accessibility results, SCCs, etc. affects
architecture and behavior and was explicitly left as a design question
for later consideration.

If caching becomes necessary:

1. justify the need;
2. analyze compatibility with immutability;
3. analyze copying/pickling behavior;
4. analyze interaction with upstream cached methods;
5. add dedicated tests;
6. document the decision.

Do not silently add caches as a micro-optimization.


# 10. Typing and data structures

Use Python typing consistently.

Use immutable structures such as `frozenset` when appropriate to the
mathematical object or public API.

Respect the types exposed by automata-lib 9.2.0.

Do not weaken types merely to make an implementation easier.

Prefer meaningful type aliases when complex state or transition types are
reused.


# 11. Naming conventions

Use consistent terminology.

Computations / transformations should use names such as:

    accessible_states()
    coaccessible_states()
    useful_states()
    trim()
    complete()
    complement()
    reverse()

Predicates should normally begin with `is_`:

    is_accessible()
    is_complete()
    is_trim()
    is_empty()
    is_finite()
    is_deterministic()

Conversions should normally begin with `to_`:

    to_regex()
    to_dfa()
    to_nfa()
    to_gnfa()
    to_grammar()

Prefer terminology from formal-language and automata theory.

Do not invent synonyms when the specification already provides a name.


# 12. Documentation contract

Every public method must have a structured docstring.

The docstring should document, as relevant:

    Parameters
    Returns
    Raises
    Complexity
    References

Algorithmic complexity must be explicitly documented.

Example structure:

    def accessible_states(self):
        """
        Compute the set of accessible states.

        Returns
        -------
        set
            Reachable states from the initial state.

        Complexity
        ----------
        O(|Q| + |E|)

        References
        ----------
        Hopcroft, Motwani & Ullman.
        """

Use complexity definitions consistent with the actual implementation.

Do not copy a complexity statement without checking that it matches the
code.


# 13. Testing contract

Tests are mandatory.

Use pytest.

Every algorithm should have enough tests to cover the meaningful cases
for that algorithm.

When relevant, include:

- nominal case;
- minimal case;
- boundary case;
- empty-language / empty-like case where valid;
- one-state automaton;
- inaccessible states;
- sink/trap states;
- multiple connected components;
- epsilon transitions for NFA behavior;
- partial DFA behavior when supported.

In addition, transformation tests should verify:

- the original automaton was not modified;
- the returned object has the expected type;
- language semantics are preserved when appropriate;
- chaining/composability still works.

For functionality implemented at the common FA layer, test it against
each relevant concrete class rather than validating it only on DFA.

Do not write tests merely to reproduce the implementation.

Tests must validate the mathematical contract.


# 14. Regression discipline

Whenever a bug is discovered:

1. write a regression test demonstrating it;
2. identify whether the cause is:
   - our extension;
   - an upstream behavior;
   - an architectural mismatch;
3. fix the smallest correct layer;
4. keep the regression test permanently.

Do not patch symptoms in multiple algorithms.

Fix shared problems at the shared abstraction layer.


# 15. Existing upstream bugs and compatibility issues

The reference documentation contains compatibility problems discovered
through real execution.

Before changing low-level behavior involving:

- copying;
- `input_parameters`;
- `__slots__`;
- cached methods;
- pickling;
- chained calls on temporary automata;

inspect the documented known issues first.

Do not independently invent a workaround if an already-understood root
cause and solution is documented.

Any compatibility patch that globally affects automata-lib behavior must
be explicitly justified and tested.


# 16. Visualization

Graphviz is the visualization engine.

Avoid duplicating rendering logic.

The intended layering is conceptually:

    dot()
        -> graph()
            -> svg()
            -> png()
            -> pdf()

with TikZ / LaTeX support built as appropriate.

Common rendering primitives should be shared.

Do not implement separate unrelated rendering pipelines for every output
format.


# 17. Separation of concerns

Keep distinct:

- automaton representation;
- language semantics;
- traversal/graph analysis;
- transformations;
- conversions;
- visualization;
- grammar functionality.

Do not mix unrelated concerns simply because they operate on the same
class.

Factor shared algorithms.

Never duplicate code when a reusable abstraction can express the same
operation clearly.


# 18. Implementation order

Follow the pedagogical levels and ordering from the project specification
unless a reusable prerequisite must reasonably be introduced first.

For a prerequisite introduced earlier than its listed public feature:

- keep it minimal;
- make its role explicit;
- do not implement unrelated future functionality.

Do not implement several future algorithms speculatively.


# 19. Scope discipline

When asked to implement one feature:

- implement that feature;
- implement only the helpers required for it;
- add its tests;
- add/update its documentation;
- update exports if necessary.

Do NOT opportunistically implement unrelated algorithms from later in the
roadmap.

This keeps commits understandable and makes regressions easier to locate.


# 20. Definition of done for a feature

A feature is not complete until:

1. its specification has been checked;
2. upstream automata-lib 9.2.0 has been inspected;
3. the reference extension documentation has been inspected;
4. its architectural placement has been justified;
5. its public API has been decided;
6. typing is correct;
7. immutability is preserved;
8. relevant tests pass;
9. edge cases are covered;
10. complexity is documented;
11. no unnecessary duplication was introduced;
12. existing tests still pass;
13. package imports remain valid.


# 21. Required response before substantial implementation

For substantial new functionality, briefly report before or alongside the
implementation:

    Feature:
    Specification:
    Existing upstream support:
    Reference-extension behavior:
    Dependencies:
    Chosen layer/mixin:
    Public API:
    Return type:
    Immutability considerations:
    Important edge cases:
    Planned tests:
    Complexity target:

If an unresolved ambiguity would change the public API, architecture or
mathematical semantics, STOP and ask for clarification instead of guessing.


# 22. Repository rules

The following directories have different roles.

    automata_extensions/
        Our implementation. May be modified.

    tests/
        Our tests. May be modified.

    reference/automata-lib/
        Upstream reference only. NEVER modify.

    notebooks/
        Experimental/manual demonstrations.
        Do not make production behavior depend on notebooks.

Generated metadata such as:

    *.egg-info/
    __pycache__/
    .pytest_cache/

is not source code and must not be manually edited.


# 23. Packaging

The project must remain installable in editable mode:

    python -m pip install -e .

The normal public import should remain clean, for example:

    from automata_extensions.fa import ExtendedDFA

Do not require users to import internal mixin modules just to use the
public API.


# 24. Quality gate

Before declaring work complete, run at minimum:

    python -m pytest

Also verify imports for the public classes affected by the change.

No feature should be considered finished while existing tests are failing.


# 25. Core principle

The goal is not merely to make the current test pass.

Every implementation decision should be made with the rest of the
automata project in mind.

Prefer a stable reusable abstraction now over a shortcut that will force
the same algorithm to be rewritten later.

At the same time, do not over-engineer speculative future functionality.

Build the smallest architecture that correctly supports the current
feature and its already-known future dependencies.

# 26. Project tracking

The canonical implementation tracker is:

    docs/IMPLEMENTATION_STATUS.md

Before starting a feature:

1. locate the corresponding professor requirement in the tracker;
2. verify its current status;
3. set it to `DESIGN` while performing the required design analysis.

When implementation starts:

    DESIGN -> IN_PROGRESS

A feature may only become:

    VERIFIED

when all of the following are true:

- the required behavior is implemented;
- relevant tests pass;
- existing tests still pass;
- the public API is stable;
- typing is correct;
- immutability is preserved;
- complexity is documented;
- required documentation is present.

After completing a feature, update:

    docs/IMPLEMENTATION_STATUS.md

with:

- final public API;
- implementation layer / mixin;
- test location;
- relevant notes or constraints.

Never mark a feature VERIFIED merely because one test passes.

## 26.1 Architecture decisions

Durable architectural decisions must be documented under:

    docs/decisions/

using Architecture Decision Records (ADR).

Create an ADR when a decision affects several current or future features,
for example:

- mixin organization;
- common FA abstractions;
- traversal primitives;
- caching;
- return-type policy;
- DFA/NFA specialization;
- epsilon-transition handling;
- compatibility patches.

Do not revisit an accepted ADR without a concrete reason.

If a previous decision must change, document the new decision and indicate
which ADR it supersedes.

Git history is not a replacement for the implementation tracker or ADRs.

# 27. Governance files

`AGENTS.md` defines project-wide development rules.

Do not modify `AGENTS.md` unless the user explicitly requests a change
to the project rules.

Accepted ADRs must not be silently rewritten to match a new implementation.

If a decision changes, create a new ADR that supersedes the previous one.

Do not weaken tests, specifications, tracking requirements, or public
contracts merely to make an implementation pass.

Tracking updates are part of the feature itself.

A feature implementation is not complete if the code and tests are finished
but `docs/IMPLEMENTATION_STATUS.md` still describes the old state.
