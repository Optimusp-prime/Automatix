"""Classical Thompson construction for the project's regular-expression AST."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, AbstractSet, Self, cast

from automata_extensions.regex import Regex, _ast

if TYPE_CHECKING:
    from automata_extensions.fa.nfa import ExtendedNFA


@dataclass(frozen=True, slots=True)
class _Fragment:
    """Entry and exit of one fragment in a shared, disjoint state graph."""

    start: int
    final: int


class _ThompsonBuilder:
    """Own the temporary graph while recursively composing fragments."""

    def __init__(self) -> None:
        self.transitions: dict[int, dict[str, set[int]]] = {}

    def _state(self) -> int:
        state = len(self.transitions)
        self.transitions[state] = {}
        return state

    def _edge(self, source: int, symbol: str, target: int) -> None:
        self.transitions[source].setdefault(symbol, set()).add(target)

    def build(self, expression: _ast.Node) -> _Fragment:
        """Build a fresh fragment by the six textbook Thompson rules."""
        if isinstance(expression, (_ast.EmptyLanguage, _ast.Epsilon, _ast.Literal)):
            start, final = self._state(), self._state()
            if isinstance(expression, _ast.Epsilon):
                self._edge(start, "", final)
            elif isinstance(expression, _ast.Literal):
                self._edge(start, expression.symbol, final)
            return _Fragment(start, final)

        if isinstance(expression, _ast.Union):
            start = self._state()
            left = self.build(expression.left)
            right = self.build(expression.right)
            final = self._state()
            self._edge(start, "", left.start)
            self._edge(start, "", right.start)
            self._edge(left.final, "", final)
            self._edge(right.final, "", final)
            return _Fragment(start, final)

        if isinstance(expression, _ast.Concatenation):
            left = self.build(expression.left)
            right = self.build(expression.right)
            self._edge(left.final, "", right.start)
            return _Fragment(left.start, right.final)

        # All remaining nodes are stars.
        assert isinstance(expression, _ast.Star)
        start = self._state()
        operand = self.build(expression.expression)
        final = self._state()
        self._edge(start, "", operand.start)
        self._edge(start, "", final)
        self._edge(operand.final, "", operand.start)
        self._edge(operand.final, "", final)
        return _Fragment(start, final)


class ThompsonMixin:
    """Build an extended NFA from the project's classical regex grammar."""

    @classmethod
    def from_regex(
        cls: type[Self], regex: str, *, input_symbols: AbstractSet[str] | None = None
    ) -> Self:
        """Construct an epsilon-NFA explicitly by Thompson's algorithm.

        Parameters
        ----------
        regex : str
            A #49 expression: literals, union, concatenation, star and groups.
        input_symbols : AbstractSet[str] | None, optional
            Explicit single-character alphabet, or infer it from literals.

        Returns
        -------
        Self
            A fresh extended NFA. The source expression is not modified.

        Raises
        ------
        InvalidRegexError
            If the expression or explicit alphabet violates the #49 grammar.

        Complexity
        ----------
        The fragment construction takes O(n) time and space for the normalized
        AST of n nodes, followed by automata-lib constructor cost V. Parsing
        and normalization can exceed O(len(regex)) through subtree comparisons;
        recursive parser/construction depth is bounded by Python's stack.

        References
        ----------
        Professor requirement #51 (Thompson construction); requirement #49
        private immutable AST; automata-lib 9.2.0 NFA constructor. This
        intentionally does not delegate to upstream NFA.from_regex.
        """
        parsed = Regex(regex, input_symbols=input_symbols)
        builder = _ThompsonBuilder()
        fragment = builder.build(parsed._root)
        concrete = cast("type[ExtendedNFA]", cls)
        result = concrete(
            states=set(builder.transitions),
            input_symbols=parsed._symbols,
            transitions=builder.transitions,
            initial_state=fragment.start,
            final_states={fragment.final},
        )
        return cast(Self, result)
