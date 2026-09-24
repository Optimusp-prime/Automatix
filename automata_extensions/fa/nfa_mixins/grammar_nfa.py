"""Construct extended NFAs from structural or textual regular grammars."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Self, cast

from automata_extensions.grammar import Grammar, Production

if TYPE_CHECKING:
    from automata_extensions.fa.nfa import ExtendedNFA

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_UNDECLARED_SUFFIX = re.compile(r"[A-Z][A-Za-z0-9_]*\Z")


def _parse_grammar(text: str) -> Grammar:
    """Parse a small right-linear notation, with () denoting epsilon."""
    rules: list[tuple[str, list[str]]] = []
    declared: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.count("->") != 1:
            raise ValueError(f"expected exactly one '->' in grammar line: {line!r}")
        left, right = (part.strip() for part in line.split("->"))
        if not _IDENTIFIER.fullmatch(left):
            raise ValueError(f"invalid nonterminal declaration: {left!r}")
        alternatives = [part.strip() for part in right.split("|")]
        if any(not part or any(char.isspace() for char in part) for part in alternatives):
            raise ValueError(f"malformed production alternatives: {line!r}")
        declared.add(left)
        rules.append((left, alternatives))
    if not rules:
        raise ValueError("grammar text must declare at least one nonterminal")

    productions: set[Production] = set()
    terminals: set[str] = set()
    for head, alternatives in rules:
        for alternative in alternatives:
            if alternative == "()":
                word, target = "", None
            else:
                if "(" in alternative or ")" in alternative:
                    raise ValueError(f"invalid epsilon notation: {alternative!r}")
                matches = [name for name in declared if alternative.endswith(name)]
                if matches:
                    # Longest declared suffix wins; equal-length names are distinct.
                    target = max(matches, key=len)
                    word = alternative[:-len(target)]
                elif _UNDECLARED_SUFFIX.search(alternative):
                    raise ValueError(f"undeclared trailing nonterminal: {alternative!r}")
                else:
                    word, target = alternative, None
                terminals.update(word)
            productions.add((head, word, target))
    return Grammar(
        terminals=terminals,
        nonterminals=declared,
        start_symbol=rules[0][0],
        productions=productions,
    )


class NFAGrammarMixin:
    """Build an epsilon-NFA by expanding right-linear productions."""

    @classmethod
    def from_grammar(cls: type[Self], grammar: Grammar) -> Self:
        """Return an extended NFA recognizing a right-linear grammar.

        Nonterminals are states. A continuation production leads to its
        nonterminal; a terminal-only word leads to one fresh accepting state.
        Intermediate integer states expand longer words character by
        character. Unit productions become epsilon edges and epsilon-only
        terminal productions mark their head final. With no productions,
        the result recognizes the empty language. The grammar is unchanged.

        Parameters
        ----------
        grammar : Grammar
            Immutable structural right-linear grammar.

        Returns
        -------
        Self
            New ExtendedNFA accepting exactly the generated language.

        Raises
        ------
        TypeError
            If grammar is not a Grammar instance.

        Complexity
        ----------
        O(|N| + |Sigma| + |P| + L + |P| log(|P| + 1) * K + V)
        expected time,
        where N is the nonterminal set, P the productions, L the total
        length of their terminal words, K the maximum string-comparison
        length among production keys, and V upstream NFA freezing and
        validation. Stable sorting contributes |P| log(|P| + 1) * K; rule
        expansion contributes |P| + L, including empty-word rules. Space
        is O(|N| + |P| + L) plus upstream constructor workspace.

        References
        ----------
        Professor requirement #55: A -> wB and A -> w constructions.
        automata-lib 9.2.0 NFA epsilon transitions use the empty label.
        """
        if not isinstance(grammar, Grammar):
            raise TypeError("from_grammar expects a Grammar instance")
        states: set[str | int] = set(grammar.nonterminals)
        transitions: dict[str | int, dict[str, set[str | int]]] = {
            name: {} for name in grammar.nonterminals
        }
        finals: set[str | int] = set()
        next_state = 0
        terminal_final: int | None = None

        def fresh() -> int:
            nonlocal next_state
            state = next_state
            next_state += 1
            states.add(state)
            transitions[state] = {}
            return state

        def edge(source: str | int, symbol: str, target: str | int) -> None:
            transitions[source].setdefault(symbol, set()).add(target)

        for head, word, target in sorted(
            grammar.productions, key=lambda rule: (rule[0], rule[1], rule[2] or "")
        ):
            if target is None and not word:
                finals.add(head)
                continue
            if target is None:
                if terminal_final is None:
                    terminal_final = fresh()
                    finals.add(terminal_final)
                end: str | int = terminal_final
            else:
                end = target
            current: str | int = head
            for symbol in word[:-1]:
                intermediate = fresh()
                edge(current, symbol, intermediate)
                current = intermediate
            edge(current, word[-1] if word else "", end)

        return cast(Self, cast("type[ExtendedNFA]", cls)(
            states=states,
            input_symbols=grammar.terminals,
            transitions=transitions,
            initial_state=grammar.start_symbol,
            final_states=finals,
        ))

    @classmethod
    def from_grammar_string(cls: type[Self], text: str) -> Self:
        """Parse right-linear rules and return their equivalent NFA.

        The first LHS is the start symbol. ``->`` separates a rule, ``|``
        separates alternatives, and ``()`` denotes epsilon. All LHS names
        are discovered first; the longest declared RHS suffix is interpreted
        as a continuation nonterminal. An undeclared uppercase suffix is an
        error, not a terminal word. Repeated LHS lines add alternatives.

        Parameters
        ----------
        text : str
            Multiline right-linear grammar text.

        Returns
        -------
        Self
            New ExtendedNFA accepting the grammar's language.

        Raises
        ------
        ValueError
            If declarations or alternatives are malformed or ambiguous
            under the documented notation.

        Complexity
        ----------
        O(B + |P|*|N|*K + |P| log(|P| + 1) * R + V) expected time, where B is
        text length, P the parsed alternatives, N the declared nonterminals,
        K the maximum declared-name length, R the maximum string-comparison
        length of a production sort key, and V upstream NFA construction
        validation. The parser scans each alternative against every
        declared name; ``from_grammar`` then sorts and expands the rules.
        Expansion of terminal words is covered by B. Space is linear in
        the parsed grammar and generated NFA, plus constructor workspace.

        References
        ----------
        Professor requirement #55; approved source-precedence divergence
        for ``S -> aS | b`` is recorded in ADR-0017.
        """
        return cls.from_grammar(_parse_grammar(text))
