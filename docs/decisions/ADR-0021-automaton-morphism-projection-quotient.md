# ADR-0021 — Automaton morphism, projection, and state-quotient semantics

Status: Accepted
Date: 2026-09-24

## Context

Professor requirement #61 asks for automaton morphisms through state merging
or projection while preserving transitions. The supplied mature reference
names a common `MorphismMixin` with `is_morphism_to`, `project`, and
`quotient_by`. Its executed examples establish an identity morphism, the
acceptance of `xxx` after `a -> x, b -> None`, and quotient-state names
`["0", "2"]` after merging states `0` and `1`. The source material does not
settle final-state reflection, partial-transition definedness, return types,
or how a non-congruent DFA merge retains conflicting outgoing edges. The
mature description explicitly permits such non-congruent merges.

Automata-lib 9.2.0 supplies DFA/NFA constructors and individual labeled
edge iteration but no corresponding public morphism or projection API.
DFA edges have one destination; NFA edges may have several, and NFA epsilon
is labeled by the empty string.

## Decision

Automatix uses one shared `MorphismMixin` implementation exposed by
`ExtendedDFA` and `ExtendedNFA`, but not by `ExtendedGNFA`. These choices
below, beyond the three mature observable examples, are **Automatix design
decisions** resolving the underspecified contract.

`is_morphism_to(other, state_map) -> bool` accepts DFA/NFA source and target
combinations. The map domain must equal the full source state set, every
image must belong to the target, alphabets must agree, and the source initial
state must map to the target initial state. Every source final must map to a
target final; nonfinal states may also map to final states. Every source edge,
including an NFA epsilon edge, must have its mapped counterpart in the
target. Target-only edges are allowed. A missing source transition imposes no
condition, so no implicit DFA sink is constructed. Invalid map semantics
return `False`. This is forward edge/finality preservation, not isomorphism
or equality/reflection of transition sets.

`project(symbol_map) -> ExtendedNFA` requires a mapping defined on exactly
the source alphabet. Each image is one character or `None`; `None` becomes
an NFA epsilon edge. Existing source NFA epsilon edges are unchanged.
Colliding projected labels union all destinations. States, initial state and
final states are retained; the result alphabet is exactly the non-None
images. Invalid map domains or image labels raise `ValueError`. A fresh NFA
is returned consistently, even when a particular projection is deterministic.
Arbitrary target words are outside #61.

`quotient_by(state_map) -> ExtendedNFA` requires a mapping defined on exactly
the source state set, with hashable image labels. The result states are its
image; the initial state is mapped; a quotient state is final iff at least
one source final maps to it. Every source edge is mapped, with all
destinations unioned on collision. Non-congruent DFA merges are accepted and
retain every edge as NFA nondeterminism. Invalid map domains or unhashable
image labels raise `ValueError`. The quotient map is then a valid morphism
under the forward-only predicate above.

Neither transformation modifies its source or caller map. Neither performs
automatic completion, determinization, or minimization. The shared module
is integrated selectively to avoid misleading GNFA regex-label semantics.

## Alternatives considered

- Requiring transition-set equality or final-state reflection would reject
  the natural quotient map after a non-congruent merge or a mixed-final fibre.
- Choosing one destination for a merged DFA transition would violate the
  professor's transition-preservation requirement.
- Rejecting every non-congruent merge would conflict with the mature
  description.
- Returning a DFA only when projection happens to be deterministic would
  make the API's return type input-dependent and obscure epsilon/collision
  behavior.
- Attaching the mixin to `ExtendedFA` would expose an unsupported GNFA API.

## Consequences

Projection and quotient may recognize languages that differ from the source
under state fusion, as the mathematical operations require; they preserve
mapped paths rather than claim language equality. Callers can explicitly
determinize a returned NFA when needed. The exact mature examples are
regression tests. #26 isomorphism, #32 minimization, and #62 syntactic monoid
remain separate features.

## Related requirements

Implements #61. #62 remains TODO.

## Supersedes

None.
