"""AgenticReviewOrchestrator — TZ alias over ComplianceAgent + IFC KG tool.

Advisory only. DeterminismGate remains mandatory before persistence.
"""

from __future__ import annotations

from aerobim.application.services.compliance_agent_orchestrator import (
    ComplianceAgentOrchestrator,
)
from aerobim.domain.compliance_agent import AgentRunResult
from aerobim.domain.models import ValidationRequest


class AgenticReviewOrchestrator:
    """Thin application facade keeping the TZ name for Contour.AI_ADVISORY."""

    def __init__(self, *, compliance_agent: ComplianceAgentOrchestrator) -> None:
        self._agent = compliance_agent

    def run(self, request: ValidationRequest) -> AgentRunResult:
        return self._agent.run(request)
