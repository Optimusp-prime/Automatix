"""Arden's lemma for one left-coefficient rational-language equation."""

from automata_extensions.regex import Regex, _ast


def solve_arden(coefficient: Regex, constant: Regex) -> Regex:
    """Solve ``X = A X ∪ B`` as the unique solution ``A* B``.

    The coefficient ``A`` must not accept epsilon. The source expressions
    remain unchanged, and the result retains symbols declared by either one.

    Parameters
    ----------
    coefficient : Regex
        The expression ``A`` multiplying the unknown on the left.
    constant : Regex
        The expression ``B`` independent of the unknown.

    Returns
    -------
    Regex
        A fresh immutable expression for the unique solution ``A* B``.

    Raises
    ------
    TypeError
        If either operand is not a ``Regex``.
    ValueError
        If epsilon belongs to the coefficient language, so the theorem's
        uniqueness condition does not hold.

    Algorithm
    ---------
    Check nullability of ``A`` on its immutable AST, then build ``Star(A)``
    followed by ``B`` with the existing private normalization constructors.
    The AST subtrees are structurally shared; no expression is reparsed.

    Complexity
    ----------
    Let |A| be the unfolded AST size visited by nullability and ΣA, ΣB be
    the operand alphabets. Time is O(|A| + |ΣA| + |ΣB|); auxiliary space is
    O(depth(A) + |ΣA ∪ ΣB|), including the recursion stack and merged alphabet.
    Rendering later costs at least O(output length); the existing renderer
    may also copy intermediate strings along the AST depth.

    References
    ----------
    Professor requirement #57; Arden's lemma, unique-solution form.
    """
    if not isinstance(coefficient, Regex) or not isinstance(constant, Regex):
        raise TypeError("coefficient and constant must be Regex values")
    if _ast.nullable(coefficient._root):
        raise ValueError("Arden's lemma requires epsilon outside the coefficient language")
    root = _ast.concatenate(_ast.star(coefficient._root), constant._root)
    return Regex._from_ast(root, coefficient._symbols | constant._symbols)
