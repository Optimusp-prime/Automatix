"""One finite derivation chain of a right-linear regular grammar."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping

from automata.base.exceptions import RejectionException

if TYPE_CHECKING:
    from automata_extensions.grammar.grammar import Grammar, Production

_Configuration = tuple[str, int]


@dataclass(frozen=True, slots=True)
class DerivationStep:
    """Immutable sequence of sentential forms ending in a terminal word."""

    _forms: tuple[str, ...]
    _terminal_word: str

    def word(self) -> str:
        """Return the fully derived terminal word.

        Returns
        -------
        str
            Terminal word represented by the final sentential form.

        Complexity
        ----------
        O(1) time and auxiliary space: the word is retained immutably.

        References
        ----------
        Professor requirement #56; supplied mature DerivationStep API.
        """
        return self._terminal_word

    def sequence(self) -> str:
        """Render the complete derivation with ``' => '`` separators.

        Returns
        -------
        str
            Every sentential form, from start to terminal word.

        Complexity
        ----------
        O(C + k) time and space, where C is the total character count of
        stored forms and k their count, including join separators.

        References
        ----------
        Professor requirement #56; supplied mature sequence rendering.
        """
        return " => ".join(self._forms)


def _derive(
    grammar: Grammar, target_word: str,
    display_names: Mapping[str, str] | None = None,
) -> DerivationStep:
    """Breadth-first derivation search over (nonterminal, input position)."""
    choices: dict[str, list[Production]] = {name: [] for name in grammar.nonterminals}
    for production in sorted(
        grammar.productions, key=lambda rule: (rule[0], rule[1], rule[2] or "")
    ):
        choices[production[0]].append(production)

    start = (grammar.start_symbol, 0)
    pending = deque([start])
    parent: dict[_Configuration, tuple[_Configuration, Production] | None] = {start: None}
    completion: tuple[_Configuration, Production] | None = None
    while pending and completion is None:
        current = pending.popleft()
        head, position = current
        for production in choices[head]:
            _, terminal_word, continuation = production
            if not target_word.startswith(terminal_word, position):
                continue
            next_position = position + len(terminal_word)
            if continuation is None:
                if next_position == len(target_word):
                    completion = (current, production)
                    break
                continue
            successor = (continuation, next_position)
            if successor not in parent:
                parent[successor] = (current, production)
                pending.append(successor)

    if completion is None:
        raise RejectionException(f"grammar does not derive {target_word!r}")

    current, final_production = completion
    selected = [final_production]
    while (link := parent[current]) is not None:
        previous, production = link
        selected.append(production)
        current = previous
    selected.reverse()

    def display(name: str) -> str:
        return display_names.get(name, name) if display_names is not None else name

    prefix = ""
    forms = [display(grammar.start_symbol)]
    for _, terminal_word, continuation in selected:
        prefix += terminal_word
        forms.append(prefix + (display(continuation) if continuation is not None else ""))
    return DerivationStep(tuple(forms), target_word)
