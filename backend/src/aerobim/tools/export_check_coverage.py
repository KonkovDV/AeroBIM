"""Export a per-source check-coverage map on a synthetic package (P0, verdict-neutral).

Демонстрирует карту покрытия комплекта («где система реально работала») на
СИНТЕТИЧЕСКОМ наборе — без реальных данных заказчика, без сети, без влияния на вердикт.
Показывает весь словарь статусов: checked_ok / checked_findings / not_checked /
insufficient_data / requires_expert + строку (unattributed).

Честные границы: это наблюдаемость на фикстуре, НЕ точность продукта; «нет находок» ≠
«не проверялось»; CHECKED_OK требует явной области (scope); карта не выставляет
summary.passed (ADR-001). Checkpoint NO_GO.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from aerobim.domain.check_coverage import build_check_coverage
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    ReportCapabilities,
    Severity,
    ValidationIssue,
)

_C = FindingCategory


def _issue(
    source_id: str | None, category: FindingCategory, *, origin: str = "deterministic"
) -> ValidationIssue:
    return ValidationIssue(
        rule_id="R",
        severity=Severity.ERROR,
        message="synthetic finding",
        category=category,
        source_id=source_id,
        origin=origin,  # type: ignore[arg-type]
    )


def synthetic_scenario() -> dict[str, Any]:
    """Return (source_ids, issues, capabilities, scope) as a coverage report dict."""
    capabilities = ReportCapabilities(
        ifc_validation=CapabilityStatus(CapabilityState.OK),
        ifc_schema=CapabilityStatus(CapabilityState.OK),
        ids=CapabilityStatus(CapabilityState.OK),
        section_pairing=CapabilityStatus(CapabilityState.OK),
        raster=CapabilityStatus(CapabilityState.FAILED, "OCR zero-yield on this sheet"),
        clash=CapabilityStatus(CapabilityState.SKIPPED, "clash not requested"),
    )
    source_ids = ["model.ifc", "AR_RD_sheet12.pdf", "req.ids", "sheet-12"]
    scope: dict[FindingCategory, set[str]] = {
        _C.IFC_VALIDATION: {"model.ifc"},
        _C.IDS_VALIDATION: {"req.ids"},
        _C.CROSS_DOCUMENT: {"AR_RD_sheet12.pdf", "model.ifc"},
        _C.DRAWING_VALIDATION: {"sheet-12"},
        _C.SPATIAL: {"model.ifc"},
    }
    issues = [
        _issue("model.ifc", _C.IFC_VALIDATION),  # deterministic -> CHECKED_FINDINGS
        _issue("AR_RD_sheet12.pdf", _C.CROSS_DOCUMENT, origin="advisory"),  # -> REQUIRES_EXPERT
        _issue("clash", _C.SPATIAL),  # synthetic source id -> (unattributed) row
    ]
    coverage = build_check_coverage(
        source_ids=source_ids, issues=issues, capabilities=capabilities, scope=scope
    )
    return coverage.to_dict()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export a synthetic check-coverage map (evidence)."
    )
    parser.add_argument("--output", type=Path, default=None, help="write JSON here (else stdout)")
    args = parser.parse_args(argv)
    text = json.dumps(synthetic_scenario(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
