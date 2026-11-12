# ADR-0029 - Complete DFA construction from normalized regex derivatives

Status: Accepted
Date: 2026-10-16

## Context

After TD38 the user asked to continue the confirmed missing functionality.
TD51.1-3 require both Thompson and a derivative construction. Regex already
has one-symbol derivatives, but no full derivative automaton. Upstream
automata-lib 9.2.0 offers regex -> NFA -> DFA rather than this construction;
no public name collision was found. The mature reference documents no
direct derivative builder. Existing ADR-0015 keeps its syntax and API.

Raw structural derivative equality is insufficient for repeated exploration:
unions can reassociate, reorder and repeat terms. Regex.__str__ is also
not a lossless serialization: an internal empty language and the literal
empty-set glyph can both display as the same string.

## Decision

Expose Regex.to_dfa() -> ExtendedDFA without new parameters. Its alphabet
is the frozen alphabet already validated by Regex. Keep this conversion
at the regex layer rather than a mixin over unrelated automaton classes.

A private normalization module recursively flattens unions, deduplicates
their terms structurally and orders them by their unambiguous dataclass
representation. Concatenations flatten without reordering; existing AST
smart constructors handle epsilon/empty identities and trivial stars.
Apply normalization to the initial AST and to every computed derivative.
No semantic language-equivalence oracle or global cache is introduced.
Existing Regex.derivative and display outputs are not changed.

Run BFS over normalized ASTs. Each concrete state is an immutable Regex
value with the original alphabet. For every state and alphabet character,
call its derivative method and intern the normalized resulting AST within
this call. Mark a state final using the existing AST nullable predicate.
The returned ExtendedDFA is complete and has only reachable states. Include
the empty-language sink exactly when reachable. Minimality is not promised;
the existing minimize() remains available.

The finite-similarity argument is the classical derivative construction:
associative, commutative and idempotent union canonicalization suffices for
finite exploration for classical regular expressions; the additional
identities preserve language. See Owens, Reppy and Turon (2009), section
4.1, https://doi.org/10.1017/S0956796808007090. This is a termination argument,
not a polynomial-state or minimality guarantee.

## Alternatives considered

- Convert through Thompson or subset construction: produces a DFA but
  does not supply the independently requested derivative algorithm.
- Compare raw ASTs: misses union similarity and risks unbounded syntax
  growth despite finitely many language quotients.
- Compare rendered strings: conflates empty-language nodes and literals.
- Replace every existing smart constructor: changes existing observable
  derivative and conversion outputs beyond the authorized feature.
- Public nullable/simplify APIs or semantic minimization during discovery:
  unnecessary contracts and algorithms for the selected construction.

## Consequences

For R reachable states and s symbols the graph has R*s edges. Track all
AST transformation, ordering, hashing/equality and nullability costs C
explicitly; time is O(s log s + R*s + C + V), including constructor V.
Space is O(R*(s+1)+S+W+V_space), with retained AST size S and temporary
workspace W. State counts and expression sizes can be exponential; the
existing recursive AST operations retain Python's depth limits.

Tests cover all TD51 expressions, equivalence with independent automata-lib
and existing Thompson construction, every transition's quotient rule,
nullable final states, reachable completeness, empty alphabets/languages,
Unicode, ambiguous/reordered unions, sink identity, immutable fresh results,
unchanged derivative renderings and composition with existing transformations.
Mocks ensure no Thompson or subset algorithm is used by the builder.

## Related requirements

Supplemental TD51, existing #49 derivatives and #51 Thompson construction.
See [usage](../DERIVATIVE_DFA.md).

## Supersedes

None. Complements ADR-0015 without changing its accepted contracts.
