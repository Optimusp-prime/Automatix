# ADR-0017 — Right-linear grammar conversion preserves language semantics

Status: Accepted
Date: 2026-09-24

## Context

Professor requirement #55 specifies conversion between finite automata and
right-linear regular grammars, using productions `A -> wB` or `A -> w`, with
the same recognized/generated language. The supplied mature executed
extension returns `False` for
`ExtendedNFA.from_grammar_string("S -> aS | b").accepts_input("aab")`.
No documented parser convention or mature source code was available that
explains this result.

The classical derivation is `S -> aS -> aaS -> aab`, so `aab` belongs to
the grammar's language `a*b` under the professor's stated definition.

## Decision

Apply the project source-precedence rule: the primary professor specification
and its right-linear language semantics prevail over this conflicting mature
observable. Parse `aS` as terminal word `a` followed by declared nonterminal
`S`; convert the recursive rule into an NFA loop and `S -> b` into a terminal
edge to an accepting state. Therefore the extended NFA accepts `aab`.

Keep the mature public names `to_grammar`, `from_grammar`,
`from_grammar_string` and the concrete public type name `Grammar`.
Represent productions structurally as immutable `(head, word, target)`
triples, where `target=None` distinguishes terminal-only rules and an empty
word denotes epsilon. Share automaton-to-grammar conversion across DFA and
NFA, excluding regex-labeled GNFA. Build the reverse conversion on NFA,
expanding multi-character terminal words into one edge per character.

## Alternatives considered

- Copy the mature `False` result: contradicts the stated grammar derivation
  and fails to preserve the generated language.
- Guess an undocumented parser convention that makes `aab` invalid: there is
  no available source evidence for such a convention.
- Convert through regular expressions: unnecessary and obscures the direct
  state/nonterminal and transition/production association.

## Consequences

`from_grammar_string("S -> aS | b").accepts_input("aab")` returns `True`
in Automatix, an intentional observable divergence from that one mature
example. This record does not claim to know the mature implementation's
internal cause. The unambiguous mature `type(d.to_grammar()).__name__ ==
"Grammar"` result remains a compatibility test.

Structural grammars can express epsilon, unit, terminal-only and longer-word
rules without textual ambiguity. The small text format uses `()` for epsilon,
the project's existing regex spelling; it discovers LHS declarations first,
chooses the longest declared suffix as a continuation, and rejects an
undeclared uppercase trailing nonterminal. Its first LHS is the start.

## Related requirements

Implements #55 only. Derivation trees (#56) and other grammar-hierarchy
features remain separate. No upstream source is modified.

## Supersedes

None.
