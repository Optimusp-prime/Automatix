"""Language reversal for symbol-labeled DFA and NFA automata."""

from typing import TYPE_CHECKING, cast

from automata.fa.dfa import DFA
from automata.fa.nfa import NFA

if TYPE_CHECKING:
    from automata_extensions.fa.nfa import ExtendedNFA


class ReverseMixin:
    """Delegate reversal to upstream while retaining the extension layer."""

    def reverse(self) -> "ExtendedNFA":
        """Return an NFA recognizing the mirror of this DFA/NFA language.

        Returns
        -------
        ExtendedNFA
            A fresh NFA whose transitions reverse the original edges,
            preserving labels (including epsilon). The old initial state
            is the sole final state. Following upstream, a fresh initial
            state has epsilon edges to all old finals, even if there are
            zero or one. Its name is the first unused nonnegative integer.
            The alphabet and original state objects are preserved. Neither
            source mutation nor caching is introduced.

            This mixin is exposed only on DFA/NFA, not regex-labeled GNFA.
            None states are preserved structurally; upstream NFA word
            reading still has the NetworkX limitation recorded in ADR-0007.

        Complexity
        ----------
        O(|Q| + T + V) time and O(|Q| + |E| + V_space) peak space,
        including optional DFA-to-NFA conversion and upstream construction.
        T counts stored rows, symbol entries and destinations inspected;
        E counts actual edges. V/V_space cover freezing and validation.
        Expected constant-time original-state hashing is assumed.

        References
        ----------
        Professor requirement #36 and supplied mature ReverseMixin example.
        automata-lib 9.2.0 NFA.from_dfa, NFA.reverse and FA._add_new_state.
        ADR-0002 delegation; ADR-0003 representation-specific placement.
        """
        from automata_extensions.fa.nfa import ExtendedNFA

        source = cast(DFA | ExtendedNFA, self)
        nfa = ExtendedNFA.from_dfa(source) if isinstance(source, DFA) else source
        # Explicit upstream dispatch avoids recursively calling this wrapper.
        return NFA.reverse(nfa)
