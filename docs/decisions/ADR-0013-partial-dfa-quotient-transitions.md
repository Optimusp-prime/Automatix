# ADR-0013 — Partial DFA quotient transitions

Status: Accepted
Date: 2026-09-24

## Context

Requirements #29 and #30 define equivalence by future acceptance, with a
missing transition interpreted as rejection through an analysis-only trap.
Requirement #32 must minimize reachable real states without exporting that
trap. The professor's quotient recipe reads outgoing transitions from a
representative of each class. For a partial DFA, equivalent members can
nonetheless differ structurally: one can lack a symbol edge while another
has that edge to an empty-language class. Selecting only the member with
the missing edge can make an otherwise reachable quotient class unreachable,
contradicting the required minimal result and the intended quotient of all
reachable classes. No such discrepancy exists for complete DFA.

## Decision

Use a class representative solely for output naming when
`keep_original_names=True`, preferring the original initial state for its
class. For each quotient class and symbol, retain a defined transition if
any member has one. All defined targets must belong to the same equivalence
class; assert this invariant. Missing transitions remain missing when no
member defines the symbol. This is a minimal refinement of the
representative-transition recipe for partial DFA.

Compute classes only after restricting the source to accessible real states.
The completion trap used by #29 is never a public quotient state. This
policy preserves language, keeps each quotient class reachable, and allows
`is_minimal()` to certify the result. The source automaton remains unchanged.

## Alternatives considered

- Read only one arbitrary member's transitions: may make a class unreachable
  even though it was reachable before merging.
- Complete the result and retain the synthetic trap: changes the requested
  partial structure and may add a public state absent from the source.
- Re-run accessibility after choosing arbitrary representatives and discard
  newly unreachable classes: preserves language but needlessly loses a class
  from the accessible-state partition used to construct the quotient.

## Consequences

The output's defined-transition pattern can differ from that of a chosen
single representative, but only where both choices recognize the same
language. Tests cover partial equivalent states with different missing
edges, language preservation, reachable quotient classes and minimality.
The rule also applies when #22 optionally minimizes a complement through
the extension. It does not change ADR-0007 or ADR-0012.

## Related requirements

Implements the partial-DFA edge policy for #32, reusing #29 and #30. It
does not implement any requirement after #32.

## Supersedes

None.
