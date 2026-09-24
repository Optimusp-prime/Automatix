"""Shared construction of state right-language equation systems."""

from __future__ import annotations

from collections.abc import Hashable

from automata.fa.dfa import DFA
from automata.fa.nfa import NFA

from automata_extensions.equations import SystemOfEquations
from automata_extensions.fa.fa_mixins.regex import _state_order_key
from automata_extensions.regex import Regex, _ast


def _build_equation_system(source: DFA | NFA) -> SystemOfEquations[Hashable]:
    """Build all state equations from consuming transitions of a DFA/NFA."""
    alphabet = frozenset(source.input_symbols)
    if any(not isinstance(symbol, str) or len(symbol) != 1 for symbol in alphabet):
        raise ValueError("equation Regex alphabet requires single-character symbols")
    ordered = tuple(sorted(source.states, key=_state_order_key))
    rows: dict[Hashable, dict[Hashable, _ast.Node]] = {
        state: {} for state in ordered
    }
    for start, end, symbol in source.iter_transitions():
        if not symbol:
            raise ValueError("equation system requires epsilon-free transitions")
        row = rows[start]
        row[end] = _ast.union(row.get(end, _ast.EMPTY), _ast.Literal(symbol))

    coefficients = {
        state: {
            target: Regex._from_ast(root, alphabet)
            for target, root in rows[state].items()
        }
        for state in ordered
    }
    constants = {
        state: Regex._from_ast(
            _ast.EPSILON if state in source.final_states else _ast.EMPTY,
            alphabet,
        )
        for state in ordered
    }
    return SystemOfEquations(ordered, coefficients, constants)
