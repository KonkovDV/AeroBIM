"""IfcKnowledgeGraphPort stub — advisory NL→GUID path (I9 / IfcLLM-style).

/** @sota-stub */
Never implies product IFC understanding or summary.passed.
"""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.tz_architecture_ports import IfcKnowledgeQueryResult


class StubIfcKnowledgeGraph:
    """Fail-soft stub until relational/graph backends are productized.

    /** @sota-stub */
    Tracked as STUB-IFC-KG-001 in KNOWN_BUGS.md.
    """

    def query_nl(self, question: str, *, ifc_path: Path) -> IfcKnowledgeQueryResult:
        _ = ifc_path
        cleaned = (question or "").strip()
        return IfcKnowledgeQueryResult(
            question=cleaned,
            element_guids=(),
            facts=(
                "IfcKnowledgeGraphPort is advisory-only and not productized",
                "DeterminismGate must reconcile any future GUID hits before persistence",
            ),
            backend="stub",
            degraded=True,
            reason=(
                "STUB-IFC-KG-001: no relational/graph backend configured "
                "(IfcLLM-style hybrid deferred until customer IFC corpus)"
            ),
        )
