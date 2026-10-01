"""Advisory LLM requirement extraction — never feeds summary.passed."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

ExtractionStatus = Literal["ok", "skipped", "failed"]


@dataclass(frozen=True)
class ExtractionCandidate:
    """Structured extraction candidate with mandatory evidence grounding fields.

    Candidates without ``evidence_refs`` are counted as hallucinations in eval
    harnesses. This port is advisory/experimental only.
    """

    rule_id: str | None
    ifc_entity: str | None
    property_set: str | None
    property_name: str | None
    expected_value: str | None
    evidence_refs: tuple[str, ...]
    confidence: float | None = None
    provider: str = "unknown"
    status: ExtractionStatus = "ok"
    unit: str | None = None
    operator: str | None = None


@runtime_checkable
class LlmExtractionPort(Protocol):
    """Extract requirement candidates from free/structured text (advisory)."""

    def extract_candidates(
        self, text: str, *, source_id: str | None = None
    ) -> list[ExtractionCandidate]: ...


__all__ = [
    "ExtractionCandidate",
    "ExtractionStatus",
    "LlmExtractionPort",
]
