"""Translate an editor draft into an immutable ExtendedDFA."""
from collections import Counter

from automata.base.exceptions import AutomatonException

from automata_extensions.fa import ExtendedDFA
from web.backend.models import DFADraft, ValidationIssue, ValidationResult


def validate_draft(draft: DFADraft) -> ValidationResult:
    """Validate a complete DFA draft, retaining error locations.

    Parameters
    ----------
    draft : DFADraft
        Parsed editor data. Neither the draft nor an existing DFA is mutated.

    Returns
    -------
    ValidationResult
        All adapter issues, or success after ExtendedDFA validation.

    Complexity
    ----------
    O(Q * S + E) expected time and space including reported missing transitions,
    where Q is states, S alphabet size and E transitions; strings are bounded.

    References
    ----------
    automata-lib 9.2.0 DFA.__init__, DFA.validate; ADR-0032.
    """
    issues: list[ValidationIssue] = []

    def report(code: str, message: str, state: str | None = None,
               edge: str | None = None, symbol: str | None = None) -> None:
        issues.append(ValidationIssue(code=code, message=message, state_id=state,
                                      transition_id=edge, symbol=symbol))

    alphabet = set(draft.alphabet)
    for symbol, count in Counter(draft.alphabet).items():
        if len(symbol) != 1 or symbol.isspace() or symbol == "ε":
            report("invalid_symbol", "Chaque symbole doit être un caractère non blanc, différent de ε.", symbol=symbol)
        if count > 1:
            report("duplicate_symbol", f"Le symbole « {symbol} » apparaît plusieurs fois dans l’alphabet.", symbol=symbol)

    if not draft.states:
        report("empty_states", "Ajoutez au moins un état.")
    ids: set[str] = set()
    labels: set[str] = set()
    for state in draft.states:
        if state.id in ids:
            report("duplicate_state", "Deux états partagent le même identifiant.", state.id)
        ids.add(state.id)
        label = state.label.strip()
        if not label:
            report("invalid_label", "Donnez un nom à cet état.", state.id)
        elif label in labels:
            report("duplicate_label", f"Le nom « {label} » est déjà utilisé.", state.id)
        labels.add(label)
    initial = [state.id for state in draft.states if state.initial]
    if len(initial) != 1:
        report("initial_state", "Définissez un unique état initial.")

    edge_ids: set[str] = set()
    counts: Counter[tuple[str, str]] = Counter()
    transitions: dict[str, dict[str, str]] = {state: {} for state in ids}
    for edge in draft.transitions:
        if edge.id in edge_ids:
            report("duplicate_edge_id", "Deux transitions partagent le même identifiant.", edge=edge.id)
        edge_ids.add(edge.id)
        endpoints_valid = edge.source in ids and edge.target in ids
        if not endpoints_valid:
            report("unknown_state", "Cette transition référence un état absent.", edge=edge.id)
        if edge.symbol not in alphabet:
            report("unknown_symbol", f"« {edge.symbol} » n’appartient pas à l’alphabet.", edge.source, edge.id, edge.symbol)
        key = (edge.source, edge.symbol)
        counts[key] += 1
        if counts[key] > 1:
            report("duplicate_transition", f"Plusieurs transitions lisent « {edge.symbol} » depuis cet état.", edge.source, edge.id, edge.symbol)
        if endpoints_valid and edge.symbol in alphabet and counts[key] == 1:
            transitions[edge.source][edge.symbol] = edge.target
    for state in draft.states:
        for symbol in dict.fromkeys(draft.alphabet):
            if (state.id, symbol) not in counts:
                report("missing_transition", f"{state.label} : transition manquante pour « {symbol} ».", state.id, symbol=symbol)
    if issues:
        return ValidationResult(valid=False, issues=issues)

    try:
        automaton = ExtendedDFA(states=ids, input_symbols=alphabet,
                               transitions=transitions, initial_state=initial[0],
                               final_states={s.id for s in draft.states if s.final},
                               allow_partial=False)
        # Explicit even if upstream's automatic constructor validation is disabled.
        automaton.validate()
    except AutomatonException:
        report("invalid_automaton", "Automatix ne peut pas valider cet automate. Vérifiez ses états et transitions.")
    return ValidationResult(valid=not issues, issues=issues)
