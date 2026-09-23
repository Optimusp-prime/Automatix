"""DFA language complement, with completion before final-state inversion."""

from typing import Protocol, Self, cast

from automata.fa.dfa import DFA


class _CompletableDFA(Protocol):
    """Completion capability required by the complement transformation."""

    def complete(self) -> DFA: ...


class ComplementMixin:
    """Construct the complement of a deterministic finite automaton."""

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
            Reserved for the optional minimization branch.
        minify : bool, default: False
            Request minimization after complementing. This option awaits
            Automatix professor requirement #32.

        Returns
        -------
        Self
            New complete ExtendedDFA accepting the complement language.

        Raises
        ------
        NotImplementedError
            If ``minify=True`` is requested before requirement #32.

        Complexity
        ----------
        O(|Q| × |Sigma| + V) time and O(|Q| × |Sigma| + M) auxiliary space
        in the worst case, including completion and new DFA validation.
        V and M are upstream constructor/validation time and memory.

        References
        ----------
        Professor requirement #22: complete, then invert final states.
        The supplied mature reference specifies ``minify=False`` by default.
        The source PDFs were not accessed.
        """
        if minify:
            raise NotImplementedError(
                "minify=True requires Automatix requirement #32 minimization, "
                "which is not implemented yet."
            )

        completed = cast(_CompletableDFA, self).complete()
        return cast(
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
