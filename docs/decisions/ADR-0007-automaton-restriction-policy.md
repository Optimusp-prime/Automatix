# ADR-0007 — Automaton restriction policy for trim

Status: Accepted
Date: 2026-09-23

## Context

Professor requirement #8 removes states outside `useful_states()` and returns
a new automaton. The prompt-provided reference example equates the result's
states with useful states in an ordinary nonempty case; it does not specify
what to do when no state is useful. The source PDFs were not accessed.

In automata-lib 9.2.0, every concrete FA validates that `initial_state` is
in `states`, so an empty state set is invalid. GNFA also requires a singular
`final_state` in `states` and uses a dense table of regex or None cells.
Concrete constructors differ: DFA has `allow_partial`; NFA destinations are
sets and may include epsilon; GNFA has `final_state` instead of a constructor
argument named `final_states`. Restricting a complete DFA can remove edges
and make the resulting DFA partial.

In the current hierarchy, `type(self)(...)` constructs the corresponding
ExtendedDFA, ExtendedNFA, or ExtendedGNFA. Observed `copy()` and
`input_parameters` work for tested current instances, but generic copying
is unnecessary here; upstream `input_parameters` reads only `self.__slots__`
and a reference warning identifies potential inheritance issues. No global
patch to copying, pickling, or input parameters is introduced.

## Decision

`AccessibilityMixin.trim()` computes useful states once and delegates to a
private `_restrict_to_states` method on each concrete Extended class. This
keeps the public operation at the common FA layer and isolates constructor
and transition representation differences without `isinstance` branches.
There is no public induced-subautomaton API.

For a nonempty useful set, each helper constructs `type(self)(...)` with
exactly those states, the same input symbols and initial state, restricted
final states, and transitions whose endpoints remain in the set. NFA epsilon
keys and destination sets are filtered like other edges. Existing NFA source
rows are preserved, including their absence when upstream permits it. GNFA
retains None-valued cells between kept states to satisfy its table shape,
and passes its singular final state to the constructor.

DFA preserves `allow_partial=True` from the source. If the source is complete
but restriction removes any required symbol edge, the result uses
`allow_partial=True`; otherwise the original value is retained. This is
required by upstream constructor validation and preserves the language.

For an empty useful set, the user explicitly chose a fresh, valid automaton
of the same Extended type that recognizes the empty language:

- DFA: one nonfinal initial state. Preserve `allow_partial`; if complete,
  add a self-loop for each input symbol, otherwise use an empty row.
- NFA: one nonfinal initial state with an empty transition row.
- GNFA: retain the original distinct initial and final states with a
  None-labelled cell from initial to final and no actual edge.

In this exceptional case, `trimmed.states` cannot equal the empty
`useful_states()` result because upstream constructors reject an empty state
set. The returned automaton itself has no useful states. This convention
does not decide the later public `is_trim()` predicate.

Never mutate the source or its transition dictionaries. Return a fresh
automaton even when the source is already trim. Do not use a cache.

## Alternatives considered

- Return a zero-state object: invalid under all three upstream constructors.
- Raise on an empty useful set: explicitly rejected in favor of the user's
  selected language-preserving representation.
- Retain the entire source on the empty case: fails to perform restriction.
- Use `copy()` or generic `input_parameters` reconstruction: does not express
  transition filtering and risks unrelated compatibility behavior.
- Implement trim separately three times: duplicates the shared public
  operation and useful-state analysis.
- Expose `induced_subautomaton()` now: exceeds requirement #8.

## Rationale

The common method expresses the mathematical operation once. Private
concrete reconstruction respects distinct constructor and transition
contracts while preserving the extension type needed for composition.
The empty-language convention reconciles the professor's transformation
requirement with upstream's mandatory structural states.

## Consequences

For valid DFA/NFA, useful-state analysis and reconstruction are
O(|Q| + T) time and O(|Q| + |E|) peak space at constant factors, assuming
constant-time state hashing and equality. Q is all states, E emitted edges,
and T is the cost of exhausting the upstream transition iterator. Complete
DFA empty representatives add one loop per input symbol, already bounded by
T for a valid complete source.

GNFA also revalidates retained regular-expression labels during construction.
Its full time bound is O(|Q| + T + V), with V the upstream freezing and
validation cost, including regex parsing; peak space is O(|Q| + |E| + M),
where M is temporary upstream validation memory. T includes stored None
slots. A small useful subgraph still requires global accessibility scans.

GNFA does not expose word recognition upstream. Its `to_regex()` can be used
for representative nonempty conversion checks; an empty GNFA's absent edge
produces None at runtime despite its upstream str annotation. Upstream NFA
can construct a state named None, but its word-reading path through NetworkX
rejects None as a graph node. Trim supports that state structurally; word
acceptance tests use readable state names. These upstream behaviors are not
patched here.

## Related requirements

Implements #8 only using #7. The private reconstruction helpers may inform
future #19, but no public induced-subautomaton, `is_trim()` (#9), or other
requirement is implemented or advanced.

## Supersedes

None. Complements ADR-0003 and ADR-0005 without changing their decisions.
