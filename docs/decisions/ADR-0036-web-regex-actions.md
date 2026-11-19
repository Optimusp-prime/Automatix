# ADR-0036 — Regex actions in the web DFA editor

Status: Accepted design; implementation awaiting verification (2026-11-19).

## Context and decision

User-requested W02 adds three regex conversions and clearing the sheet, without
running tests. The editor remains DFA-only. Expose POST `/api/algorithms/regex`
with `to_regex`, `from_regex`, `from_regex_minimized`, a `draft` and `expression`.
Reuse `ExtendedDFA.to_regex`, `Regex.to_dfa` (derivatives) and `minimize`.
Validate the complete source DFA before conversion. No source mutation or new
mathematical algorithm. Actual constructor and extension contracts were read;
no unavailable professor reference was assumed.

Results are regex text or the existing DFA transport shape. BFS assigns qN names;
grid placement is frontend-only. Alphabet remains explicit. ∅ means empty
language; ε and () mean the empty word. Regex operators are excluded as alphabet
literals to avoid ambiguous conversions. Existing library syntax is retained.

The result panel offers copyable text or an automaton preview before explicit,
undoable replacement. Source changes invalidate results. Clearing retains alphabet
and undo history. Operations delegate immutably to the library.

## Limits and complexity

Conversions may require exponential space/output. Each isolated worker has a
15-second deadline and Linux/WSL 512 MiB memory limit. Input: 120 expression
characters or 12 states for DFA-to-regex. Output: 200 states / 4000 transitions,
or 50000 expression characters. Transport/BFS adds O(Q + E), plus alphabet
sorting. No cache; no server state persistence.

## Pending verification

No tests, builds or servers run at user request. Check epsilon/empty language,
syntax/alphabet errors, incomplete DFA, language equivalence and minimality,
resource errors, stale requests, clear/replace undo and responsive layout.
Implementation is not VERIFIED.

## Supersedes

None. Extends ADR-0033 and ADR-0035.
