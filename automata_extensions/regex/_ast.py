"""Private immutable syntax tree for classical regular expressions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True, slots=True)
class EmptyLanguage:
    """The language containing no words."""


@dataclass(frozen=True, slots=True)
class Epsilon:
    """The language containing only the empty word."""


@dataclass(frozen=True, slots=True)
class Literal:
    symbol: str


@dataclass(frozen=True, slots=True)
class Union:
    left: Node
    right: Node


@dataclass(frozen=True, slots=True)
class Concatenation:
    left: Node
    right: Node


@dataclass(frozen=True, slots=True)
class Star:
    expression: Node


Node: TypeAlias = EmptyLanguage | Epsilon | Literal | Union | Concatenation | Star

EMPTY = EmptyLanguage()
EPSILON = Epsilon()


def union(left: Node, right: Node) -> Node:
    """Apply the smallest useful union identities during construction."""
    if isinstance(left, EmptyLanguage):
        return right
    if isinstance(right, EmptyLanguage) or left == right:
        return left
    return Union(left, right)


def concatenate(left: Node, right: Node) -> Node:
    """Apply zero and identity laws without distributing concatenation."""
    if isinstance(left, EmptyLanguage) or isinstance(right, EmptyLanguage):
        return EMPTY
    if isinstance(left, Epsilon):
        return right
    if isinstance(right, Epsilon):
        return left
    return Concatenation(left, right)


def star(expression: Node) -> Node:
    """Normalize the trivial and nested stars."""
    if isinstance(expression, (EmptyLanguage, Epsilon)):
        return EPSILON
    if isinstance(expression, Star):
        return expression
    return Star(expression)


def nullable(expression: Node) -> bool:
    """Return whether the expression accepts the empty word."""
    if isinstance(expression, EmptyLanguage):
        return False
    if isinstance(expression, Epsilon):
        return True
    if isinstance(expression, Literal):
        return False
    if isinstance(expression, Union):
        return nullable(expression.left) or nullable(expression.right)
    if isinstance(expression, Concatenation):
        return nullable(expression.left) and nullable(expression.right)
    return True  # Star always contains epsilon.


def derivative(expression: Node, symbol: str) -> Node:
    """Compute one Brzozowski derivative by structural recursion."""
    if isinstance(expression, (EmptyLanguage, Epsilon)):
        return EMPTY
    if isinstance(expression, Literal):
        return EPSILON if expression.symbol == symbol else EMPTY
    if isinstance(expression, Union):
        return union(
            derivative(expression.left, symbol),
            derivative(expression.right, symbol),
        )
    if isinstance(expression, Concatenation):
        first = concatenate(derivative(expression.left, symbol), expression.right)
        if nullable(expression.left):
            return union(first, derivative(expression.right, symbol))
        return first
    return concatenate(derivative(expression.expression, symbol), expression)


def render(expression: Node) -> str:
    """Render deterministically, adding parentheses only for precedence."""
    if isinstance(expression, EmptyLanguage):
        return "∅"
    if isinstance(expression, Epsilon):
        return "()"
    if isinstance(expression, Literal):
        # ∅ is a valid input literal, unlike the internal EmptyLanguage node.
        # This rendering is diagnostic and is not a lossless serialization.
        return expression.symbol
    if isinstance(expression, Union):
        return f"{render(expression.left)}|{render(expression.right)}"
    if isinstance(expression, Concatenation):
        left = render(expression.left)
        right = render(expression.right)
        if isinstance(expression.left, Union):
            left = f"({left})"
        if isinstance(expression.right, Union):
            right = f"({right})"
        return left + right
    inner = render(expression.expression)
    if isinstance(expression.expression, (Union, Concatenation)):
        inner = f"({inner})"
    return inner + "*"
