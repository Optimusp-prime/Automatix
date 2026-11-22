"""Local web adapter; existing library algorithms run in a bounded worker."""
import json
import subprocess
import sys
from pathlib import Path
from typing import Literal, cast

from fastapi import HTTPException
from pydantic import Field

from web.backend.models import DFADraft, TransportModel


class AlgorithmRequest(TransportModel):
    """Explicit alphabet and optional source DFA for regex conversions."""

    operation: Literal["to_regex", "from_regex", "from_regex_minimized"]
    draft: DFADraft
    expression: str = Field(default="", max_length=120)


def run_algorithm(request: AlgorithmRequest) -> dict[str, object]:
    """Run an immutable conversion with a 15-second worker deadline.

    Parameters
    ----------
    request : AlgorithmRequest
        Operation, current alphabet and source drawing/expression.

    Returns
    -------
    dict
        Regex text or a bounded DFA transport document.

    Raises
    ------
    HTTPException
        Invalid input, computation limit or unavailable worker.

    Complexity
    ----------
    Serialization is O(Q + E + expression length). DFA-to-regex minimizes,
    then eliminates states greedily (O(n**3) label operations); only the
    rendered text can be exponential, so it is capped at 1,000,000
    characters. Regex-to-DFA can be exponential; the isolated worker has a
    wall-clock and memory budget.
    """
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "web.backend.algorithm_worker"],
            input=request.model_dump_json(), capture_output=True, text=True,
            timeout=15, cwd=Path(__file__).resolve().parents[2],
        )
    except subprocess.TimeoutExpired as error:
        raise HTTPException(408, "Calcul trop long. Simplifiez l’expression ou l’automate.") from error
    if completed.returncode:
        raise HTTPException(422, "Limite de calcul atteinte. Simplifiez l’entrée.")
    result = cast(dict[str, object], json.loads(completed.stdout))
    if "error" in result:
        raise HTTPException(422, result["error"])
    return result
