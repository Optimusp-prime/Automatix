"""HTTP contract of the optional DFA editor adapter."""
from copy import deepcopy
from typing import Any

import pytest
pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient
from web.backend.app import app
from web.backend.models import DFADraft
from web.backend.validation import validate_draft


@pytest.fixture
def draft() -> dict[str, Any]:
    return {"alphabet": ["a", "b"], "states": [
        {"id": "s0", "label": "q0", "initial": True, "final": False},
        {"id": "s1", "label": "q1", "initial": False, "final": True}],
        "transitions": [
            {"id": "e0", "source": "s0", "target": "s1", "symbol": "a"},
            {"id": "e1", "source": "s0", "target": "s0", "symbol": "b"},
            {"id": "e2", "source": "s1", "target": "s1", "symbol": "a"},
            {"id": "e3", "source": "s1", "target": "s0", "symbol": "b"}]}


def check(payload: dict[str, Any]) -> dict[str, Any]:
    response = TestClient(app).post("/api/dfa/validate", json=payload)
    assert response.status_code == 200, response.text
    result: dict[str, Any] = response.json()
    return result


def test_real_automatix_validation(draft: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    from automata_extensions.fa import ExtendedDFA
    calls: list[ExtendedDFA] = []
    original = ExtendedDFA.validate
    def observe(self: ExtendedDFA) -> None:
        calls.append(self)
        original(self)
    monkeypatch.setattr(ExtendedDFA, "validate", observe)
    assert check(draft) == {"valid": True, "issues": []}
    assert calls and not calls[-1].allow_partial
    assert calls[-1].accepts("a") and not calls[-1].accepts("ab")


def test_missing_transition_localized(draft: dict[str, Any]) -> None:
    draft["transitions"].pop()
    result = check(draft)
    assert not result["valid"]
    issue = next(i for i in result["issues"] if i["code"] == "missing_transition")
    assert issue["state_id"] == "s1" and issue["symbol"] == "b"


@pytest.mark.parametrize("target", ["s0", "s1"])
def test_duplicate_transition_not_overwritten(draft: dict[str, Any], target: str) -> None:
    draft["transitions"].append({"id": "extra", "source": "s0", "target": target, "symbol": "a"})
    assert "duplicate_transition" in {i["code"] for i in check(draft)["issues"]}


@pytest.mark.parametrize("field,code", [("source", "unknown_state"), ("target", "unknown_state"), ("symbol", "unknown_symbol")])
def test_edge_errors(draft: dict[str, Any], field: str, code: str) -> None:
    draft["transitions"][0][field] = "missing"
    assert any(i["code"] == code and i["transition_id"] == "e0" for i in check(draft)["issues"])


@pytest.mark.parametrize("symbol", ["", "ε", "ab", " ", "\n"])
def test_invalid_symbols(draft: dict[str, Any], symbol: str) -> None:
    draft["alphabet"] = [symbol]
    assert "invalid_symbol" in {i["code"] for i in check(draft)["issues"]}


def test_empty_alphabet_no_finals_allowed() -> None:
    assert check({"alphabet": [], "states": [{"id": "q", "label": "q", "initial": True, "final": False}], "transitions": []})["valid"]


def test_no_finals_unreachable_states_allowed(draft: dict[str, Any]) -> None:
    for state in draft["states"]:
        state["final"] = False
    draft["states"].append({"id": "trap", "label": "p", "initial": False, "final": False})
    for symbol in draft["alphabet"]:
        draft["transitions"].append({"id": "trap-" + symbol, "source": "trap", "target": "trap", "symbol": symbol})
    assert check(draft)["valid"]


@pytest.mark.parametrize("initials", [[False, False], [True, True]])
def test_one_initial(draft: dict[str, Any], initials: list[bool]) -> None:
    for state, initial in zip(draft["states"], initials):
        state["initial"] = initial
    assert "initial_state" in {i["code"] for i in check(draft)["issues"]}


@pytest.mark.parametrize("case,code", [("id", "duplicate_state"), ("label", "duplicate_label"), ("blank", "invalid_label"), ("edge", "duplicate_edge_id"), ("alphabet", "duplicate_symbol")])
def test_duplicates(draft: dict[str, Any], case: str, code: str) -> None:
    if case in ("id", "label"):
        draft["states"][1][case] = draft["states"][0][case]
    elif case == "blank":
        draft["states"][1]["label"] = " "
    elif case == "edge":
        draft["transitions"][1]["id"] = "e0"
    else:
        draft["alphabet"].append("a")
    assert code in {i["code"] for i in check(draft)["issues"]}


def test_empty_draft() -> None:
    assert not check({"alphabet": ["a"], "states": [], "transitions": []})["valid"]


def test_immutability(draft: dict[str, Any]) -> None:
    before = deepcopy(draft)
    model = DFADraft.model_validate(draft)
    snapshot = model.model_dump()
    assert validate_draft(model).valid
    assert model.model_dump() == snapshot and draft == before


def test_malformed_requests(draft: dict[str, Any]) -> None:
    client = TestClient(app)
    assert client.post("/api/dfa/validate", json={}).status_code == 422
    draft["states"][0]["initial"] = "true"
    assert client.post("/api/dfa/validate", json=draft).status_code == 422
    draft["states"] *= 101
    assert client.post("/api/dfa/validate", json=draft).status_code == 422


def test_health_and_schema() -> None:
    client = TestClient(app)
    assert client.get("/api/health").json() == {"status": "ok"}
    assert "/api/dfa/validate" in client.get("/openapi.json").json()["paths"]
