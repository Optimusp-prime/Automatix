"""Transport schemas, intentionally separate from graphical coordinates."""
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

ShortText = Annotated[str, Field(max_length=64)]
Identifier = Annotated[str, Field(min_length=1, max_length=64)]


class TransportModel(BaseModel):
    """Reject coercions and extra fields at the HTTP boundary."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class DraftState(TransportModel):
    """An editable state, including incomplete user labels."""

    id: Identifier
    label: ShortText
    initial: bool
    final: bool


class DraftTransition(TransportModel):
    """One symbol per edge; a list preserves duplicate transition errors."""

    id: Identifier
    source: Identifier
    target: Identifier
    symbol: ShortText


class DFADraft(TransportModel):
    """Bounded draft; semantic invalidity is reported by the adapter."""

    alphabet: list[ShortText] = Field(max_length=128)
    states: list[DraftState] = Field(max_length=200)
    transitions: list[DraftTransition] = Field(max_length=4000)


class ValidationIssue(TransportModel):
    """Stable machine code, French message, and optional editor identifiers."""

    code: str
    message: str
    state_id: str | None = None
    transition_id: str | None = None
    symbol: str | None = None


class ValidationResult(TransportModel):
    """Semantic validation result (distinct from HTTP schema/network errors)."""

    valid: bool
    issues: list[ValidationIssue]
