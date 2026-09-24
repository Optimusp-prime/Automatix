"""State morphisms, symbol projections, and state-map quotients for DFA/NFA."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, cast

from automata.fa.dfa import DFA
from automata.fa.fa import FAStateT
from automata.fa.nfa import NFA

if TYPE_CHECKING:
    from automata_extensions.fa.nfa import ExtendedNFA


class MorphismMixin:
    """Preserve labeled edges while mapping states or input symbols."""

    def is_morphism_to(
        self, other: DFA | NFA, state_map: Mapping[FAStateT, FAStateT]
    ) -> bool:
        """Test whether a total state map preserves initial, final and edges.

        The alphabets must agree. A source final must map to a target final,
        but the converse is not required. Every source edge, including NFA
        epsilon edges, must have its mapped counterpart in the target.
        Extra target edges and undefined source DFA transitions are allowed.
        Invalid state maps return False. Neither automaton is modified.

        Parameters
        ----------
        other : DFA | NFA
            Target automaton, deterministic or nondeterministic.
        state_map : Mapping[FAStateT, FAStateT]
            Proposed image for every source state, with no extra keys.

        Returns
        -------
        bool
            Whether the mapping is an edge-preserving automaton morphism.

        Complexity
        ----------
        Expected O(|Q_A| + |Q_B| + M + |Sigma_A| + |Sigma_B| + T_A + T_B)
        time and O(M + |E_B|) auxiliary space. M is mapping size; T_A/T_B
        scan the source/target transition tables, including empty NFA
        destination entries, and E_B counts individual target edges.
        Target edges are materialized once for expected constant-time
        membership tests. State hashing is assumed constant-time.

        References
        ----------
        Professor requirement #61; supplied mature ``is_morphism_to``
        example; Automatix ADR-0021 defines forward-only preservation.
        """
        source = cast(DFA | NFA, self)
        if not isinstance(other, (DFA, NFA)):
            return False
        if source.input_symbols != other.input_symbols:
            return False
        if set(state_map) != source.states:
            return False
        try:
            if any(image not in other.states for image in state_map.values()):
                return False
        except TypeError:
            return False
        if state_map[source.initial_state] != other.initial_state:
            return False
        if any(state_map[state] not in other.final_states for state in source.final_states):
            return False

        target_edges = set(other.iter_transitions())
        return all(
            (state_map[source_state], state_map[target_state], symbol)
            in target_edges
            for source_state, target_state, symbol in source.iter_transitions()
        )

    def project(self, symbol_map: Mapping[str, str | None]) -> ExtendedNFA:
        """Relabel each input symbol, with None erasing it into epsilon.

        The map covers exactly the source alphabet. Images are single input
        characters or None. The result keeps states, initial and finals;
        collisions union all destination states. Existing NFA epsilon edges
        remain epsilon edges. A fresh ExtendedNFA is returned even when the
        projection happens to be deterministic. The source and map are not
        changed.

        Parameters
        ----------
        symbol_map : Mapping[str, str | None]
            Total map from source input symbols to one-character target
            symbols or None for epsilon.

        Returns
        -------
        ExtendedNFA
            NFA over exactly the non-None symbol images.

        Raises
        ------
        ValueError
            If the map domain differs from the source alphabet or an image
            is not a single-character string or None.

        Complexity
        ----------
        Expected O(|Q| + |Sigma| + M + T + V) time and
        O(|Q| + |Sigma| + |E| + W) space, including the new automaton.
        M is map size, T scans all transition-table entries, E counts
        individual emitted edges, and V/W are upstream NFA construction
        and validation time/memory. Hashing is assumed constant-time.

        References
        ----------
        Professor requirement #61; supplied mature ``project`` example;
        Automatix ADR-0021. NFA epsilon is the upstream empty-string label.
        """
        from automata_extensions.fa.nfa import ExtendedNFA

        source = cast(DFA | NFA, self)
        if set(symbol_map) != source.input_symbols:
            raise ValueError("symbol_map must cover exactly the input alphabet")

        alphabet: set[str] = set()
        for image in symbol_map.values():
            if image is None:
                continue
            if not isinstance(image, str) or len(image) != 1:
                raise ValueError("projected symbols must be one character or None")
            alphabet.add(image)

        transitions: dict[FAStateT, dict[str, set[FAStateT]]] = {
            state: {} for state in source.states
        }
        for start, end, symbol in source.iter_transitions():
            if symbol == "":
                mapped_symbol = ""
            else:
                image = symbol_map[symbol]
                mapped_symbol = "" if image is None else image
            transitions[start].setdefault(mapped_symbol, set()).add(end)

        return ExtendedNFA(
            states=source.states,
            input_symbols=alphabet,
            transitions=transitions,
            initial_state=source.initial_state,
            final_states=source.final_states,
        )

    def quotient_by(self, state_map: Mapping[FAStateT, FAStateT]) -> ExtendedNFA:
        """Merge source states by a total map, retaining every mapped edge.

        The result states are exactly the image of the map. The initial
        state is mapped, and an image is final when any source final maps
        to it. Non-congruent merges are allowed: mapped destinations on
        the same symbol are unioned in an NFA, including epsilon edges.
        No completion, determinization or minimization is performed.
        The source and map are not modified.

        Parameters
        ----------
        state_map : Mapping[FAStateT, FAStateT]
            Total mapping of source states to hashable quotient labels.

        Returns
        -------
        ExtendedNFA
            Fresh state-fusion automaton over the source alphabet.

        Raises
        ------
        ValueError
            If the mapping domain is not exactly the source state set or
            an image is unhashable.

        Complexity
        ----------
        Expected O(|Q| + M + T + V) time and O(|Q| + |E| + W) space,
        including the result. M is map size, T scans source transition
        entries, E counts individual emitted edges, and V/W are upstream
        NFA construction and validation time/memory. Expected constant-
        time state hashing and edge insertion are assumed.

        References
        ----------
        Professor requirement #61; supplied mature ``quotient_by``
        example; Automatix ADR-0021 on non-congruent merges.
        """
        from automata_extensions.fa.nfa import ExtendedNFA

        source = cast(DFA | NFA, self)
        if set(state_map) != source.states:
            raise ValueError("state_map must cover exactly the source states")
        try:
            images = set(state_map.values())
        except TypeError as exc:
            raise ValueError("mapped state labels must be hashable") from exc

        transitions: dict[FAStateT, dict[str, set[FAStateT]]] = {
            state: {} for state in images
        }
        for start, end, symbol in source.iter_transitions():
            mapped_start = state_map[start]
            mapped_end = state_map[end]
            transitions[mapped_start].setdefault(symbol, set()).add(mapped_end)

        return ExtendedNFA(
            states=images,
            input_symbols=source.input_symbols,
            transitions=transitions,
            initial_state=state_map[source.initial_state],
            final_states={state_map[state] for state in source.final_states},
        )
