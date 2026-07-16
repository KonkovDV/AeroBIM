"""Optional LLM assist for IDS drafting — advisory only (W3.6).

Never wire into AnalyzeProjectPackageUseCase or any sign-off path.
Human review of generated IDS is mandatory before use as EIR/acceptance criteria.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class IdsAssistDraft:
    """Suggested IDS fragment — not a validated requirement source."""

    suggested_ids_xml: str
    rationale: str
    confidence: float
    advisory_only: bool = True


class IdsAssistDraftPort(Protocol):
    """Port for optional IDS drafting assistance."""

    def draft_from_narrative(self, narrative: str) -> IdsAssistDraft: ...


class StubIdsAssistDraftAdapter:
    """Advisory IDS draft stub.

    /** @sota-stub */
    LLM IDS assist is intentionally outside the sign-off path.
    """

    def draft_from_narrative(self, narrative: str) -> IdsAssistDraft:
        _ = narrative
        return IdsAssistDraft(
            suggested_ids_xml="",
            rationale=(
                "IDS assist is advisory-only. Generated drafts must be reviewed by a "
                "human before use; they never affect summary.passed or pilot sign-off."
            ),
            confidence=0.0,
            advisory_only=True,
        )
