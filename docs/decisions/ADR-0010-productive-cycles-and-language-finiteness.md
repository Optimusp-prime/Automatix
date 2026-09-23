# ADR-0010 — Productive cycles and language finiteness

Status: Accepted
Date: 2026-09-23

## Context

Professor requirement #14 describes infinite-language decision through a
cycle that is accessible and coaccessible. The supplied reference excerpts
call this a useful cycle and name `is_finite()`. The source PDFs were not
available. Requirements #3, #5, #7 and #10 already provide useful states and
strongly connected components; ADR-0009 provides graph-cycle analysis.

Literal unlabeled graph cycles are insufficient for real NFA language
finiteness. A one-state accepting NFA with only an epsilon self-loop has a
useful cycle but recognizes only the empty word. The user explicitly chose
real language finiteness: a useful cycle must be able to add positive word
length. A GNFA can also recognize an infinite language without any state
cycle, for example a sole edge labeled `a*` from initial to final. The user
chose to defer GNFA regex-label finiteness and limit the guarantee to DFA/NFA.

## Decision

Expose `is_finite() -> bool` in CycleMixin for ExtendedDFA and ExtendedNFA.
Compute useful states, then the existing SCC partition. The language is
infinite exactly when a transition consuming an input symbol has both ends
in the same useful SCC. An NFA epsilon transition has label `""` and does
not by itself make a cycle productive. DFA transitions consume symbols.

An edge inside an SCC belongs to a directed cycle; an edge with a nonempty
label makes that cycle repeatable with positive word length. A useful SCC
lies on an initial-to-final path. This is the semantic refinement of the
professor's accessible-and-coaccessible cycle criterion.

ExtendedGNFA overrides `is_finite()` to raise NotImplementedError. Returning
a graph-only boolean would misstate regex-label semantics. No GNFA
conversion or regex-finiteness analyzer is added in this requirement. Do
not call upstream `isfinite()`, rebuild with `trim()`, add caching, or change
the public behavior of `has_cycle()` and `has_cycle_from()`.

## Alternatives considered

- Apply `not has_cycle()` to the whole graph: dead or unreachable cycles
  yield false positives, as do useful epsilon-only NFA cycles.
- Run DFS on useful states without filtering edges: it can enter a dead
  cyclic branch from a useful state.
- Inspect only labels on DFS back edges: a consuming edge inside an SCC
  may be a forward or cross edge, while the discovered back edge is epsilon.
- Use GNFA's state graph alone: an acyclic edge labeled `a*` already
  describes an infinite language. Converting regex labels through upstream
  automata was deferred by the user's explicit scope choice.

## Rationale

The SCC partition expresses exactly which edges can be repeated on a
cycle, while labels decide whether repetition can lengthen a word. Reusing
the verified SCC analysis avoids a third cycle algorithm and preserves the
existing graph traversal contracts. The GNFA override makes the unsupported
case explicit instead of returning an unreliable result.

## Consequences

Let Q be all states, E emitted transitions and T the cost of exhausting
`iter_transitions()`. Useful-state analysis, SCC construction and one label
scan each cost O(|Q| + T) time and O(|Q| + |E|) peak space; their combination
has the same asymptotic bounds at constant factors, assuming constant-time
state hashing and equality. Recursive Tarjan retains Python's recursion
limit. The method does not mutate or cache automata.

For GNFA, callers receive NotImplementedError even for simple labels.
Semantic finiteness of regex-labeled GNFA edges remains a separate design
task requiring explicit scope. The #14 guarantee is complete for DFA/NFA.

## Related requirements

Implements #14 for ExtendedDFA and ExtendedNFA. The GNFA limitation is
explicit and does not implement any conversion, word-recognition method,
`is_infinite()` alias, or other professor requirement.

## Supersedes

None. Complements ADR-0005, ADR-0008 and ADR-0009 without rewriting them.
