"""Immutable, structural representation of a right-linear regular grammar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, TypeAlias

from automata_extensions.grammar.derivation import DerivationStep, _derive

# (head nonterminal, terminal word, optional continuation nonterminal).
# None distinguishes A -> w from A -> wB; an empty word denotes epsilon.
Production: TypeAlias = tuple[str, str, str | None]


@dataclass(frozen=True, slots=True, init=False)
class Grammar:
    """A right-linear grammar with immutable structural productions.

    ``(A, w, B)`` means ``A -> wB`` and ``(A, w, None)`` means
    ``A -> w``. ``w == ""`` represents epsilon in either form.
    Terminals are single-character input symbols, matching automata-lib's
    string-word reader.
    """

    terminals: frozenset[str]
    nonterminals: frozenset[str]
    start_symbol: str
    productions: frozenset[Production]

    def __init__(
        self,
        *,
        terminals: Iterable[str],
        nonterminals: Iterable[str],
        start_symbol: str,
        productions: Iterable[Production],
    ) -> None:
        """Normalize and validate a right-linear grammar.

        Copy the supplied collections into frozensets, then check the
        declared symbols and every structural production without changing
        any caller-owned collection.

        Parameters
        ----------
        terminals, nonterminals : Iterable[str]
            Terminal characters and nonterminal names.
        start_symbol : str
            Declared initial nonterminal.
        productions : Iterable[Production]
            Triples ``(head, terminal_word, continuation_or_None)``.

        Raises
        ------
        ValueError
            If symbols, the start, or productions violate the grammar model.

        Complexity
        ----------
        O(|N| + |Sigma| + |P| + L) expected time and space
        proportional to the normalized grammar, where P is the set of
        productions and L is the total length of their terminal words.
        The |P| term also counts epsilon and unit productions, whose
        terminal words are empty. Hash lookups are assumed O(1).

        References
        ----------
        Professor requirement #55: right-linear A -> wB or A -> w.
        """
        terminal_set = frozenset(terminals)
        nonterminal_set = frozenset(nonterminals)
        production_set = frozenset(productions)
        if any(not isinstance(symbol, str) or len(symbol) != 1 for symbol in terminal_set):
            raise ValueError("terminals must be single-character strings")
        if any(not isinstance(name, str) or not name for name in nonterminal_set):
            raise ValueError("nonterminals must be nonempty strings")
        if start_symbol not in nonterminal_set:
            raise ValueError("start_symbol must be a declared nonterminal")
        for production in production_set:
            if not isinstance(production, tuple) or len(production) != 3:
                raise ValueError("each production must be a (head, word, target) triple")
            head, word, target = production
            if head not in nonterminal_set or (
                target is not None and target not in nonterminal_set
            ):
                raise ValueError("production uses an undeclared nonterminal")
            if not isinstance(word, str) or any(char not in terminal_set for char in word):
                raise ValueError("production word must use declared terminals")
        object.__setattr__(self, "terminals", terminal_set)
        object.__setattr__(self, "nonterminals", nonterminal_set)
        object.__setattr__(self, "start_symbol", start_symbol)
        object.__setattr__(self, "productions", production_set)

    def derivation_tree(self, word: str) -> DerivationStep:
        """Find one finite derivation chain for a generated word.

        Breadth-first search visits each (nonterminal, consumed position)
        at most once. Rules are examined in lexical (head, word, target)
        order, making the shortest-rule derivation deterministic even for
        ambiguous grammars. Prefix-incompatible rules are pruned; epsilon
        and unit cycles cannot cause infinite search. No grammar data changes.

        Parameters
        ----------
        word : str
            Desired terminal word, possibly empty.

        Returns
        -------
        DerivationStep
            Immutable sequence of complete sentential forms.

        Raises
        ------
        RejectionException
            If the grammar cannot derive the requested word.

        Complexity
        ----------
        Let n = len(word), N be the nonterminals, P the productions, L the
        total length of their terminal words, K the maximum production-key
        comparison length, and C the total length of forms in the selected
        derivation. Expected time is O(|P| log(|P| + 1) * K +
        (n + 1)(|P| + L) + C), including rule sorting, prefix checks at
        at most |N|(n + 1) configurations, and rendering. Auxiliary space
        is O(|P| + |N|(n + 1) + C). Hash lookups are assumed O(1).

        References
        ----------
        Professor requirement #56; supplied mature derivation chain API.
        """
        return _derive(self, word)
