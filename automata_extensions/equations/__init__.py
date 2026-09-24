"""Rational-language equation solvers."""

from automata_extensions.equations.arden import solve_arden
from automata_extensions.equations.system import SystemOfEquations

__all__ = ["solve_arden", "SystemOfEquations"]
