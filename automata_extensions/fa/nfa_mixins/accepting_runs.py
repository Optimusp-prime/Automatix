"""Individual accepting runs and their multiplicity for epsilon-free NFAs."""

from collections.abc import Iterator
from typing import cast

from automata.fa.fa import FAStateT
from automata.fa.nfa import NFA


def _validate_run_input(source: NFA, word: str) -> None:
    """Validate eagerly, including epsilon edges in unreachable components."""
    if not isinstance(word, str):
        raise TypeError("word must be a string")
    if any(paths.get("") for paths in source.transitions.values()):
        raise ValueError("accepting-run queries require an epsilon-free NFA")


def _iter_accepting_runs(
    source: NFA, word: str,
) -> Iterator[tuple[FAStateT, ...]]:
    """Iterative DFS over run prefixes, retaining distinct merged histories."""
    path: list[FAStateT] = [source.initial_state]
    if not word:
        if source.initial_state in source.final_states:
            yield tuple(path)
        return

    pending: list[Iterator[FAStateT]] = [
        iter(source.transitions.get(path[-1], {}).get(word[0], ()))
    ]
    while pending:
        try:
            target = next(pending[-1])
        except StopIteration:
            pending.pop()
            path.pop()
            continue

        path.append(target)
        if len(path) == len(word) + 1:
            if target in source.final_states:
                yield tuple(path)
            path.pop()
        else:
            symbol = word[len(path) - 1]
            pending.append(iter(source.transitions.get(target, {}).get(symbol, ())))


class AcceptingRunsMixin:
    """Query accepting state sequences without changing NFA language semantics."""

    def accepting_runs(self, word: str) -> Iterator[tuple[FAStateT, ...]]:
        """Iterate over every accepting run of an epsilon-free NFA on a word.

        Each run is an immutable tuple ``(q0, ..., qn)`` with n input
        characters, the original initial state first and a final state last.
        Distinct histories remain distinct even after merging at a state.
        Transition destinations are sets, so duplicate parallel edges are
        not representable. Enumeration uses iterative depth-first search;
        its order follows destination iteration and is not a sorted-order
        contract. It does not materialize all runs or use a visited set.

        Parameters
        ----------
        word : str
            Input word, possibly empty. A character outside input_symbols
            yields no runs. All validation occurs when this method is called,
            before the returned iterator is consumed.

        Returns
        -------
        Iterator[tuple[FAStateT, ...]]
            An independent lazy iterator. For the empty word, the sole run
            is ``(initial_state,)`` if that state is final; otherwise none.
            The source and its caches are unchanged.

        Raises
        ------
        TypeError
            If word is not a string.
        ValueError
            If any real epsilon edge exists, even in an unreachable component.
            An empty epsilon destination set is allowed. Epsilon elimination
            is not applied: it preserves language, not run multiplicity.

        Complexity
        ----------
        Validation takes O(|Q| + n) expected time. Full enumeration takes
        O(|Q| + n + P + A*(n+1)) time, where P counts explored run-prefix
        extensions, including rejecting ones, and A is the accepting-run
        count. P and A can be exponential in n. The DFS uses O(n+1)
        auxiliary references; each emitted tuple holds n+1 references.
        Collecting the iterator adds O(A*(n+1)) space. State hashing and
        lookup are assumed expected O(1). There is no recursion or cache.

        References
        ----------
        INF302 Enonce_TD.v04, exercise 38; ADR-0028. automata-lib 9.2.0
        NFA.read_input_stepwise merges active states; _get_input_path selects
        one path, so neither implements exhaustive run enumeration.
        """
        source = cast(NFA, self)
        _validate_run_input(source, word)
        if not source.final_states or any(
            symbol not in source.input_symbols for symbol in word
        ):
            return iter(())
        return _iter_accepting_runs(source, word)

    def count_accepting_runs(self, word: str) -> int:
        """Count accepting runs on a word without enumerating their histories.

        Start with multiplicity 1 at the initial state. For each character,
        propagate each active state's multiplicity along its matching edges
        and add contributions at merged destinations. Sum multiplicities of
        final states after the entire word. Counts use exact Python integers.

        Parameters
        ----------
        word : str
            Input word, possibly empty. A character outside input_symbols
            gives zero, as does a missing transition before word completion.

        Returns
        -------
        int
            Number of accepting state sequences, not distinct accepted words.
            The empty word has count 1 exactly when the initial state is
            final. No source data or persistent caches are modified.

        Raises
        ------
        TypeError
            If word is not a string.
        ValueError
            If any real epsilon edge exists, reachable or not. Empty epsilon
            destination sets are allowed. Epsilon removal is not implicit.

        Complexity
        ----------
        O(|Q| + n + sum_i E_i) expected time with unit-cost integer addition,
        where E_i counts matching edges from states active before character
        i. At most two state-count dictionaries are retained, O(|Q|) entries.
        If counts have at most B bits, integer additions cost O(B) and the
        dictionaries require O(|Q|*B) bits for counts, besides state references.
        No path enumeration, determinization, recursion or caching occurs.

        References
        ----------
        INF302 Enonce_TD.v04, exercise 38; ADR-0028. This is the natural-number
        transition recurrence, distinct from DFA.count_words_of_length.
        """
        source = cast(NFA, self)
        _validate_run_input(source, word)
        if not source.final_states or any(
            symbol not in source.input_symbols for symbol in word
        ):
            return 0

        counts: dict[FAStateT, int] = {source.initial_state: 1}
        for symbol in word:
            following: dict[FAStateT, int] = {}
            for state, multiplicity in counts.items():
                for target in source.transitions.get(state, {}).get(symbol, ()):
                    following[target] = following.get(target, 0) + multiplicity
            counts = following
            if not counts:
                return 0
        return sum(
            count for state, count in counts.items() if state in source.final_states
        )
