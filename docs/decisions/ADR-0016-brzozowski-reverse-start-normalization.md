# ADR-0016 — Normalize the reverse start for Brzozowski minimization

Status: Accepted
Date: 2026-09-24

## Context

Professor requirement #50 specifies minimization by reversing and
determinizing twice. The supplied mature example evaluates
`d.brzozowski_minimize() == d.minimize()` to `True`. In automata-lib 9.2.0,
an NFA has one initial state. The verified #36 `reverse()` therefore adds a
fresh, epsilon-only initial state pointing to the old final states. The
verified #35 `determinize()` includes that fresh state in the initial
epsilon-closed subset. For the mature three-state DFA, direct composition
produces four states, including two equivalent subsets, and is not minimal.
The one-state universal DFA similarly produces two equivalent states.
Upstream DFA equality compares languages, so the mature equality example
alone does not expose this duplicate.

## Decision

Keep the public #35 and #36 behavior unchanged. Introduce a private helper
used only by #50 after each `reverse().determinize()` stage. It takes the
initial state of that exact reverse result and removes only its identity
from determinized subset labels. If the logical subset already exists, the
two representations merge. Their transitions and finality must agree;
otherwise the helper fails rather than performing broader equivalence
merging. Rebuild a fresh ExtendedDFA with the same alphabet and partiality
policy. Apply this helper twice in the classical reverse/determinize/
reverse/determinize sequence. Do not invoke ordinary `minimize()`.

Expose `BrzozowskiMixin.brzozowski_minimize()` on ExtendedDFA and ExtendedNFA,
both of which already support `reverse()`; exclude regex-labeled GNFA.

## Alternatives considered

- Append `minimize()`: masks the representation problem and does not
  implement the prescribed independent algorithm.
- Change #35 or #36: their separate public contracts and tests are correct.
- Merge arbitrary equivalent states: introduces general minimization inside
  the Brzozowski path.
- Parse or guess a fresh state's name: unsafe with heterogeneous state types.

## Rationale

The reverse-created initial state is fresh, has only epsilon edges to the
logical reversed initial set, has no incoming edge, and is not accepting.
It therefore cannot appear after consuming a symbol. Removing it from
subset identity changes neither future transitions nor acceptance. The
normalization matches the classical reversal with a *set* of initial states
while preserving the existing single-initial NFA representation elsewhere.

## Consequences

The two determinization stages can each discover exponentially many states
in their input NFA; the second input may already be exponentially larger
than the original. The private normalization adds a reconstruction pass
over each determinized DFA and invokes constructor validation. No caching,
new public determinization option or general minimization is introduced.
Tests assert actual `is_minimal()`, not only language equality, on DFA/NFA,
partial and empty-language examples. The source automata remain unchanged.

## Related requirements

Implements the representation bridge for #50 using #35 and #36. #49 regex
derivatives are separate and unchanged. #51 and later remain TODO.

## Supersedes

None. Complements the accepted reversal and determinization contracts.
