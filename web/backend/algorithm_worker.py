"""Private, short-lived conversion worker; no source automaton is mutated."""
import json
import sys
from collections import deque

from automata.base.exceptions import AutomatonException
from automata_extensions.fa import ExtendedDFA
from automata_extensions.regex import Regex
from web.backend.algorithms import AlgorithmRequest
from web.backend.validation import validate_draft

MAX_EXPRESSION_LENGTH = 1_000_000


def _thousands(value: int) -> str:
    """French digit grouping with a narrow no-break space."""
    return f"{value:_}".replace("_", "\u202f")


def _convert(request: AlgorithmRequest) -> dict[str, object]:
    alphabet = set(request.draft.alphabet)
    reserved = set("|*()+?&^.[]{}\\ε∅")
    if len(alphabet) != len(request.draft.alphabet) or any(
        len(s) != 1 or s.isspace() or s in reserved for s in alphabet
    ):
        raise ValueError("Alphabet : caractères uniques, sans espaces ni opérateurs d’expression régulière.")
    if request.operation == "to_regex":
        validation = validate_draft(request.draft)
        if not validation.valid:
            raise ValueError(validation.issues[0].message)
        paths: dict[str, dict[str, str]] = {s.id: {} for s in request.draft.states}
        for e in request.draft.transitions:
            paths[e.source][e.symbol] = e.target
        dfa = ExtendedDFA(states=set(paths), input_symbols=alphabet, transitions=paths,
                          initial_state=next(s.id for s in request.draft.states if s.initial),
                          final_states={s.id for s in request.draft.states if s.final})
        # The verbose lexical #53 trace explodes beyond a dozen states; the
        # minimal DFA with greedy elimination keeps large automata tractable.
        expression = dfa.minimize().to_regex_heuristic()
        text = "∅" if expression is None else expression or "ε"
        if len(text) > MAX_EXPRESSION_LENGTH:
            raise ValueError(
                f"L’expression équivalente compte {_thousands(len(text))} caractères "
                f"(maximum {_thousands(MAX_EXPRESSION_LENGTH)}). Ce langage n’admet pas "
                "d’expression compacte avec cette méthode ; réduisez l’automate.")
        return {"kind": "regex", "expression": text}
    if request.expression == "∅":
        dfa = ExtendedDFA(states={0}, input_symbols=alphabet, initial_state=0,
                          final_states=set(), transitions={0: {s: 0 for s in alphabet}})
    else:
        dfa = Regex(request.expression.replace("ε", "()"), input_symbols=alphabet).to_dfa()
    if request.operation == "from_regex_minimized":
        dfa = dfa.minimize()
    # Stable BFS names avoid leaking compound mathematical state representations.
    names = {dfa.initial_state: "q0"}
    queue = deque([dfa.initial_state])
    transitions: list[dict[str, str]] = []
    while queue:
        state = queue.popleft()
        for symbol in sorted(alphabet):
            target = dfa.transitions[state][symbol]
            if target not in names:
                names[target] = f"q{len(names)}"
                queue.append(target)
            transitions.append({"id": f"t{len(transitions)}", "source": names[state],
                                "target": names[target], "symbol": symbol})
            if len(names) > 200 or len(transitions) > 4000:
                raise ValueError("Résultat trop grand : maximum 200 états et 4 000 transitions.")
    return {"kind": "dfa", "draft": {"alphabet": sorted(alphabet),
            "states": [{"id": name, "label": name, "initial": state == dfa.initial_state,
                        "final": state in dfa.final_states} for state, name in names.items()],
            "transitions": transitions}}


if __name__ == "__main__":
    try:
        # Linux/WSL worker only; never alter the API server's resource limits.
        if sys.platform == "linux":
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
        output = _convert(AlgorithmRequest.model_validate_json(sys.stdin.read()))
    except (ValueError, AutomatonException) as error:
        output = {"error": str(error)}
    except (RecursionError, MemoryError):
        output = {"error": "Calcul trop volumineux pour la mémoire disponible. "
                           "Simplifiez l’expression ou l’automate avant de réessayer."}
    print(json.dumps(output))
