# ADR-0015 — Immutable regex syntax tree for derivatives

Status: Accepted
Date: 2026-09-24

## Context

Professor requirement #49 asks for recursive Brzozowski derivatives of
rational expressions. The supplied mature documentation has no executed
derivative example; its `BrzozowskiMixin.brzozowski_minimize()` concerns
future requirement #50 instead. automata-lib 9.2.0 represents regexes as
strings and parses them with tokens that build a mutable `NFARegexBuilder`.
It has no reusable immutable regex AST, `derivative()`, or `nullable()`.

## Decision

Add `automata_extensions.regex.Regex`, not `ExtendedRegex`: no upstream
`Regex` class is being extended. Keep six private, frozen AST forms:
empty language, epsilon, literal, union, concatenation and star. Parse the
classical grammar (`|`, implicit concatenation, `*`, parentheses, and `""`
or `()` for epsilon) within Automatix. Reject unsupported upstream regex
operators explicitly with `InvalidRegexError`. A supplied alphabet contains
single-character symbols and must include every literal in the expression.

The public operation `derivative(symbol: str) -> Regex` applies the textbook
recursive rules to exactly one character and returns a fresh immutable
value. A character absent from the expression yields the empty-language
node. Empty or multi-character derivative arguments are rejected. Keep
`nullable` and the small identity-based normalization constructors private;
no public `nullable()` or `simplify()` is introduced.

The empty language has an internal AST node but no constructor input token.
In particular, `∅` remains a literal in input, as in upstream. `__str__`
renders the internal empty language as `∅` for diagnosis; this rendering
is not promised as a lossless, reparsable serialization.

## Alternatives considered

- Reuse upstream parser tokens or `NFARegexBuilder`: these construct mutable
  NFAs rather than preserving an expression tree and would couple the
  extension to upstream parser internals.
- Differentiate strings directly: repeated parsing, parenthesis management
  and the missing empty-language token obscure the recursive algorithm.
- Implement all upstream regex extensions now: their derivatives require
  additional algebra and alphabet semantics beyond #49.
- Expose every AST node or a public simplifier: unnecessary public contracts
  for this requirement.

## Rationale

An owned immutable AST expresses the mathematical rules directly, supports
structural normalization, and can later be reused for Thompson's #51
construction. Restricting grammar explicitly avoids claiming incomplete
compatibility with automata-lib's richer regex language.

## Consequences

Parsing is linear in input length before structural normalization costs.
One derivative visits the input tree recursively and builds a result whose
size can grow under repeated differentiation; subtree equality and hashing
may add cost. No cache is introduced. Very deep expressions are subject to
Python's recursion limit. String rendering is deterministic and
precedence-aware but is diagnostic when it contains internal empty language.

The identity `L(D_a(R)) = a⁻¹L(R)` relates this feature to #47 without
coupling their implementations. #50 is a different Brzozowski algorithm
over automata. #51 can consume the AST later, but no NFA conversion is
implemented here.

## Related requirements

Implements #49 only. #50–#62 remain TODO.

## Supersedes

None. Complements ADR-0001 and ADR-0002 without changing them.
