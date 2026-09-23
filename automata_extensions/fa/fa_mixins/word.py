"""Pedagogical word-recognition alias for upstream automata."""

from typing import Protocol


class _WordRecognizer(Protocol):
    """The upstream operation required by the common word alias."""

    def accepts_input(self, input_str: str) -> bool:
        """Return whether the input string is accepted."""
        ...


class WordMixin:
    """Expose word recognition without duplicating upstream simulation."""

    def accepts(self: _WordRecognizer, word: str) -> bool:
        """Return whether the automaton accepts a word.

        This method delegates word recognition to automata-lib's
        ``accepts_input``. In particular, NFA epsilon transitions retain
        their upstream semantics.

        Parameters
        ----------
        word : str
            Input word, including the empty string.

        Returns
        -------
        bool
            The upstream acceptance decision.

        Raises
        ------
        Exception
            Any exception from ``accepts_input`` other than a rejected
            word is propagated unchanged.

        Complexity
        ----------
        The wrapper adds O(1) time and space. Upstream DFA simulation is
        O(|word|) time; NFA cost also depends on active states and epsilon
        closure computation. No simulation cache is added here.

        References
        ----------
        automata-lib 9.2.0 ``Automaton.accepts_input``; professor
        requirement #15 (word recognition).
        """
        return self.accepts_input(word)
