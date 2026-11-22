"""Exercise the actual subprocess API and verify resulting languages."""
from itertools import product
from typing import Any

import pytest
pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient
from web.backend.app import app
from automata_extensions.fa import ExtendedDFA, ExtendedNFA
from automata_extensions.regex import Regex


def convert(operation: str, expression: str = "", draft: dict[str, Any] | None = None):
    return TestClient(app).post("/api/algorithms/regex", json={
        "operation": operation, "expression": expression,
        "draft": draft or {"alphabet": ["a", "b"], "states": [], "transitions": []}})


def automaton(draft: dict[str, Any]) -> ExtendedDFA:
    paths = {s["id"]: {} for s in draft["states"]}
    for edge in draft["transitions"]:
        paths[edge["source"]][edge["symbol"]] = edge["target"]
    return ExtendedDFA(states=set(paths), input_symbols=set(draft["alphabet"]),
                       transitions=paths, initial_state=next(s["id"] for s in draft["states"] if s["initial"]),
                       final_states={s["id"] for s in draft["states"] if s["final"]})


@pytest.mark.parametrize("expression", ["(a|b)*abb", "a|ab", "ε", "()", "", "∅"])
@pytest.mark.parametrize("operation", ["from_regex", "from_regex_minimized"])
def test_generated_complete_dfa_language(expression: str, operation: str) -> None:
    response = convert(operation, expression)
    assert response.status_code == 200, response.text
    dfa = automaton(response.json()["draft"])
    assert dfa.is_complete()
    expected = None if expression == "∅" else Regex(expression.replace("ε", "()"), input_symbols={"a", "b"}).to_dfa()
    for length in range(5):
        for chars in product("ab", repeat=length):
            word = "".join(chars)
            assert dfa.accepts_input(word) == (expected.accepts_input(word) if expected is not None else False)
    if operation.endswith("minimized"):
        assert len(dfa.states) == len(dfa.minimize().states)


def test_dfa_to_regex_round_trip_and_no_input_mutation() -> None:
    draft = convert("from_regex", "(a|b)*abb").json()["draft"]
    import copy
    before = copy.deepcopy(draft)
    response = convert("to_regex", draft=draft)
    assert response.status_code == 200, response.text
    result = Regex(response.json()["expression"], input_symbols={"a", "b"}).to_dfa()
    assert result == automaton(draft)
    assert draft == before


@pytest.mark.parametrize("expression", ["a|", "(", "c", "a+", "a b"])
def test_invalid_expression_returns_actionable_error(expression: str) -> None:
    response = convert("from_regex", expression)
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)


def test_incomplete_dfa_cannot_be_converted() -> None:
    response = convert("to_regex")
    assert response.status_code == 422


def test_worker_timeout_reports_controlled_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess
    from web.backend import algorithms
    def expire(*args: Any, **kwargs: Any) -> None:
        raise subprocess.TimeoutExpired("worker", 15)
    monkeypatch.setattr(algorithms.subprocess, "run", expire)
    assert convert("from_regex", "a").status_code == 408


def test_input_length_limit() -> None:
    assert convert("from_regex", "a" * 121).status_code == 422


def _draft(size: int, alphabet: str, step: dict[str, Any], finals: set[int]) -> dict[str, Any]:
    """Complete drawing whose state i goes to step[symbol](i) on symbol."""
    return {
        "alphabet": list(alphabet),
        "states": [{"id": f"s{i}", "label": f"q{i}", "initial": i == 0, "final": i in finals}
                   for i in range(size)],
        "transitions": [{"id": f"t{i}{c}", "source": f"s{i}", "target": f"s{step[c](i) % size}",
                         "symbol": c} for i in range(size) for c in alphabet],
    }


def _assert_regex_matches(draft: dict[str, Any], expression: str) -> None:
    """Independent oracle: Thompson (#51) then subset construction (#35)."""
    source = automaton(draft)
    text = "()" if expression == "ε" else expression
    oracle = ExtendedNFA.from_regex(text, input_symbols=source.input_symbols).determinize()
    assert oracle.is_equivalent(source)


@pytest.mark.parametrize("size", [13, 18, 25])
def test_regression_dfa_to_regex_beyond_twelve_states(size: int) -> None:
    """Regression: drawings above 12 states were refused by the worker."""
    import random
    rng = random.Random(size)
    targets = {c: [rng.randrange(size) for _ in range(size)] for c in "abc"}
    draft = _draft(size, "abc", {
        "a": lambda i: i + 1, "b": lambda i: targets["b"][i], "c": lambda i: targets["c"][i],
    }, {i for i in range(size) if rng.random() < 0.4} | {size - 1})
    response = convert("to_regex", draft=draft)
    assert response.status_code == 200, response.text
    assert len(response.json()["expression"]) < 200_000
    _assert_regex_matches(draft, response.json()["expression"])


def test_dfa_to_regex_at_editor_state_limit() -> None:
    """200 states (editor maximum): binary multiples of 200, non-minimal input."""
    draft = _draft(200, "01", {"0": lambda i: 2 * i, "1": lambda i: 2 * i + 1}, {0})
    response = convert("to_regex", draft=draft)
    assert response.status_code == 200, response.text
    _assert_regex_matches(draft, response.json()["expression"])


@pytest.mark.parametrize(("finals", "expected"), [(set(), "∅"), ({0}, None)])
def test_dfa_to_regex_empty_and_universal_languages(finals: set[int], expected: str | None) -> None:
    draft = _draft(20, "ab", {"a": lambda i: i + 1, "b": lambda i: i + 1}, finals)
    response = convert("to_regex", draft=draft)
    assert response.status_code == 200, response.text
    if expected is not None:
        assert response.json()["expression"] == expected
    else:
        _assert_regex_matches(draft, response.json()["expression"])


def test_oversized_expression_reports_its_length(monkeypatch: pytest.MonkeyPatch) -> None:
    from web.backend import algorithm_worker
    from web.backend.algorithms import AlgorithmRequest
    monkeypatch.setattr(algorithm_worker, "MAX_EXPRESSION_LENGTH", 10)
    draft = _draft(5, "ab", {"a": lambda i: i + 1, "b": lambda i: 2 * i}, {1, 3})
    request = AlgorithmRequest.model_validate({"operation": "to_regex", "draft": draft})
    with pytest.raises(ValueError, match="maximum 10"):
        algorithm_worker._convert(request)
