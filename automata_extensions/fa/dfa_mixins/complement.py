"""DFA language complement, with completion before final-state inversion."""

from typing import TYPE_CHECKING, Protocol, Self, cast

from automata.fa.dfa import DFA

if TYPE_CHECKING:
    from automata_extensions.fa.dfa import ExtendedDFA


class _CompletableDFA(Protocol):
    """Completion capability required by the complement transformation."""

    def complete(self) -> DFA: ...


class _MinimizableDFA(Protocol):
    """Extension minimization applied only when requested."""

    def minimize(self, *, keep_original_names: bool = False) -> DFA: ...


class ComplementMixin:
    """Construct the complement of a deterministic finite automaton."""

    def is_universal(self) -> bool:
        """Return whether this DFA accepts every word over its alphabet.

        Returns
        -------
        bool
            True exactly when the complement language is empty. Completion
            handles missing partial-DFA transitions before final inversion.
            For an empty alphabet, universality means accepting epsilon.
            The source is unchanged; no cache or minimization is added.

        Complexity
        ----------
        O(n + (n+1)*|Sigma| + V) time and
        O(n + (n+1)*|Sigma| + V_space) peak space, where n=|Q|.
        Includes completion/inversion, constructor freezing and validation
        V/V_space, and accessibility on the complete result, which has at
        most n+1 states. Hashing/lookups are expected constant-time.

        References
        ----------
        Professor requirement #38: complement then empty-language decision.
        Supplied mature DFA complement domain; requirements #22 and #13.
        """
        return cast("ExtendedDFA", self).complement().is_empty()

    def complement(
        self, *, retain_names: bool = False, minify: bool = False
    ) -> Self:
        """Return a fresh DFA recognizing the complement language.

        The DFA is completed first, then every final state is exchanged
        with a nonfinal state. In particular, a newly added sink becomes
        final. The source automaton is not modified. ``retain_names`` has
        no effect without minimization.

        Parameters
        ----------
        retain_names : bool, default: False
            Keep a representative original state name when minimizing.
        minify : bool, default: False
            Minimize the complemented DFA using the extension's method.

        Returns
        -------
        Self
            New complete ExtendedDFA accepting the complement language.

        Complexity
        ----------
        O(|Q| × |Sigma| + V) time and O(|Q| × |Sigma| + M) auxiliary space
        without minimization, including completion and validation.
        With ``minify=True``, add the extension minimization cost:
        O(|Q|² × |Sigma| + |Q|² × alpha(|Q|) + V) expected time and
        O(|Q|² × |Sigma| + M) auxiliary space. V/M cover construction and
        validation in both phases.

        References
        ----------
        Professor requirement #22: complete, then invert final states.
        The supplied mature reference specifies ``minify=False`` by default.
        Requirement #32 supplies optional extension minimization. The source
        PDFs were not accessed.
        """
        completed = cast(_CompletableDFA, self).complete()
        result = cast(
            Self,
            type(completed)(
                states=completed.states,
                input_symbols=completed.input_symbols,
                transitions=completed.transitions,
                initial_state=completed.initial_state,
                final_states=completed.states - completed.final_states,
                allow_partial=False,
            ),
        )
        if minify:
            return cast(
                Self,
                cast(_MinimizableDFA, result).minimize(
                    keep_original_names=retain_names
                ),
            )
        return result
