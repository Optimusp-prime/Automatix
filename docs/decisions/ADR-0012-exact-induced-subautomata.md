# ADR-0012 — Exact induced subautomata

Status: Accepted
Date: 2026-09-23

## Context

Professor requirement #19 defines a subautomaton induced by a requested
state set, with exactly those states and only transitions internal to it.
The supplied mature reference names `induced_subautomaton` in
SubautomatonMixin. The professor PDFs were not available. ADR-0007 already
establishes concrete `_restrict_to_states` helpers for trim, including a
special empty-language representation that retains mandatory structural
states when no useful state exists. That exception would violate #19's
exact-set contract if applied to an empty request.

automata-lib 9.2.0 requires the initial state in every concrete automaton;
GNFA also requires its distinct final state and a dense transition table.
Restricting a complete DFA can remove required edges and make it partial.

## Decision

Expose `induced_subautomaton(states)` in a common SubautomatonMixin through
ExtendedFA. Materialize the input iterable once as a frozenset. Reject
unknown or unhashable states, an empty request, and any request omitting the
initial state with upstream InvalidStateError. The GNFA reconstruction
helper explicitly rejects a request omitting its final state.

For a valid request, delegate to the existing concrete
`_restrict_to_states` helper, which constructs a fresh same-type Extended
automaton over exactly the requested states and filters transitions and
final states according to its upstream representation. Declare that
private reconstruction contract abstractly on ExtendedFA for consistent
typing; each concrete extension already implements it. Upstream constructor
validation remains authoritative for any further representation invariant.

Do not invoke the empty-set branch used by trim: validation rejects that
request before reconstruction. Do not change trim or ADR-0007.

## Alternatives considered

- Reuse trim's empty-language representative for an empty request: adds
  states absent from the requested set and violates exact induction.
- Silently retain initial or GNFA final states: also violates the contract.
- Reimplement DFA/NFA/GNFA transition filtering in the new mixin: duplicates
  the accepted concrete helpers and blurs representation boundaries.
- Use generic copy or input_parameters: does not filter transitions and
  carries the compatibility risk recorded in ADR-0007.

## Rationale

The public method expresses common set validation once, while the concrete
helpers preserve upstream-specific construction rules. A rejected request
is clearer than returning an object with more states than requested.

## Consequences

For every successful call, `result.states == frozenset(states)`, the result
is a new instance of the same Extended concrete type, and the source is
unchanged. DFA restriction may set `allow_partial=True`; NFA epsilon edges
are filtered without closure computation; GNFA retains None cells and
remaining regex labels. The result may have no final states for DFA/NFA.

Materialization, validation, filtering and upstream reconstruction cost
O(|Q| + T + V) time as a conservative bound, where T covers examined
transition entries and V is constructor validation (including GNFA regex
checks). Memory is proportional to the request, retained transition table
and upstream validation structures. No cache is introduced.

## Related requirements

Implements #19 only. Reuses ADR-0003 and ADR-0007. Completeness testing (#20)
and completion (#21) remain separate requirements; no sink state is added.

## Supersedes

None. The trim empty-language exception in ADR-0007 remains unchanged.
