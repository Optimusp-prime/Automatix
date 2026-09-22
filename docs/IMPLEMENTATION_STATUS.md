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

Current feature: —  
Next planned feature: DFS / BFS traversal  
Current phase: foundation complete, algorithm design beginning

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
All algorithmic requirements remain TODO, including those for which upstream
already provides behavior: inherited behavior alone does not validate the
project requirement. Planned public APIs remain TBD until feature design
confirms their names and contracts.

## Level 1

| # | Requirement | Planned public API | Layer / Mixin | Status | Tests | Notes |
| - | ----------- | ------------------ | ------------- | ------ | ----- | ----- |
| 1 | DFS iterative and recursive | TBD | TBD | TODO | — | — |
| 2 | BFS | TBD | TBD | TODO | — | — |
| 3 | Accessible states | TBD | TBD | TODO | — | — |
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

No algorithmic feature has been implemented yet.

Feature-specific notes will be added when a feature enters DESIGN.

Each future feature note may contain:

- Specification
- Design decisions
- Implementation
- Public API
- Tests
- Complexity
- Related requirements
- ADR references
- Known limitations
- Git commit
