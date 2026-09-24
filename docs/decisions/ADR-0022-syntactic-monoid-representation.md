# ADR-0022 — Syntactic monoid representation and canonical normalization

Status: Accepted
Date: 2026-09-24

## Context

Professor requirement #62 asks for the syntactic monoid constructed from
word-induced transformations. The supplied mature extension names DFA-only
`SyntacticMonoidMixin.syntactic_monoid()` and reports three elements for its
executed modulo-three DFA. It specifies neither the public transformation
representation nor the return container. The broader analysis mentions
`SyntacticMonoid` and `TransitionMonoid` as concepts, without a class API.

Closing transformations over an arbitrary DFA's stored states instead yields
that **representation's transition monoid**. Inaccessible or equivalent states
can enlarge it, while partial transitions do not define total maps. The
syntactic monoid of a language is isomorphic to the transition monoid of its
minimal complete DFA. Verified requirement #60 already builds that DFA from
the distinct left quotients, including an empty quotient when needed.

## Decision

Expose `ExtendedDFA.syntactic_monoid() -> frozenset[tuple[int, ...]]` through
`SyntacticMonoidMixin` only. First call `residual_automaton()`; do not redo
minimization or close over the source transition table. The residual states
must be exactly `q0, ..., q(n-1)`; their numeric indices define each tuple's
positions and destinations: entry `i == j` means `qi -> qj`. This tuple and
frozenset representation is an **Automatix public API decision**, not a type
specified by the supplied mature material. The set has no iteration order.

Include `tuple(range(n))` as the empty word's identity, including for an
empty alphabet. Construct one total generator for each input letter from the
complete residual DFA. A queue closes the discovered transformations by
appending each letter. If `tau_w` is the current tuple and `tau_a` the letter
tuple, the appended word `wa` has `tau_(wa) = tau_a ∘ tau_w`, encoded by
`next[i] = tau_a[tau_w[i]]`. Extending each discovered element by each letter
generates every word by induction from the empty word; all-pairs composition
is unnecessary.

The method is a pure query. It does not mutate the source or #60's fresh
residual automaton and does not cache its result. Its output is a language
invariant up to monoid isomorphism; literal tuple equality across arbitrary
renamings is not promised. Partial source DFAs are normalized through #60's
empty residual. Source-inaccessible and equivalent states disappear.

## Alternatives considered

- Direct closure on `self` would calculate a potentially larger source
  transition monoid and mishandle partial transitions.
- `complete().minimize()` can also give a suitable minimal complete DFA but
  duplicates normalization policy already verified by #59/#60 and provides
  less direct q-index semantics.
- A mutable set or mapping would weaken the immutable mathematical API.
- Dedicated public monoid or transformation classes, multiplication tables,
  and general algebraic operations are unsupported by the supplied contract.
- automata-lib 9.2.0 has no syntactic-monoid closure operation to delegate to.

## Consequences

If the canonical DFA has `n` states, the alphabet has `s` letters, and the
monoid has `m` transformations, closure uses expected `O(m*s*n)` time and
`O(m*n + s*n)` space, in addition to #60's construction cost and storage.
The explicit result can be large: `m <= n**n`. The mature three-state DFA
produces exactly identity and two rotations, matching its observed size 3.

## Related requirements

Implements final professor requirement #62 using verified #59/#60. Does not
change their public behavior or introduce a standalone algebra framework.

## Supersedes

None.
