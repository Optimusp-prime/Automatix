"""Immutable regular expressions and Brzozowski symbol derivatives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import AbstractSet

from automata.base.exceptions import InvalidRegexError

from automata_extensions.regex import _ast


_UNSUPPORTED = frozenset("+?&^.[]{}\\")


class _Parser:
    """Recursive-descent parser for union, concatenation and star."""

    def __init__(self, expression: str, input_symbols: frozenset[str] | None):
        self.expression = expression
        self.input_symbols = input_symbols
        self.position = 0
        self.literals: set[str] = set()

    def parse(self) -> _ast.Node:
        if not self.expression:
            return _ast.EPSILON
        result = self._union()
        if self.position != len(self.expression):
            raise InvalidRegexError(
                f"Unexpected character at position {self.position}"
            )
        return result

    def _union(self) -> _ast.Node:
        left = self._concatenation()
        while self._peek() == "|":
            self.position += 1
            left = _ast.union(left, self._concatenation())
        return left

    def _concatenation(self) -> _ast.Node:
        if self._peek() in (None, ")", "|"):
            raise InvalidRegexError(
                f"Missing expression at position {self.position}"
            )
        left = self._postfix()
        while self._peek() not in (None, ")", "|"):
            left = _ast.concatenate(left, self._postfix())
        return left

    def _postfix(self) -> _ast.Node:
        value = self._atom()
        while self._peek() == "*":
            self.position += 1
            value = _ast.star(value)
        return value

    def _atom(self) -> _ast.Node:
        character = self._peek()
        if character is None:
            raise InvalidRegexError("Unexpected end of regular expression")
        if character == "(":
            self.position += 1
            if self._peek() == ")":
                self.position += 1
                return _ast.EPSILON
            value = self._union()
            if self._peek() != ")":
                raise InvalidRegexError("Unmatched opening parenthesis")
            self.position += 1
            return value
        if character in _UNSUPPORTED:
            raise InvalidRegexError(
                f"Unsupported regex syntax {character!r} at position {self.position}"
            )
        if character in ("*", "|", ")"):
            raise InvalidRegexError(
                f"Unexpected operator {character!r} at position {self.position}"
            )
        if self.input_symbols is not None and character not in self.input_symbols:
            raise InvalidRegexError(
                f"Literal {character!r} is not in input_symbols"
            )
        self.position += 1
        self.literals.add(character)
        return _ast.Literal(character)

    def _peek(self) -> str | None:
        if self.position == len(self.expression):
            return None
        return self.expression[self.position]


@dataclass(frozen=True, slots=True, init=False)
class Regex:
    """An immutable classical regular expression.

    Parameters
    ----------
    expression : str
        Expression using literals, ``|``, implicit concatenation, ``*`` and
        parentheses. ``""`` and ``()`` denote epsilon.
    input_symbols : AbstractSet[str] | None, optional
        Explicit single-character alphabet. If omitted, literal characters
        in the expression form the alphabet.

    Raises
    ------
    InvalidRegexError
        If the expression is malformed, uses unsupported syntax, or contains
        a literal outside the explicit single-character alphabet.

    Complexity
    ----------
    Parsing visits the input once and allocates O(n) AST nodes for an
    expression of length n. Structural normalization may compare subtrees,
    so its worst-case cost can exceed O(n).

    References
    ----------
    Professor requirement #49; the classical rational-expression grammar.
    This is not an automata-lib Regex subclass.
    """

    _root: _ast.Node
    _symbols: frozenset[str]

    @classmethod
    def _from_ast(cls, root: _ast.Node, symbols: AbstractSet[str]) -> Regex:
        """Construct a fresh immutable value from a trusted private AST."""
        result = object.__new__(cls)
        object.__setattr__(result, "_root", root)
        object.__setattr__(result, "_symbols", frozenset(symbols))
        return result

    def __init__(
        self,
        expression: str,
        *,
        input_symbols: AbstractSet[str] | None = None,
    ) -> None:
        if not isinstance(expression, str):
            raise TypeError("expression must be a string")
        symbols = None if input_symbols is None else frozenset(input_symbols)
        if symbols is not None and any(
            not isinstance(symbol, str) or len(symbol) != 1
            for symbol in symbols
        ):
            raise InvalidRegexError("input_symbols must contain single characters")
        parser = _Parser(expression, symbols)
        root = parser.parse()
        object.__setattr__(self, "_root", root)
        object.__setattr__(
            self, "_symbols", symbols if symbols is not None else frozenset(parser.literals)
        )

    def derivative(self, symbol: str) -> Regex:
        """Return the Brzozowski derivative by one character.

        Parameters
        ----------
        symbol : str
            A single input character, not a word.

        Returns
        -------
        Regex
            A fresh immutable expression for the left quotient by ``symbol``.
            An unknown character gives the internal empty language.

        Raises
        ------
        ValueError
            If ``symbol`` is empty or contains more than one character.
        TypeError
            If ``symbol`` is not a string.

        Complexity
        ----------
        Visits the input AST recursively and constructs a result whose size
        may grow with repeated derivatives. Structural normalization can add
        subtree comparison cost; recursion depth follows AST depth.

        References
        ----------
        Professor requirement #49. ``L(D_a(R)) = a⁻¹ L(R)``, the one-symbol
        case of the left quotient in requirement #47.
        """
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        if len(symbol) != 1:
            raise ValueError("derivative requires exactly one character")
        result = object.__new__(type(self))
        object.__setattr__(result, "_root", _ast.derivative(self._root, symbol))
        object.__setattr__(result, "_symbols", self._symbols)
        return result

    def __str__(self) -> str:
        """Render the AST for display; ``∅`` is not a reparsable input token.

        Returns
        -------
        str
            Deterministic precedence-aware diagnostic expression.

        Complexity
        ----------
        O(output length) time and recursive stack space proportional to AST
        depth.

        References
        ----------
        Professor requirement #49; the private immutable AST renderer.
        """
        return _ast.render(self._root)
