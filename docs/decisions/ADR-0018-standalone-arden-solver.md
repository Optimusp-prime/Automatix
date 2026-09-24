# ADR-0018 — Standalone Arden solver API

Status: Accepted
Date: 2026-09-24

## Context

Professor requirement #57 asks for Arden's lemma to solve rational-language
equations. Requirement #58 separately covers systems of equations associated
with automata. The supplied mature documentation and upstream automata-lib
9.2.0 do not establish a standalone public solver name for one equation.
Automatix already owns the immutable `Regex` representation from #49.

## Decision

Introduce the Automatix function
`automata_extensions.equations.solve_arden(coefficient: Regex,
constant: Regex) -> Regex`. It solves only `X = A X ∪ B`, returning the
unique solution `A* B` when epsilon is not in `L(A)`. Reject a nullable
coefficient with `ValueError` rather than returning a merely least solution.
The function checks operand types and does not mutate either value.

Reuse #49's private immutable AST and its `nullable`, `star`, and
`concatenate` operations. A private `Regex._from_ast` factory constructs a
fresh result without parsing or exposing AST node classes publicly. Merge
both operand alphabets so explicitly declared symbols are not lost. The
internal empty-language node participates normally, without adding a public
empty-language parser token or a separate regex representation.

Do not refactor #54's `ExtendedDFA.to_regex_arden()`: its string-level
factorization preserves a verified exact mature output. The standalone
function uses AST values for a single equation; #54 solves an entire DFA
equation system and retains its current public contract.

## Alternatives considered

- A string-based API or a new regex parser would duplicate #49 and obscure
  the mathematical expression structure.
- Public `RegexEquation`/`Arden` classes and a public AST would add contracts
  unnecessary for a single equation.
- Accepting nullable coefficients would silently weaken the professor's
  stated uniqueness condition.
- Replacing #54's algebra with the new function could alter its exact
  documented rendering without adding #57 behavior.

## Consequences

The name `solve_arden` is an Automatix design decision, not a name claimed
from the professor's mature implementation. A future #58 system solver may
reuse this one-equation primitive; no system API is created now. The result
retains immutable shared AST subtrees and the union of operand alphabets.

## Related requirements

Implements #57 using #49. #54 remains unchanged. #58-#62 remain TODO.

## Supersedes

None.
