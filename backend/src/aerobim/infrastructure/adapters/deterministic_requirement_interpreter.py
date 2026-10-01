"""RequirementInterpreterPort — wraps deterministic IDS compiler (TZ alias)."""

from __future__ import annotations

from typing import Literal

from aerobim.domain.models import RequirementSource, SourceKind
from aerobim.domain.ports import RequirementToIdsCompiler
from aerobim.domain.tz_architecture_ports import MachineCheckableRule


class DeterministicRequirementInterpreter:
    """NL/TZ text → MachineCheckableRule via existing RequirementToIdsCompiler family.

    ``mode=llm_assisted`` stays advisory-only and currently degrades to deterministic
    (LLM IDS assist remains ``@sota-stub`` elsewhere).
    """

    def __init__(self, compiler: RequirementToIdsCompiler) -> None:
        self._compiler = compiler

    def interpret(
        self,
        tz_text: str,
        *,
        locale: Literal["ru", "en"] = "ru",
        mode: Literal["deterministic", "llm_assisted"] = "deterministic",
    ) -> list[MachineCheckableRule]:
        _ = mode  # llm_assisted not productized — same deterministic path
        source = RequirementSource(
            text=tz_text or "",
            source_kind=SourceKind.TECHNICAL_SPECIFICATION,
        )
        draft = self._compiler.compile(source)
        if not draft.suggested_ids_xml.strip():
            return []
        rase = tuple(draft.rase_elements) if draft.rase_elements else ()
        if not rase and draft.source_requirement_count > 0:
            # Compiler may omit RASE on empty extract path; keep advisory tag floor.
            rase = ("R",)
        return [
            MachineCheckableRule(
                rule_id="AEROBIM-INTERPRET-IDS-DRAFT",
                ids_fragment_or_dsl=draft.suggested_ids_xml,
                rase_elements=rase,  # type: ignore[arg-type]
                source_span=None,
                locale=locale,
                confidence=float(draft.confidence),
                advisory_only=True,
            )
        ]
