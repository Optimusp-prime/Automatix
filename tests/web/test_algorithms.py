"""Exercise the actual subprocess API and verify resulting languages."""
from itertools import product
from typing import Any

import pytest
pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient
from web.backend.app import app
from automata_extensions.fa import ExtendedDFA
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
