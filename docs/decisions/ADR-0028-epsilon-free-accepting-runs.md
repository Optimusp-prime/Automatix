# ADR-0028 - Accepting runs of epsilon-free NFAs

Status: Accepted
Date: 2026-10-16

## Context

INF302 Enonce_TD.v04 exercise 38 asks to list accepting executions and
compute N(A,u), their count for one input word. The user selected this
feature after a coverage audit and explicitly accepted starting without
epsilon transitions. It is supplemental TD work, not a change to the
professor requirements numbered #1-#62 or previously verified features.

automata-lib 9.2.0 has no colliding accepting_runs/count_accepting_runs API.
NFA.read_input_stepwise merges active states; _get_input_path selects one
path. DFA.count_words_of_length counts words, not executions. None can
implement this contract by delegation. The mature reference contains no
documented accepting-run API to reproduce.

## Decision

Expose AcceptingRunsMixin on ExtendedNFA only, before the upstream NFA:

- accepting_runs(word: str) -> Iterator[tuple[FAStateT, ...]]
- count_accepting_runs(word: str) -> int

A run contains the initial state and one state per consumed character,
ending in an original final state. Destination sets contain no parallel
copies of an identical edge; runs are distinguished by their state history.
An empty word has exactly one accepting run if the initial state is final.
Unknown characters and dead ends yield no runs/count zero.

Validate the string and absence of real epsilon edges eagerly, even for
unreachable edges and empty words. Raise TypeError for a non-string and
ValueError for an epsilon edge. An empty epsilon destination set is not an
edge. Do not automatically eliminate epsilon transitions: language
equivalence does not preserve the number of execution paths.

Use iterative DFS for lazy enumeration, with an iterator stack and a
single mutable local prefix; yield immutable tuple snapshots. Never merge
histories or sort heterogeneous state names. Destination iteration order
is deliberately not a stable-order API. Every call has independent state.

Count using the natural-number recurrence c_0(initial)=1 and
c_(i+1)(r)=sum(c_i(q) for each q --word[i]--> r). Keep only the current
and next dictionaries. Sum over final states after consuming the word.
Python integers preserve exact large multiplicities. Neither query mutates
the automaton, populates a persistent cache, determinizes or calls the
other query.

## Alternatives considered

- Count by enumerating runs: exponential even when dynamic programming
  needs only a small active-state set.
- Use active-state sets: loses multiplicity when branches merge.
- Memoize a recursive counter: introduces recursion limits and unnecessary
  state/history storage; a two-layer recurrence is simpler.
- Support epsilon paths now: cycles can produce infinitely many runs and
  require another mathematical contract, outside the agreed first scope.
- Put the feature in ExtendedFA: deterministic targets and regex-labelled
  GNFA edges require different semantics; this API is specifically NFA.

## Consequences

Enumeration can be exponential because its output is exponential. It
validates in O(|Q|+n), then takes O(P+A*(n+1)) time for explored prefix
extensions P and A accepted runs. DFS auxiliary references are O(n+1);
retaining the output requires O(A*(n+1)) additional references.

Counting takes O(|Q|+n+sum_i E_i) with unit-cost arithmetic, for matching
edges E_i from each active layer. It retains O(|Q|) integer entries.
Arbitrary-precision additions cost O(B) for B-bit counts; integer storage
can take O(|Q|*B) bits besides state references. All lookup bounds assume
expected constant-time hashing. No algorithm-result cache is introduced.

Tests check the exercise-38 occurrence identity and product-square law,
independent exhaustive state-sequence enumeration, merged branches,
empty words/languages, dead ends, heterogeneous/None states, epsilon
rejection, immutability, iteration independence and long words. Upstream
NetworkX rejects None as a node during NFA simulation; the independent
language check for that fixture uses the existing determinization, without
changing upstream or the recognition API.

## Related requirements

Supplemental TD38; existing #16 execution trace and #43 NFA intersection.
See [usage and mathematical contract](../ACCEPTING_RUNS.md).

## Supersedes

None.
