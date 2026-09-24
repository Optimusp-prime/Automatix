"""Immutable rational-language equation systems and Arden elimination."""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Generic, TypeVar

from automata_extensions.equations.arden import _arden_multiplier
from automata_extensions.regex import Regex, _ast


VariableT = TypeVar("VariableT", bound=Hashable)


@dataclass(frozen=True, slots=True, init=False)
class SystemOfEquations(Generic[VariableT]):
    """An immutable system ``X_i = ⋃_j A_ij X_j ∪ B_i``.

    Missing coefficients denote the empty language. Variables retain their
    caller-specified order and can be any hashable state objects.

    Parameters
    ----------
    variables : Sequence[VariableT]
        Distinct variables in deterministic elimination order.
    coefficients : Mapping[VariableT, Mapping[VariableT, Regex]]
        Sparse left coefficients, indexed first by equation then variable.
    constants : Mapping[VariableT, Regex]
        One constant term for every declared variable.

    Raises
    ------
    TypeError
        If a variable is unhashable or a term is not a Regex.
    ValueError
        If variables repeat, a variable is undeclared, or a constant is
        missing.

    Complexity
    ----------
    For n variables and m supplied coefficients, construction copies and
    validates O(n + m) entries in expected time and space, assuming constant-
    time hashing. It does not traverse or render Regex ASTs.

    References
    ----------
    Professor requirement #58; Automatix's chosen standalone system API.
    """

    variables: tuple[VariableT, ...]
    coefficients: Mapping[VariableT, Mapping[VariableT, Regex]]
    constants: Mapping[VariableT, Regex]

    def __init__(
        self,
        variables: Sequence[VariableT],
        coefficients: Mapping[VariableT, Mapping[VariableT, Regex]],
        constants: Mapping[VariableT, Regex],
    ) -> None:
        ordered = tuple(variables)
        try:
            declared = set(ordered)
        except TypeError as error:
            raise TypeError("equation variables must be hashable") from error
        if len(declared) != len(ordered):
            raise ValueError("equation variables must be distinct")
        if declared != constants.keys():
            raise ValueError("constants must contain exactly the declared variables")
        if not coefficients.keys() <= declared:
            raise ValueError("coefficient sources must be declared variables")

        copied_coefficients: dict[VariableT, Mapping[VariableT, Regex]] = {}
        copied_constants: dict[VariableT, Regex] = {}
        for source in ordered:
            constant = constants[source]
            if not isinstance(constant, Regex):
                raise TypeError(f"constant for {source!r} must be a Regex")
            copied_constants[source] = constant
            row = coefficients.get(source, {})
            if not row.keys() <= declared:
                raise ValueError(
                    f"coefficient destinations for {source!r} must be declared variables"
                )
            copied_row: dict[VariableT, Regex] = {}
            for target, coefficient in row.items():
                if not isinstance(coefficient, Regex):
                    raise TypeError(
                        f"coefficient for {source!r}, {target!r} must be a Regex"
                    )
                copied_row[target] = coefficient
            copied_coefficients[source] = MappingProxyType(copied_row)

        object.__setattr__(self, "variables", ordered)
        object.__setattr__(self, "coefficients", MappingProxyType(copied_coefficients))
        object.__setattr__(self, "constants", MappingProxyType(copied_constants))

    def solve(self) -> Mapping[VariableT, Regex]:
        """Solve every variable by ordered Arden elimination.

        Each pivot isolates its self coefficient, substitutes the factored
        row into later equations, then back-substitution resolves the saved
        rows. A nullable effective diagonal violates the unique-solution
        form of Arden's lemma and is rejected. The source system is unchanged.

        Returns
        -------
        Mapping[VariableT, Regex]
            Read-only mapping containing one fresh immutable Regex per
            declared variable, in the system's variable order.

        Raises
        ------
        ValueError
            If a pivot coefficient accepts epsilon.

        Complexity
        ----------
        For n variables, m supplied coefficients, H total operand-alphabet
        entries and s distinct symbols, dense initialization uses O(n² + m)
        references. Elimination performs O(n³) algebraic updates. Each AST
        constructor shares subtrees but union equality and pivot nullability
        can traverse expressions. Let C be their total traversal/copying
        cost: time is O(n³ + n² + m + H + n*s + C), not merely cubic; n*s
        accounts for alphabet copies into the returned Regex values.
        Generated ASTs have O(n³) node references before normalization, but
        unfolded expressions and their rendered strings can be exponential
        in n. Peak memory includes O(n²) table references, generated nodes,
        O(n*s) output alphabets and recursion stacks. Rendering is separate and at least
        linear in the rendered length.

        References
        ----------
        Professor requirement #58; #57's shared private nullable-pivot
        check and Arden multiplier. No automaton conversion is used here.
        """
        ordered = self.variables
        symbols: set[str] = set()
        coefficients: dict[VariableT, dict[VariableT, _ast.Node]] = {}
        constants: dict[VariableT, _ast.Node] = {}
        for source in ordered:
            source_constant = self.constants[source]
            symbols.update(source_constant._symbols)
            constants[source] = source_constant._root
            row: dict[VariableT, _ast.Node] = {}
            for target in ordered:
                coefficient = self.coefficients[source].get(target)
                if coefficient is None:
                    row[target] = _ast.EMPTY
                else:
                    symbols.update(coefficient._symbols)
                    row[target] = coefficient._root
            coefficients[source] = row

        rows: dict[
            VariableT, tuple[_ast.Node, dict[VariableT, _ast.Node], _ast.Node]
        ] = {}
        for position, state in enumerate(ordered):
            later = ordered[position + 1:]
            multiplier = _arden_multiplier(coefficients[state][state], state)
            row = {target: coefficients[state][target] for target in later}
            rows[state] = (multiplier, row, constants[state])

            for successor in later:
                incoming = coefficients[successor][state]
                if isinstance(incoming, _ast.EmptyLanguage):
                    continue
                route = _ast.concatenate(incoming, multiplier)
                for target in later:
                    via = _ast.concatenate(route, row[target])
                    coefficients[successor][target] = _ast.union(
                        via, coefficients[successor][target]
                    )
                constants[successor] = _ast.union(
                    _ast.concatenate(route, constants[state]),
                    constants[successor],
                )
                coefficients[successor][state] = _ast.EMPTY

        solutions: dict[VariableT, _ast.Node] = {}
        for position in range(len(ordered) - 1, -1, -1):
            state = ordered[position]
            multiplier, row, saved_constant = rows[state]
            remainder = saved_constant
            for target in ordered[position + 1:]:
                remainder = _ast.union(
                    _ast.concatenate(row[target], solutions[target]), remainder
                )
            solutions[state] = _ast.concatenate(multiplier, remainder)

        return MappingProxyType({
            state: Regex._from_ast(solutions[state], symbols) for state in ordered
        })
