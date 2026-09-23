"""Cycle analysis of finite-automaton transition graphs."""

from automata.fa.fa import FAStateT

from automata_extensions.fa.fa_mixins.graph import _build_successors, _GraphSource


class CycleMixin:
    """Detect directed cycles through DFS back edges."""

    def has_cycle(self: _GraphSource) -> bool:
        """Return whether any state belongs to a directed cycle.

        Search the entire graph, including components inaccessible from the
        initial state. A self-loop is a cycle. No automaton data is changed or
        cached.

        Returns
        -------
        bool
            True if a DFS edge reaches a state still on its active path;
            False if every DFS finishes without such an edge.

        Complexity
        ----------
        Adjacency construction takes O(|Q| + T) time and O(|Q| + |E|)
        space, where Q is all states, E the emitted transitions (including
        parallel edges), and T exhausts iter_transitions. DFS takes
        O(|Q| + |E|) time and O(|Q|) additional space, including the
        recursion stack. Overall: O(|Q| + T) time and O(|Q| + |E|) space,
        assuming constant-time state hashing and equality. T includes
        NFA empty target entries and GNFA stored None labels. A sufficiently
        deep graph may exceed Python's recursion limit.

        References
        ----------
        Professor requirement #11: DFS back-edge cycle detection, as
        supplied in the task prompt; the source PDFs were not accessed.
        ADR-0004: common graph foundation. ADR-0009: global cycle analysis.
        """
        successors = _build_successors(self)
        gray = 1
        black = 2
        colors: dict[FAStateT, int] = {}

        def visit(state: FAStateT) -> bool:
            colors[state] = gray
            for neighbor in successors[state]:
                if colors.get(neighbor) == gray:
                    return True
                if neighbor not in colors and visit(neighbor):
                    return True
            colors[state] = black
            return False

        for state in successors:
            if state not in colors and visit(state):
                return True
        return False
