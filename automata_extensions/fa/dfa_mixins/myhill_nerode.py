"""Distinct left quotients of a deterministic automaton language."""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, cast

from automata.fa.fa import FAStateT

if TYPE_CHECKING:
    from automata_extensions.fa.dfa import ExtendedDFA


class MyhillNerodeMixin:
    """Construct language quotients from reachable state-right-languages."""

    def myhill_nerode_quotients(self) -> tuple[ExtendedDFA, ...]:
        """Return one automaton for each distinct left quotient of the language.

        A word's quotient is the right-language of its reached state. Reuse
        ``equivalence_classes`` to merge equal right-languages, but retain
        only classes reached from the initial state. A missing transition in
        a partial DFA denotes the empty quotient. It is included once only
        when no reachable explicit state already has empty right-language.
        Unlike ``equivalence_classes``, this is a language-level collection,
        not a partition of all stored states. The source is unchanged.

        Returns
        -------
        tuple[ExtendedDFA, ...]
            Fresh DFA representations of distinct quotients. The source
            language is first; other explicit quotients follow shortest BFS
            witnesses, with symbols visited in sorted order. A new implicit
            empty quotient, if needed, is last.

        Complexity
        ----------
        Expected O(|Q|²|Sigma| + |Q|² alpha(|Q|) +
        |Sigma| log |Sigma| + |Q| + T + k(|Q| + T + V)) time and
        O(|Q|²|Sigma| + |Q| + |E| +
        k(|Q| + T + M)) space. Q is the original state set, Sigma the
        alphabet, T the transition-scanning cost, E its edges, and k the
        number of returned quotients (at most |Q| + 1). V/M bound each
        delegated quotient constructor's validation time/memory. The first
        terms include #30's pair analysis and the existing coaccessibility
        traversal; the k term accounts for materializing full DFA copies.
        Assumes constant-time hash and transition lookup.

        References
        ----------
        Professor requirement #59; Automatix ADR-0020. Reuses requirements
        #30 and #47 without changing their public contracts.
        """
        source = cast("ExtendedDFA", self)
        classes = source.equivalence_classes()
        class_of = {state: group for group in classes for state in group}
        symbols = sorted(source.input_symbols)

        witnesses: dict[FAStateT, str] = {source.initial_state: ""}
        pending: deque[FAStateT] = deque((source.initial_state,))
        represented: set[frozenset[FAStateT]] = set()
        quotient_witnesses: list[str] = []
        missing_witness: str | None = None

        while pending:
            state = pending.popleft()
            witness = witnesses[state]
            group = class_of[state]
            if group not in represented:
                represented.add(group)
                quotient_witnesses.append(witness)

            paths = source.transitions.get(state, {})
            for symbol in symbols:
                next_witness = witness + symbol
                if symbol not in paths:
                    if missing_witness is None:
                        missing_witness = next_witness
                    continue
                target = paths[symbol]
                if target not in witnesses:
                    witnesses[target] = next_witness
                    pending.append(target)

        if missing_witness is not None:
            coaccessible = source.coaccessible_states()
            if all(state in coaccessible for state in witnesses):
                quotient_witnesses.append(missing_witness)

        return tuple(source.left_quotient_word(word) for word in quotient_witnesses)
