"""Pedagogical word-recognition alias for upstream automata."""

from collections.abc import Iterator
from typing import Protocol, TypeVar

from automata.base.exceptions import RejectionException


_ConfigurationT_co = TypeVar("_ConfigurationT_co", covariant=True)
_ConfigurationT = TypeVar("_ConfigurationT")


class _WordRecognizer(Protocol):
    """The upstream operation required by the common word alias."""

    def accepts_input(self, input_str: str) -> bool:
        """Return whether the input string is accepted."""
        ...


class _StepwiseReader(Protocol[_ConfigurationT_co]):
    """The upstream word-reading generator required by execution traces."""

    def read_input_stepwise(self, input_str: str) -> Iterator[_ConfigurationT_co]:
        """Yield successive configurations of the input word."""
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

    def execution_trace(
        self: _StepwiseReader[_ConfigurationT], word: str
    ) -> list[_ConfigurationT]:
        """Return each configuration visited while reading a word.

        The first configuration is the initial one. Upstream yields one
        further configuration per input symbol. DFA configurations are
        states, or ``None`` after a missing partial-DFA transition. NFA
        configurations are immutable active-state sets, including epsilon
        closure. A rejected word still returns all configurations yielded
        before upstream raises ``RejectionException``.

        Parameters
        ----------
        word : str
            Input word, including the empty string.

        Returns
        -------
        list
            The configurations emitted by ``read_input_stepwise`` in order.
            This method does not include an acceptance flag.

        Raises
        ------
        Exception
            Errors other than upstream ``RejectionException`` propagate.

        Complexity
        ----------
        The time is the upstream simulation cost plus O(k) to append k
        configurations. The trace occupies O(k) references plus the memory
        of configurations produced by upstream. For DFA, k = |word| + 1
        and simulation is O(|word|). NFA cost also depends on active-state
        sets and epsilon-closure computation; storing its immutable sets
        can require O(k|Q|) space.

        References
        ----------
        automata-lib 9.2.0 ``DFA.read_input_stepwise`` and
        ``NFA.read_input_stepwise``; professor requirement #16.
        """
        trace: list[_ConfigurationT] = []
        try:
            for configuration in self.read_input_stepwise(word):
                trace.append(configuration)
        except RejectionException:
            # Both upstream generators raise only after yielding their
            # final configuration, so rejection does not erase the trace.
            pass
        return trace
