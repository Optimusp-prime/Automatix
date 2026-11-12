"""Canonical derivatives and reachable Brzozowski DFA construction."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from typing import TYPE_CHECKING

from automata_extensions.regex import _ast

if TYPE_CHECKING:
    from automata_extensions.fa import ExtendedDFA
    from automata_extensions.regex import Regex


def _summands(node: _ast.Node) -> Iterator[_ast.Node]:
    """Flatten only the associative union at the root."""
    if isinstance(node, _ast.Union):
        yield from _summands(node.left)
        yield from _summands(node.right)
    elif not isinstance(node, _ast.EmptyLanguage):
        yield node


def _factors(node: _ast.Node) -> Iterator[_ast.Node]:
    """Flatten only the associative concatenation at the root."""
    if isinstance(node, _ast.Concatenation):
        yield from _factors(node.left)
        yield from _factors(node.right)
    elif not isinstance(node, _ast.Epsilon):
        yield node


def _normalize(node: _ast.Node) -> _ast.Node:
    """Normalize structurally, without parsing diagnostic regex renderings.

    Flatten, deduplicate and sort union operands (ACI); flatten concatenation
    while preserving order. Existing smart constructors handle epsilon,
    empty language and trivial/nested stars. Sorting uses the unambiguous
    structural dataclass repr, never the potentially ambiguous display text.
    This private normal form leaves Regex.derivative's existing output alone.
    """
    if isinstance(node, _ast.Union):
        terms = set(_summands(_normalize(node.left)))
        terms.update(_summands(_normalize(node.right)))
        result: _ast.Node = _ast.EMPTY
        for term in sorted(terms, key=repr):
            result = _ast.union(result, term)
        return result
    if isinstance(node, _ast.Concatenation):
        left, right = _normalize(node.left), _normalize(node.right)
        if isinstance(left, _ast.EmptyLanguage) or isinstance(right, _ast.EmptyLanguage):
            return _ast.EMPTY
        result = _ast.EPSILON
        for factor in (*_factors(left), *_factors(right)):
            result = _ast.concatenate(result, factor)
        return result
    if isinstance(node, _ast.Star):
        return _ast.star(_normalize(node.expression))
    return node


def _build_derivative_dfa(source: Regex) -> ExtendedDFA:
    """Expand each normalized derivative once, with total symbol transitions."""
    from automata_extensions.fa import ExtendedDFA
    from automata_extensions.regex import Regex

    symbols = sorted(source._symbols)
    initial = Regex._from_ast(_normalize(source._root), source._symbols)
    known = {initial._root: initial}
    transitions: dict[Regex, dict[str, Regex]] = {initial: {}}
    finals: set[Regex] = set()
    pending = deque([initial])
    while pending:
        state = pending.popleft()
        if _ast.nullable(state._root):
            finals.add(state)
        for symbol in symbols:
            root = _normalize(state.derivative(symbol)._root)
            target = known.get(root)
            if target is None:
                target = Regex._from_ast(root, source._symbols)
                known[root] = target
                transitions[target] = {}
                pending.append(target)
            transitions[state][symbol] = target

    return ExtendedDFA(
        states=set(transitions), input_symbols=source._symbols,
        transitions=transitions, initial_state=initial, final_states=finals,
        allow_partial=False,
    )
