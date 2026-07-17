"""Relational IFC knowledge-graph query (I9 advisory) — IfcLLM-inspired, no LLM.

Deterministic ifcopenshell by_type / name keyword routing. Never writes summary.passed.
Do **not** cite IfcLLM 93–100% figures as AeroBIM product accuracy.
"""

from __future__ import annotations

import re
from pathlib import Path

from aerobim.domain.tz_architecture_ports import IfcKnowledgeQueryResult

_ENTITY_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("стен", "wall", "стена", "стены"), "IfcWall"),
    (("колон", "column", "pillar"), "IfcColumn"),
    (("балка", "beam", "балок"), "IfcBeam"),
    (("плит", "slab", "перекрыт"), "IfcSlab"),
    (("двер", "door"), "IfcDoor"),
    (("окн", "window"), "IfcWindow"),
    (("пространств", "space", "помещен"), "IfcSpace"),
    (("труб", "pipe", "duct", "воздуховод"), "IfcFlowSegment"),
)


class RelationalIfcKnowledgeGraph:
    """Advisory NL→GUID via relational IFC scan (graph topology deferred).

    Backend label ``relational`` distinguishes from stub. Multi-hop GraphRAG
    remains planned — this adapter is the honest deterministic first slice.
    """

    def query_nl(self, question: str, *, ifc_path: Path) -> IfcKnowledgeQueryResult:
        cleaned = (question or "").strip()
        if not cleaned:
            return IfcKnowledgeQueryResult(
                question=cleaned,
                element_guids=(),
                facts=("empty question",),
                backend="relational",
                degraded=True,
                reason="Empty NL query",
            )
        if not ifc_path.exists():
            return IfcKnowledgeQueryResult(
                question=cleaned,
                element_guids=(),
                facts=(),
                backend="relational",
                degraded=True,
                reason=f"IFC path missing: {ifc_path}",
            )

        try:
            import ifcopenshell
        except ModuleNotFoundError:
            return IfcKnowledgeQueryResult(
                question=cleaned,
                element_guids=(),
                facts=(),
                backend="relational",
                degraded=True,
                reason="ifcopenshell not installed",
            )

        try:
            model = ifcopenshell.open(str(ifc_path))
        except Exception as exc:  # noqa: BLE001
            return IfcKnowledgeQueryResult(
                question=cleaned,
                element_guids=(),
                facts=(),
                backend="relational",
                degraded=True,
                reason=f"IFC open failed: {exc}",
            )

        lower = cleaned.casefold()
        entity_type = "IfcProduct"
        for hints, ifc_type in _ENTITY_HINTS:
            if any(hint in lower for hint in hints):
                entity_type = ifc_type
                break

        guids: list[str] = []
        try:
            elements = model.by_type(entity_type)
        except Exception:  # noqa: BLE001
            elements = []
        for element in elements[:50]:
            guid = getattr(element, "GlobalId", None)
            if guid:
                guids.append(str(guid))

        name_tokens = re.findall(r"[A-Za-zА-Яа-я0-9_-]{3,}", cleaned)
        name_hits = 0
        if name_tokens and entity_type == "IfcProduct":
            for element in model.by_type("IfcProduct")[:200]:
                name = str(getattr(element, "Name", "") or "")
                if any(token.casefold() in name.casefold() for token in name_tokens):
                    guid = getattr(element, "GlobalId", None)
                    if guid and str(guid) not in guids:
                        guids.append(str(guid))
                        name_hits += 1
                    if len(guids) >= 50:
                        break

        return IfcKnowledgeQueryResult(
            question=cleaned,
            element_guids=tuple(guids),
            facts=(
                f"entity_type={entity_type}",
                f"guid_count={len(guids)}",
                f"name_hits={name_hits}",
                "advisory-only; DeterminismGate owns sign-off",
            ),
            backend="relational",
            degraded=False,
            reason=(
                "Relational ifcopenshell keyword route (not GraphRAG LLM; "
                "not IfcLLM product accuracy)"
            ),
        )
