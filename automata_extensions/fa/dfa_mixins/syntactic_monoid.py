"""Syntactic monoid of a DFA language via its canonical residual automaton."""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from automata_extensions.fa.dfa import ExtendedDFA


def _append_letter(
    current: tuple[int, ...], letter: tuple[int, ...]
) -> tuple[int, ...]:
    """Compose the letter action after the current word action."""
    return tuple(letter[destination] for destination in current)


class SyntacticMonoidMixin:
    """Compute the word-induced transformations of a language's minimal DFA."""

    def syntactic_monoid(self) -> frozenset[tuple[int, ...]]:
        """Return the syntactic monoid of the recognized language.

        Normalize through ``residual_automaton()`` so inaccessible and
        equivalent source states disappear and missing transitions become
        the empty quotient. On canonical states q0, ..., q(n-1), a tuple's
        entry i is the destination index of qi. Start with the identity
        (the empty word) and close under appending each input letter. For
        a word w followed by a, tau_(wa) = tau_a composed after tau_w.
        Neither the source nor the residual automaton is modified.

        Returns
        -------
        frozenset[tuple[int, ...]]
            All distinct total transformations induced by words, encoded
            in numeric q-index order. The collection has no iteration-order
            guarantee.

        Raises
        ------
        AssertionError
            If #60's residual automaton violates its canonical-state or
            completeness contract.

        Complexity
        ----------
        Let n be the residual DFA state count, s the alphabet size, m the
        monoid size, and C60/S60 the time/space costs of #60. Expected time
        is O(C60 + s log s + m*s*n): each of m transformations is extended
        by s letters, with O(n) composition and tuple hashing. Peak space
        is O(S60 + m*n + s*n), including generators and explicit results.
        Since m <= n**n, this is not polynomial in n in general. Expected
        bounds assume constant-time dictionary/set lookups.

        References
        ----------
        Professor requirement #62; supplied mature ``syntactic_monoid``
        example; Automatix ADR-0022. Reuses requirement #60.
        """
        source = cast("ExtendedDFA", self)
        canonical = source.residual_automaton()
        size = len(canonical.states)
        names = tuple(f"q{index}" for index in range(size))
        if canonical.states != frozenset(names):
            raise AssertionError("residual states must be q0, ..., q(n-1)")

        indices = {name: index for index, name in enumerate(names)}
        generators: list[tuple[int, ...]] = []
        for symbol in sorted(canonical.input_symbols):
            try:
                generator = tuple(
                    indices[canonical.transitions[name][symbol]] for name in names
                )
            except KeyError as error:
                raise AssertionError("residual DFA must be complete") from error
            generators.append(generator)

        identity = tuple(range(size))
        discovered = {identity}
        pending = deque((identity,))
        while pending:
            current = pending.popleft()
            for letter in generators:
                successor = _append_letter(current, letter)
                if successor not in discovered:
                    discovered.add(successor)
                    pending.append(successor)

        return frozenset(discovered)
