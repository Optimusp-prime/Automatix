"""Regex conversion by greedy state elimination over the shared regex AST.

The verbose lexical engine of requirement #53 (``to_regex``) is kept for
its pedagogical trace. This mixin targets larger automata: it removes the
cheapest state first (Delgado & Morais weight) and builds labels as
immutable, structurally shared ``_ast`` nodes simplified by the existing
smart constructors, instead of copying ever-growing strings.
"""

from __future__ import annotations

from collections.abc import Iterator, Set
from dataclasses import dataclass
from typing import Protocol, TypeAlias, cast

from automata.fa.fa import FAStateT

from automata_extensions.fa.fa_mixins.regex import _state_order_key
from automata_extensions.regex import _ast


@dataclass(frozen=True, slots=True)
class _Label:
    """An AST node with its node count and nullability, both kept O(1)."""

    node: _ast.Node
    size: int
    nullable: bool


_EPSILON = _Label(_ast.EPSILON, 1, True)


def _symbol(symbol: str) -> _Label:
    """Label one transition; upstream NFA epsilon transitions use ``""``."""
    return _EPSILON if symbol == "" else _Label(_ast.Literal(symbol), 1, False)


def _plus_base(node: _ast.Node) -> _ast.Node | None:
    """Return x when node is x x* or x* x (the language x+), else None."""
    if isinstance(node, _ast.Concatenation):
        left, right = node.left, node.right
        if isinstance(right, _ast.Star) and right.expression == left:
            return left
        if isinstance(left, _ast.Star) and left.expression == right:
            return right
    return None


