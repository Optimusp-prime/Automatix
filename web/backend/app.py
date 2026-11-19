"""Run from the repository root: python -m uvicorn web.backend.app:app."""
from fastapi import FastAPI

from web.backend.models import DFADraft, ValidationResult
from web.backend.validation import validate_draft
from web.backend.algorithms import run_algorithm

app = FastAPI(title="Automatix — API du POC DFA", version="0.1.0")
app.post("/api/algorithms/regex")(run_algorithm)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Return service availability.

    Returns
    -------
    dict[str, str]
        A static status message.

    Complexity
    ----------
    O(1) time and space.
    """
    return {"status": "ok"}


@app.post("/api/dfa/validate", response_model=ValidationResult)
def validate(draft: DFADraft) -> ValidationResult:
    """Report DFA errors without changing or persisting the submitted draft.

    Parameters
    ----------
    draft : DFADraft
        States, alphabet and transitions; schema failures produce HTTP 422.

    Returns
    -------
    ValidationResult
        HTTP 200 for both valid and semantically invalid drafts.

    Complexity
    ----------
    O(Q * S + E) expected time and space; see validate_draft.
    """
    return validate_draft(draft)
