# ADR-0023 — Read-only distinguishability round table

Status: Accepted
Date: 2026-09-27

## Context

Primary #29 requires iterative marking of distinguishable DFA state pairs.
The mature documentation adds a complete pair table with marking rounds,
but does not specify the public return type of `pair_table()`. Existing
`distinguishable_states()` returns a set of frozenset pairs and does not
retain rounds. Primary #29 and #30 must preserve their verified semantics.

## Decision

Use one private reverse-dependency breadth-first table-filling engine for
both the original query and the new API. A final/nonfinal pair enters at
round 0. If a symbol leads from a pair to a round-r pair, that pair can
enter at round r+1. Breadth-first processing records its first, shortest
distinguishing-word length. A missing mark denotes equivalent states.

`pair_table() -> Mapping[frozenset[FAStateT], int | None]` returns every
unordered pair of original states, including equivalent and inaccessible
ones. Keys are inserted in a deterministic state-label order and the
mapping is protected by MappingProxyType. For a partial DFA, the
completion sink participates in the private analysis but never becomes
a public pair key. `distinguishable_states()` keeps its existing set
return type and is exactly the subset with non-None rounds.

`pair_table_str(show_round=True) -> str` renders a triangular ASCII
table with no terminal newline. Its header has one leading space for
one-character state labels, matching the exact string explicitly
requested for M3. The mature PDF prints three leading spaces in that
same line; the prompt's later, explicit expected output controls this
presentation-only discrepancy. With `show_round=False`, marked
pairs display `X`; unmarked pairs display `.` in both modes.
`print_pair_table(show_round=True) -> None` prints that same string
and a newline. A one-state DFA has no table cells and renders as the
empty string. Arbitrary heterogeneous state labels use the same
deterministic ordering key as the public mapping.

## Alternatives considered

- Return a mutable dict: callers could change an analysis result and
  mistake it for automaton state.
- Return only marked pairs: loses equivalent-pair information needed for
  a complete triangular view.
- Run separate analyses: duplicates #29's algorithm and can disagree on
  partial DFA semantics.
- Reproduce the PDF's three-space header: differs from the task's
  explicit one-space expected string; the mathematics and cells agree.

## Consequences

The shared analysis uses O(|Q|² * |Sigma| + V + |Q| log |Q|)
expected time and O(|Q|² * |Sigma| + M) space, where V/M account for
completion and validation. Round numbers are deterministic, independent
of hash-set iteration order. Formatting adds O(R) time and memory for R
rendered characters; printing adds O(R) output work.

## Related requirements

M2–M4 and primary #29–#30.

## Supersedes

None.
