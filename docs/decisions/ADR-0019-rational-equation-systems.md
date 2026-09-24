# ADR-0019 — Rational equation-system API and epsilon-NFA policy

Status: Accepted
Date: 2026-09-24

## Context

Professor requirement #58 asks to solve a rational-language equation system
associated with an automaton. The supplied mature executable reference only
exposes the DFA-specific `to_regex_arden()` of #54, not a standalone public
system API. Requirement #57 supplies one-equation `solve_arden(Regex, Regex)`
and deliberately rejects nullable coefficients to retain Arden's
unique-solution form. Epsilon-NFA edges can create nullable pivots, whereas
ordinary consuming edges cannot.

## Decision

Automatix introduces the immutable `SystemOfEquations` in
`automata_extensions.equations`. Its explicit ordered variables are arbitrary
hashable objects; sparse coefficient rows and one constant per variable hold
#49 `Regex` values. Caller mappings are copied behind read-only views.
`solve() -> Mapping[Variable, Regex]` returns a read-only solution for every
declared variable, using deterministic ordered Arden elimination and
back-substitution. A missing coefficient denotes the private empty-language
AST node. An effective nullable diagonal raises `ValueError` identifying the
variable. The result retains the union of operand alphabets.

`ExtendedDFA.to_equation_system()` and `ExtendedNFA.to_equation_system()`
construct one equation for **every** state, including inaccessible states,
using actual state objects as variables. Each consuming edge contributes a
literal coefficient; final states contribute epsilon. Partial DFA transitions
contribute no term. The NFA method first calls #37's
`remove_epsilon_transitions()` when real epsilon edges exist. That
transformation preserves the state set and language while making every
coefficient consuming, so the system remains in the unique-solution domain.
The original NFA is unchanged.

The solver and the one-equation #57 function share a private nullable-pivot
check and star constructor. Symbolic system elimination still needs its own
coefficient and substitution logic because unresolved variable terms are
not a `Regex` constant acceptable to `solve_arden`.

These public names and the epsilon normalization policy are Automatix design
decisions, not claims about an unavailable mature standalone API.

## Alternatives considered

- Calling #54 or upstream GNFA conversion would not expose all state
  solutions and would not be an independent system solver.
- Refactoring #54 to use this AST solver would risk its verified exact mature
  string `b*(ab*a((ab*ab*a|b))*ab*|())`; it remains untouched.
- Taking a least solution for nullable pivots would weaken #57's adopted
  unique-solution contract.
- Rejecting all epsilon-NFAs would ignore the verified, state-preserving
  epsilon-removal operation already available in #37.
- Public `RegexSolver` or per-row `RationalEquation` classes would add API
  without source evidence or necessity for #58.

## Consequences

The solver is reusable on caller-built systems. NFA-generated equations
describe the equivalent epsilon-free normalization, not the literal epsilon
transition table. All original state identities remain available as keys.
Regex coefficients inherit #49's single-character alphabet representation.
Rendering an internal empty language as `∅` remains diagnostic rather than
reparsable syntax. Elimination performs up to cubic algebraic updates, but
AST comparisons and rendered expression growth can be exponential.

## Related requirements

Implements #58, reusing #37, #49 and the private precondition from #57.
#54 remains independent. #59-#62 remain TODO.

## Supersedes

None.
