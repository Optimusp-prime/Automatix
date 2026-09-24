"""Conversion of DFA and NFA transition graphs to right-linear grammars."""

from __future__ import annotations

import re
from collections.abc import Set
from typing import cast

from automata.fa.dfa import DFA
from automata.fa.fa import FAStateT
from automata.fa.nfa import NFA

from automata_extensions.grammar import DerivationStep, Grammar, Production
from automata_extensions.grammar.derivation import _derive

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def _state_key(state: FAStateT) -> tuple[str, str, str, str]:
    return (str(state), type(state).__module__, type(state).__qualname__, repr(state))


def _state_names(states: Set[FAStateT]) -> dict[FAStateT, str]:
    """Name states consistently for grammar conversion and derivation display."""
    ordered = sorted(states, key=_state_key)
    if any(_state_key(left) == _state_key(right) for left, right in zip(ordered, ordered[1:])):
        raise ValueError("distinct states have indistinguishable grammar naming keys")
    reserved = {
        state for state in ordered
        if isinstance(state, str) and _IDENTIFIER.fullmatch(state)
    }
    names: dict[FAStateT, str] = {}
    used: set[str] = set(reserved)
    next_index = 0
    for state in ordered:
        if isinstance(state, str) and state in reserved:
            names[state] = state
            continue
        while f"Q{next_index}" in used:
            next_index += 1
        name = f"Q{next_index}"
        next_index += 1
        used.add(name)
        names[state] = name
    return names


class GrammarMixin:
    """Expose right-linear grammar conversion on ordinary DFA/NFA edges."""

    def to_grammar(self) -> Grammar:
        """Return a right-linear grammar recognizing the same language.

        Each source state becomes a nonterminal; a transition becomes a
        continuation production and a final state gets an epsilon rule.
        NFA epsilon transitions become unit productions. Missing edges in
        a partial DFA produce no rule; an automaton without final states
        produces no terminal-only epsilon rules. The source is not modified.
        Safe string state names are retained; other states receive
        collision-free Q0, Q1, ... names in stable type/repr order.

        Returns
        -------
        Grammar
            Immutable right-linear grammar with the same language.

        Raises
        ------
        ValueError
            If an input symbol is not one character, or distinct states
            have indistinguishable stable naming keys.

        Complexity
        ----------
        O(|Q| log |Q| + |Sigma| + T + |P|) expected time and
        O(|Q| + |P|) auxiliary space, where Q is the state set, Sigma the
        alphabet, T the transition-table entries inspected plus edges
        emitted by upstream ``iter_transitions()``, and P the generated
        productions. Every NFA epsilon/nondeterministic edge contributes
        to T. NFA entries with empty destination sets are also scanned;
        T can therefore exceed the number of emitted edges |E|.
        Sorting gives the |Q| log |Q| term; Grammar validates
        every generated rule. State-key/string comparison costs are
        additional if state representations are not constant size.

        References
        ----------
        Professor requirement #55; automata-lib 9.2.0 DFA/NFA
        ``iter_transitions()`` yields (source, destination, symbol).
        """
        source = cast(DFA | NFA, self)
        if any(len(symbol) != 1 for symbol in source.input_symbols):
            raise ValueError("grammar conversion requires single-character input symbols")
        names = _state_names(source.states)
        productions: set[Production] = {
            (names[state], "", None) for state in source.final_states
        }
        for start, end, symbol in source.iter_transitions():
            productions.add((names[start], symbol, names[end]))
        return Grammar(
            terminals=source.input_symbols,
            nonterminals=names.values(),
            start_symbol=names[source.initial_state],
            productions=productions,
        )

    def derivation_tree(self, word: str) -> DerivationStep:
        """Derive an accepted word through this automaton's grammar.

        Search the structural grammar built by ``to_grammar()`` and render
        nonterminals using their original automaton state spellings. This
        preserves the mature DFA chain even when #55 assigned internal
        grammar names to numeric or heterogeneous states. NFA epsilon
        transitions appear as unit-production steps. No source is mutated.

        Parameters
        ----------
        word : str
            Target terminal word, possibly empty.

        Returns
        -------
        DerivationStep
            One deterministic complete derivation chain.

        Raises
        ------
        RejectionException
            If the word has no derivation / is rejected.
        ValueError
            If #55 cannot map source states or symbols to the grammar model.

        Complexity
        ----------
        This includes ``to_grammar()`` plus naming and Grammar search.
        Let Q be automaton states, T scanned transition entries plus emitted
        edges, P generated grammar productions, n the word length, L the
        total production-word length, K the maximum rule-key comparison
        length, and C the output-chain character count. Expected time is
        O(|Q| log |Q| + |Sigma| + T + |P| log(|P| + 1) * K +
        (n + 1)(|P| + L) + C). Auxiliary space is O(|Q| + |P| +
        |Q|(n + 1) + C). See Grammar.derivation_tree for search details.

        References
        ----------
        Professor requirement #56; supplied mature DFA sequence example.
        Reuses #55 Grammar and its deterministic state naming policy.
        """
        source = cast(DFA | NFA, self)
        grammar = self.to_grammar()
        display_names = {
            grammar_name: str(state)
            for state, grammar_name in _state_names(source.states).items()
        }
        return _derive(grammar, word, display_names)