def _union(left: _Label, right: _Label) -> _Label:
    """Union, absorbing epsilon into a nullable operand or into x+ = x x*."""
    for epsilon, other in ((left, right), (right, left)):
        if epsilon.node == _ast.EPSILON:
            if other.nullable:
                return other
            base = _plus_base(other.node)
            if base is not None:
                # |x x*| = 2|x| + 2, hence |x*| = |x| + 1 = |x x*| // 2.
                return _Label(_ast.star(base), other.size // 2, True)
    node = _ast.union(left.node, right.node)
    if node is left.node:
        return left
    if node is right.node:
        return right
    return _Label(node, left.size + right.size + 1, left.nullable or right.nullable)


def _concatenate(left: _Label, right: _Label) -> _Label:
    """Concatenation through the AST identity laws."""
    node = _ast.concatenate(left.node, right.node)
    if node is left.node:
        return left
    if node is right.node:
        return right
    return _Label(node, left.size + right.size + 1, left.nullable and right.nullable)


def _star(label: _Label) -> _Label:
    """Kleene star through the AST normalization of trivial/nested stars."""
    node = _ast.star(label.node)
    if node is label.node:
        return label
    return _Label(node, 1 if node == _ast.EPSILON else label.size + 1, True)


class _Endpoint:
    """Fresh entry/exit vertex of the normalized elimination graph."""

    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"<{self.name}>"


_Vertex: TypeAlias = "FAStateT | _Endpoint"
_Edges: TypeAlias = "dict[_Vertex, dict[_Vertex, _Label]]"


class _EliminationSource(Protocol):
    """Finite-automaton facts consumed without reimplementing them."""

    @property
    def initial_state(self) -> FAStateT: ...

    @property
    def final_states(self) -> Set[FAStateT]: ...

    def useful_states(self) -> frozenset[FAStateT]: ...

    def iter_transitions(self) -> Iterator[tuple[FAStateT, FAStateT, str]]: ...


def _add(outgoing: _Edges, incoming: _Edges, source: _Vertex,
         target: _Vertex, label: _Label) -> None:
    """Merge a parallel edge by union, keeping both adjacency views equal."""
    existing = outgoing[source].get(target)
    merged = label if existing is None else _union(existing, label)
    outgoing[source][target] = merged
    incoming[target][source] = merged


def _weight(state: FAStateT, outgoing: _Edges, incoming: _Edges) -> int:
    """Estimated label growth caused by eliminating ``state``.

    With in-labels a_i, out-labels b_j (loop excluded) and loop c, removing
    the state replaces in+out+1 labels by in*out new ones, giving
    sum(a_i)*(out-1) + sum(b_j)*(in-1) + |c|*(in*out-1).
    """
    loop = outgoing[state].get(state)
    ins = [label.size for source, label in incoming[state].items() if source != state]
    outs = [label.size for target, label in outgoing[state].items() if target != state]
    weight = sum(ins) * (len(outs) - 1) + sum(outs) * (len(ins) - 1)
    if loop is not None:
        weight += loop.size * (len(ins) * len(outs) - 1)
    return weight


class HeuristicRegexMixin:
    """Convert an automaton to a compact regex for larger inputs."""

    def to_regex_heuristic(self) -> str | None:
        """Convert by state elimination in a greedy, size-driven order.

        Only useful states are kept. A fresh entry and exit are linked by
        epsilon to the initial and final states. At each step the remaining
        state of smallest Delgado–Morais weight (ties broken by the #53
        lexical key) is removed with ``R_pq := R_pq | R_ps (R_ss)* R_sq``.
        Labels are #49 AST nodes, simplified by its identities (empty
        word, nested stars, duplicate union operands) plus two union
        rules: epsilon is absorbed by a nullable operand, and
        epsilon | x x* (or x* x) becomes x*. Subtrees are shared, never
        copied. No minimal expression is claimed; ``to_regex()`` (#53)
        remains the verbose lexical construction. The source is unchanged.

        Returns
        -------
        str | None
            Equivalent regex in the #49 syntax (parseable by ``Regex``),
            ``""`` for the language {epsilon}, or None for the empty
            language, as in ``to_regex()``.

        Complexity
        ----------
        With n useful states and m transitions: O(n + m) setup after the
        O(|Q| + m) useful-state query, then n eliminations. Each one
        evaluates every remaining weight in O(n + E) for the current
        E <= (n + 2)**2 edges and creates at most (n + 1)**2 labels in
        O(1) each, except that AST union equality may compare shared
        subtrees. Hence O(n**3) label operations and O(n**3) AST nodes
        of internal space. Rendering the final string is linear in its
        length L, which can be exponential in n for some languages (this
        is a known lower bound for any regex, not of this algorithm).

        References
        ----------
        Brzozowski & McCluskey (1963), state elimination; Delgado &
        Morais (2004), "Approximation to the smallest regular expression
        for a given regular language", elimination-order weight.
        Requirements #49 and #53.
        """
        source = cast(_EliminationSource, self)
        useful = source.useful_states()
        if source.initial_state not in useful:
            return None

        entry, exit_ = _Endpoint("entry"), _Endpoint("exit")
        vertices: list[_Vertex] = [entry, exit_, *useful]
        outgoing: _Edges = {vertex: {} for vertex in vertices}
        incoming: _Edges = {vertex: {} for vertex in vertices}
        _add(outgoing, incoming, entry, source.initial_state, _EPSILON)
        for state in sorted(useful & source.final_states, key=_state_order_key):
            _add(outgoing, incoming, state, exit_, _EPSILON)
        for start, end, symbol in source.iter_transitions():
            if start in useful and end in useful:
                _add(outgoing, incoming, start, end, _symbol(symbol))

        remaining = sorted(useful, key=_state_order_key)
        while remaining:
            removed = min(
                remaining,
                key=lambda state: (_weight(state, outgoing, incoming), _state_order_key(state)),
            )
            loop = outgoing[removed].pop(removed, None)
            incoming[removed].pop(removed, None)
            middle = _EPSILON if loop is None else _star(loop)
            predecessors = incoming.pop(removed)
            successors = outgoing.pop(removed)
            for predecessor in predecessors:
                del outgoing[predecessor][removed]
            for successor in successors:
                del incoming[successor][removed]
            for predecessor, before in predecessors.items():
                for successor, after in successors.items():
                    _add(outgoing, incoming, predecessor, successor,
                         _concatenate(_concatenate(before, middle), after))
            remaining.remove(removed)

        text = _ast.render(outgoing[entry][exit_].node)
        return "" if text == "()" else text
