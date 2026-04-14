from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pymupdf

from aerobim.domain.models import (
    ClashResult,
    ComparisonOperator,
    DrawingAnnotation,
    DrawingAsset,
    FindingCategory,
    ParsedRequirement,
    ProblemZone,
    RuleScope,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore

SMOKE_REPORT_ID = "9" * 32
SMOKE_REQUEST_ID = "runtime-smoke-seed"
SMOKE_RULE_ID = "SMOKE-DRAW-001"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_ifc_fixture() -> Path:
    return repo_root() / "samples" / "ifc" / "walls-multi-entity.ifc"


def default_storage_dir() -> Path:
    return Path(os.getenv("AEROBIM_STORAGE_DIR", "var/reports"))


def _copy_ifc_fixture(storage_dir: Path, source_ifc_path: Path) -> Path:
    target_dir = storage_dir / "models"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / "smoke-review.ifc"
    shutil.copy2(source_ifc_path, target_path)
    return target_path.resolve()


def _extract_product_guids(ifc_path: Path) -> list[str]:
    import ifcopenshell

    model = ifcopenshell.open(str(ifc_path))
    guids = [getattr(entity, "GlobalId", "") for entity in model.by_type("IfcProduct")]
    materialized = [guid for guid in guids if guid]
    if len(materialized) < 2:
        raise ValueError("Smoke report seeding requires an IFC fixture with at least two product GUIDs")
    return materialized


def _create_smoke_pdf(storage_dir: Path) -> Path:
    input_dir = storage_dir / "smoke-inputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = input_dir / "smoke-review-sheet.pdf"

    document = pymupdf.open()
    first_page = document.new_page(width=320, height=200)
    first_page.insert_text((24, 40), "WALL-01 thickness 150 mm")
    first_page.insert_text((24, 80), "Overlay target region for runtime smoke")
    second_page = document.new_page(width=320, height=200)
    second_page.insert_text((24, 40), "A-101 browse page for 2D evidence switching")
    second_page.insert_text((24, 80), "Use this page to confirm browse mode without overlay")
    document.save(pdf_path)
    document.close()
    return pdf_path.resolve()


def seed_smoke_report(storage_dir: Path, source_ifc_path: Path | None = None) -> ValidationReport:
    storage_dir = storage_dir.resolve()
    storage_dir.mkdir(parents=True, exist_ok=True)

    ifc_fixture_path = (source_ifc_path or default_ifc_fixture()).resolve()
    if not ifc_fixture_path.exists():
        raise FileNotFoundError(ifc_fixture_path)

    seeded_ifc_path = _copy_ifc_fixture(storage_dir, ifc_fixture_path)
    drawing_pdf_path = _create_smoke_pdf(storage_dir)
    product_guids = _extract_product_guids(seeded_ifc_path)

    report = ValidationReport(
        report_id=SMOKE_REPORT_ID,
        request_id=SMOKE_REQUEST_ID,
        ifc_path=seeded_ifc_path,
        created_at=datetime.now(tz=UTC).isoformat(),
        requirements=(
            ParsedRequirement(
                rule_id=SMOKE_RULE_ID,
                ifc_entity="IFCWALL",
                rule_scope=RuleScope.DRAWING_ANNOTATION,
                target_ref="WALL-01",
                property_name="thickness",
                operator=ComparisonOperator.GREATER_OR_EQUAL,
                expected_value="200",
                unit="mm",
                source="smoke-seed",
            ),
        ),
        issues=(
            ValidationIssue(
                rule_id=SMOKE_RULE_ID,
                severity=Severity.ERROR,
                message="Smoke seed issue for runtime 2D and 3D review.",
                ifc_entity="IFCWALL",
                category=FindingCategory.DRAWING_VALIDATION,
                target_ref="WALL-01",
                property_name="thickness",
                operator=ComparisonOperator.GREATER_OR_EQUAL,
                expected_value="200",
                observed_value="150",
                unit="mm",
                element_guid=product_guids[0],
                problem_zone=ProblemZone(
                    sheet_id="A-101",
                    page_number=1,
                    x=30,
                    y=40,
                    width=80,
                    height=50,
                    element_guid=product_guids[0],
                ),
            ),
        ),
        summary=ValidationSummary(
            requirement_count=1,
            issue_count=1,
            error_count=1,
            warning_count=0,
            passed=False,
            drawing_annotation_count=1,
            generated_remark_count=0,
        ),
        drawing_annotations=(
            DrawingAnnotation(
                annotation_id="smoke-annotation-001",
                sheet_id="A-101",
                target_ref="WALL-01",
                measure_name="thickness",
                observed_value="150",
                unit="mm",
                problem_zone=ProblemZone(
                    sheet_id="A-101",
                    page_number=1,
                    x=30,
                    y=40,
                    width=80,
                    height=50,
                    element_guid=product_guids[0],
                ),
                source="smoke-seed",
            ),
        ),
        drawing_assets=(
            DrawingAsset(
                asset_id="smoke-drawing",
                sheet_id="A-101",
                media_type="application/pdf",
                source_path=drawing_pdf_path,
            ),
        ),
        clash_results=(
            ClashResult(
                element_a_guid=product_guids[0],
                element_b_guid=product_guids[1],
                clash_type="hard",
                distance=0.03,
                description="Smoke seed clash pair for runtime review.",
            ),
        ),
        project_name="Smoke Demo Project",
        discipline="architecture",
    )

    store = FilesystemAuditStore(storage_dir)
    store.save(report)
    return store.get(report.report_id) or report


def build_cli_payload(report: ValidationReport) -> dict[str, object]:
    first_asset = report.drawing_assets[0] if report.drawing_assets else None
    return {
        "report_id": report.report_id,
        "request_id": report.request_id,
        "project_name": report.project_name,
        "discipline": report.discipline,
        "ifc_path": str(report.ifc_path),
        "drawing_asset_ids": [asset.asset_id for asset in report.drawing_assets],
        "issue_rule_ids": [issue.rule_id for issue in report.issues],
        "clash_pairs": [
            {
                "element_a_guid": clash.element_a_guid,
                "element_b_guid": clash.element_b_guid,
            }
            for clash in report.clash_results
        ],
        "suggested_checks": {
            "report": f"/v1/reports/{report.report_id}",
            "ifc_source": f"/v1/reports/{report.report_id}/source/ifc",
            "drawing_preview": (
                f"/v1/reports/{report.report_id}/drawing-assets/{first_asset.asset_id}/preview"
                if first_asset is not None
                else None
            ),
            "html_export": f"/v1/reports/{report.report_id}/export/html",
            "bcf_export": f"/v1/reports/{report.report_id}/export/bcf",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a deterministic persisted report for AeroBIM runtime smoke")
    parser.add_argument("--storage-dir", type=Path, default=None, help="Target AEROBIM storage directory")
    parser.add_argument("--ifc-fixture", type=Path, default=None, help="Override the default IFC fixture path")
    args = parser.parse_args()

    report = seed_smoke_report(args.storage_dir or default_storage_dir(), args.ifc_fixture)
    print(json.dumps(build_cli_payload(report), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()