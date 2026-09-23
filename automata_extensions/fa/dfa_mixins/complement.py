"""DFA language complement, with completion before final-state inversion."""

from typing import Protocol, Self, cast

from automata.fa.dfa import DFA


class _CompletableDFA(Protocol):
    """Completion capability required by the complement transformation."""

    def complete(self) -> DFA: ...


class _MinimizableDFA(Protocol):
    """Extension minimization applied only when requested."""

    def minimize(self, *, keep_original_names: bool = False) -> DFA: ...


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
