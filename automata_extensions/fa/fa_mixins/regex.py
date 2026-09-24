"""Pedagogical DFA-to-regex conversion with fixed elimination order."""

from __future__ import annotations

from itertools import product
from typing import TYPE_CHECKING, cast

from automata.fa.dfa import DFA
from automata.fa.fa import FAStateT

if TYPE_CHECKING:
    from automata_extensions.fa.gnfa import ExtendedGNFA


def _group_union(label: str, gnfa: ExtendedGNFA) -> str:
    """Parenthesize only an ungrouped top-level union used as a factor."""
    return f"({label})" if gnfa._isbracket_req(label) else label


def _concatenate(gnfa: ExtendedGNFA, *labels: str | None) -> str | None:
    """Multiply regex labels, treating None as empty and '' as epsilon."""
    if any(label is None for label in labels):
        return None
    return "".join(_group_union(label, gnfa) for label in labels if label)


def _star(label: str | None) -> str:
    """Return a deliberately unsimplified Kleene star of a label."""
    if label is None or label == "":
        return ""
    return f"{label}*" if len(label) == 1 else f"({label})*"


def _union(existing: str | None, via: str | None) -> str | None:
    """Keep the pre-existing edge first, matching the mature trace."""
    if existing is None:
        return via
    if via is None:
        return existing
    if existing == "" and via == "":
        return ""
    # ``()`` is the project's existing epsilon spelling and is understood
    # by both automata-lib and the #49/#51 classical parser.
    left = existing if existing else "()"
    right = via if via else "()"
    return f"({left}|{right})"


class RegexMixin:
    """Convert a DFA to a verbose regex by lexicographic elimination."""

    def to_regex(self) -> str | None:
        """Eliminate DFA states in lexical order from a normalized GNFA.

        Returns
        -------
        str | None
            A pedagogically verbose regex for the same language. For the
            empty language, return None as in verified GNFA requirement #39.
            The source DFA is not modified.

        Complexity
        ----------
        For n DFA states, normalization and elimination perform O(n**3)
        label updates plus upstream GNFA construction/validation. String
        copying costs the sum of intermediate label lengths, which may grow
        exponentially; peak space holds O(n**2) labels of that size.

        References
        ----------
        Professor requirement #53: successive state elimination. Supplied
        mature RegexMixin example and lexicographic order. Reuses the #39
        GNFA.from_dfa normalization, but not upstream GNFA.to_regex, whose
        degree-based elimination yields a different observable expression.
        """
        from automata_extensions.fa.gnfa import ExtendedGNFA

        source = cast(DFA, self)
        gnfa = ExtendedGNFA.from_dfa(source)
        remaining: set[FAStateT] = set(gnfa.states)
        transitions: dict[FAStateT, dict[FAStateT, str | None]] = {
            state: dict(paths) for state, paths in gnfa.transitions.items()
        }

        # Tie-break heterogeneous states with their type and repr; ordinary
        # string states follow the mature reference's lexical order exactly.
        order = sorted(
            source.states,
            key=lambda state: (
                str(state), type(state).__module__,
                type(state).__qualname__, repr(state),
            ),
        )
        for removed in order:
            survivors = remaining - {removed}
            for start, end in product(
                survivors - {gnfa.final_state},
                survivors - {gnfa.initial_state},
            ):
                via = _concatenate(
                    gnfa,
                    transitions[start][removed],
                    _star(transitions[removed][removed]),
                    transitions[removed][end],
                )
                transitions[start][end] = _union(transitions[start][end], via)
            remaining.remove(removed)
            del transitions[removed]
            for state in remaining - {gnfa.final_state}:
                del transitions[state][removed]

        return transitions[gnfa.initial_state][gnfa.final_state]
