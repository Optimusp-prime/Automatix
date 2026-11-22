# ADR-0039 — Greedy AST state elimination for larger automata

Status: Accepted and verified (2026-11-22).

## Context

The web editor refused DFA-to-regex conversion above 12 states (ADR-0036).
Measurements on complete, strongly connected DFAs showed that computation
time was never the bottleneck (under 1.5 s at 18 states). The problem was the
output of the #53 engine: lexical elimination order with no simplification,
built by copying strings. At 18 states and 3 symbols it produced 14.4 million
characters, far above the 50 000-character web cap.

Alternatives examined:

- upstream `GNFA.to_regex()` (inherited as #39): degree-based order, about
  1000 times shorter, but it emits `?`, which the #49 `Regex` parser used by
  the editor rejects, so a copied result could not be pasted back;
- changing `to_regex()` (#53): rejected, since its verbose lexical trace is
  the VERIFIED professor contract.

## Decision

Add `to_regex_heuristic() -> str | None` through `HeuristicRegexMixin`
(`fa/fa_mixins/regex_heuristic.py`), mounted on `ExtendedDFA` and
`ExtendedNFA`. It relies only on `useful_states()` and upstream
`iter_transitions()` (NFA epsilon `""` becomes the empty word). It is not
mounted on `ExtendedGNFA`, whose labels are already regex strings and whose
upstream `to_regex()` stays as is.

- Keep useful states only; add fresh entry/exit endpoints.
- Remove the state of smallest Delgado–Morais weight; break ties with the #53
  lexical key, so results are deterministic.
- Labels are immutable #49 AST nodes with O(1) size and nullability. The
  existing smart constructors apply ∅/ε identities, nested-star and duplicate
  union removal. Two local union rules are added: ε is absorbed by a nullable
  operand, and ε | x x* (or x* x) becomes x*. The shared `_ast` constructors
  are not modified, so derivative normal forms (#49, TD51) are unchanged.
- Subtrees are shared, so internal space is O(n³) nodes; only the final
  rendering can be exponential, which is unavoidable for some languages.
- The return conventions are those of `to_regex()`: `None` for the empty
  language, `""` for {ε}. The rendered syntax is the #49 syntax.

The web worker now computes `dfa.minimize().to_regex_heuristic()`. The
12-state input limit is removed (the editor's 200-state limit remains), and
the output cap rises from 50 000 to 1 000 000 characters, with an error that
reports the actual length. Memory errors return a neutral message.

## Consequences

- 18 dense states with 3 symbols: about 31 000 characters in 20 ms, instead of
  14.4 million; 200-state structured automata convert in about a second.
- Dense random automata of 40 or more states can still exceed the cap; this
  reflects regex size lower bounds rather than a fixable limit.
- The web result is no longer the #53 lexical trace. That trace remains
  available in the library through `to_regex()`.
- No minimum-size regex is claimed. No cache is introduced.

## Supersedes

ADR-0036, section "Limits and complexity", for the DFA-to-regex input limit
(12 states) and output limit (50 000 characters). The rest of ADR-0036 stays
in force.
