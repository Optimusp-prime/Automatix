# ADR-0024 — Bounded order search for regex conversions

Status: Accepted
Date: 2026-09-27

## Context

The mature documentation exposes DFA-only `to_regex_optimum()` and
`to_regex_arden_optimum()`, but specifies neither a complete elimination
order search nor a tie-break rule. Both executed three-state outputs are
observable contracts. Requirements #53 and #54 already have verified
converters whose exact, more verbose results must remain unchanged.

## Decision

Extract each existing conversion engine into a private order-parameterized
method. The original public methods call those engines with their
established lexical order. The two optimum methods try the first 24
permutations of states sorted by the established heterogeneous-safe key.
For Arden, only accessible states participate, as in #54. Every raw
candidate is parsed and rendered through the private #49 immutable Regex
AST, which removes redundant grouping and applies its existing identity
rules. Represent epsilon alone as the established empty string. Rank
candidates by length, then lexicographically.

The three-state mature fixture tries every order. The results are exactly
`(b|ab*ab*a)*` and `(ab*ab*a|b)*`. The limit of 24 keeps larger DFA
instances usable; neither result is promised globally minimal.

## Alternatives considered

- An unbounded search over all permutations has factorial work for every
  DFA and quickly becomes impractical.
- A new state-elimination or Arden solver would duplicate verified #53/#54
  logic and risk changing their public outputs.
- A fixture-specific rewrite would not define a general algorithm.

## Consequences

For n states, k = min(n!, 24) orders are tried. The state-elimination path
makes O(k*n³) label updates plus k GNFA constructions; the Arden path makes
O(k*m³) coefficient updates for m accessible states. Intermediate strings
and AST comparisons can grow exponentially. The chosen result is stable for
ordinary and heterogeneous states. No automaton is mutated or cached.

## Related requirements

M5 and M6, reusing primary #49, #53 and #54.

## Supersedes

None.
