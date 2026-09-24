# ADR-0020 — Myhill–Nerode language-quotient representation

Status: Accepted
Date: 2026-09-24

## Context

Professor requirement #59 asks for the classes of Myhill–Nerode through
construction of a language's distinct left quotients. Requirement #30 already
exposes `equivalence_classes()` as a partition of **all stored DFA states**,
including unreachable ones, by equality of their right-languages. The mature
reference calls that state partition Myhill–Nerode classes but supplies no
standalone #59 public method or quotient-collection representation. Requirement
#60 separately calls for an automaton assembled from left quotients.

For partial DFAs, a reachable missing transition denotes the empty quotient.
It may have no corresponding stored state, or it may equal the right-language
of an explicit reachable dead state. Thus neither returning #30 unchanged nor
merely filtering its classes always enumerates the language's quotients.

## Decision

Automatix adds the DFA-only
`myhill_nerode_quotients() -> tuple[ExtendedDFA, ...]`. This public API and
representation are **Automatix decisions** resolving the absent standalone
mature contract. Each fresh tuple item recognizes one distinct left quotient;
#47's `left_quotient_word` constructs it. #30's unchanged state partition
deduplicates equal right-languages. Only classes with an accessible member
participate. A missing edge reachable from the initial state adds one empty
quotient only if no accessible explicit state already recognizes the empty
language.

A BFS from the initial state visits input symbols in sorted order. Its first
witness for each state is shortest, with lexical symbol order breaking ties.
The initial language is first. Other explicit quotients follow their first
class witness. An implicit empty quotient, if new, is appended last. This
order is independent of hash and set iteration; returned DFA state names are
not otherwise constrained.

The API is limited to `ExtendedDFA`. It neither changes #30 nor names/builds
the residual-automaton states of future #60.

## Alternatives considered

- Reusing `equivalence_classes()` as-is would include inaccessible state
  languages and omit a possible implicit empty quotient.
- A reachability filter alone would still omit that implicit quotient.
- A new `myhill_nerode_classes()` alias would confuse state classes with word
  classes and provide no quotient automata.
- Enumerating word classes or introducing public `Language`/`Quotient`
  objects would exceed the requirement and duplicate #47's representation.
- Completing the source and exposing its synthetic sink as a result state
  would make quotient representation depend on generated trap names and
  unnecessarily alter the established partial-DFA convention.

## Consequences

Each output automaton may copy the source structure, so materialization costs
grow with the number of distinct quotients. The tuple is deterministic in
language order and its members remain composable `ExtendedDFA` objects.
Future #60 may use these quotient languages to build a residual automaton,
but must specify its own state naming and transitions.

## Related requirements

Implements #59 using #30 and #47. #60–#62 remain TODO.

## Supersedes

None.
