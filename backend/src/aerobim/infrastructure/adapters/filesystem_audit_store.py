from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict
from pathlib import Path

from aerobim.domain.models import (
    ClashResult,
    ComparisonOperator,
    DrawingAsset,
    DrawingAnnotation,
    FindingCategory,
    GeneratedRemark,
    ParsedRequirement,
    ProblemZone,
    ReportSummaryEntry,
    RuleScope,
    Severity,
    SourceKind,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)


class FilesystemAuditStore:
    """Persists validation reports as JSON files with atomic writes."""

    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = storage_dir
        self._reports_dir = storage_dir / "reports"
        self._drawing_assets_dir = storage_dir / "drawing-assets"
        self._reports_dir.mkdir(parents=True, exist_ok=True)
        self._drawing_assets_dir.mkdir(parents=True, exist_ok=True)

    def save(self, report: ValidationReport) -> str:
        persisted_report = self._materialize_report(report)
        data = self._serialize_report(persisted_report)
        target = self._reports_dir / f"{report.report_id}.json"
        tmp = self._reports_dir / f"{report.report_id}.tmp"
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(str(tmp), str(target))
        return report.report_id

    def _materialize_report(self, report: ValidationReport) -> ValidationReport:
        drawing_assets = tuple(self._materialize_drawing_assets(report.report_id, report.drawing_assets))
        return ValidationReport(
            report_id=report.report_id,
            request_id=report.request_id,
            ifc_path=report.ifc_path,
            created_at=report.created_at,
            requirements=report.requirements,
            issues=report.issues,
            summary=report.summary,
            drawing_annotations=report.drawing_annotations,
            drawing_assets=drawing_assets,
            clash_results=report.clash_results,
            project_name=report.project_name,
            discipline=report.discipline,
        )

    def _serialize_report(self, report: ValidationReport) -> dict[str, object]:
        data = asdict(report)
        data["ifc_path"] = str(report.ifc_path)
        data["drawing_assets"] = [
            {
                "asset_id": asset.asset_id,
                "sheet_id": asset.sheet_id,
                "page_number": asset.page_number,
                "media_type": asset.media_type,
                "coordinate_width": asset.coordinate_width,
                "coordinate_height": asset.coordinate_height,
                "stored_filename": asset.stored_filename,
            }
            for asset in report.drawing_assets
        ]
        return data

    def _materialize_drawing_assets(
        self,
        report_id: str,
        drawing_assets: tuple[DrawingAsset, ...],
    ) -> list[DrawingAsset]:
        if not drawing_assets:
            return []

        report_asset_dir = self._drawing_assets_dir / report_id
        if report_asset_dir.exists():
            shutil.rmtree(report_asset_dir)
        report_asset_dir.mkdir(parents=True, exist_ok=True)

        persisted_assets: list[DrawingAsset] = []
        for asset in drawing_assets:
            if asset.source_path is None:
                persisted_assets.append(asset)
                continue
            persisted_assets.extend(self._persist_document_asset(report_asset_dir, asset))
        return persisted_assets

    def _persist_document_asset(
        self,
        report_asset_dir: Path,
        asset: DrawingAsset,
    ) -> list[DrawingAsset]:
        try:
            import pymupdf
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Drawing asset preview generation requires PyMuPDF. Install the 'vision' extra."
            ) from exc

        source_path = asset.source_path
        if source_path is None:
            return [asset]
        if not source_path.exists():
            raise FileNotFoundError(source_path)

        if source_path.suffix.lower() != ".pdf":
            return [self._persist_raster_asset(report_asset_dir, asset, source_path, pymupdf)]

        persisted_assets: list[DrawingAsset] = []
        with pymupdf.open(source_path) as document:
            for page_index, page in enumerate(document, start=1):
                if asset.page_number is not None and page_index != asset.page_number:
                    continue
                pix = page.get_pixmap(dpi=144, annots=False)
                persisted_asset_id = asset.asset_id
                if document.page_count > 1 or asset.page_number is None:
                    persisted_asset_id = f"{asset.asset_id}-page-{page_index:03d}"
                stored_filename = f"{persisted_asset_id}.png"
                target_path = report_asset_dir / stored_filename
                pix.save(target_path)
                persisted_assets.append(
                    DrawingAsset(
                        asset_id=persisted_asset_id,
                        sheet_id=asset.sheet_id,
                        page_number=page_index,
                        media_type="image/png",
                        coordinate_width=float(page.rect.width),
                        coordinate_height=float(page.rect.height),
                        stored_filename=stored_filename,
                    )
                )
        return persisted_assets

    def _persist_raster_asset(self, report_asset_dir: Path, asset: DrawingAsset, source_path: Path, pymupdf_module) -> DrawingAsset:
        pix = pymupdf_module.Pixmap(str(source_path))
        stored_filename = f"{asset.asset_id}.png"
        target_path = report_asset_dir / stored_filename
        pix.save(target_path)
        return DrawingAsset(
            asset_id=asset.asset_id,
            sheet_id=asset.sheet_id,
            page_number=asset.page_number or 1,
            media_type="image/png",
            coordinate_width=float(pix.width),
            coordinate_height=float(pix.height),
            stored_filename=stored_filename,
        )

    def get(self, report_id: str) -> ValidationReport | None:
        target = self._reports_dir / f"{report_id}.json"
        if not target.exists():
            return None
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            return self._reconstruct_report(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def list_reports(self) -> list[ReportSummaryEntry]:
        entries: list[ReportSummaryEntry] = []
        for path in sorted(self._reports_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                summary = data.get("summary", {})
                entries.append(
                    ReportSummaryEntry(
                        report_id=data["report_id"],
                        request_id=data["request_id"],
                        created_at=data["created_at"],
                        passed=summary.get("passed", False),
                        issue_count=summary.get("issue_count", 0),
                        project_name=data.get("project_name"),
                        discipline=data.get("discipline"),
                    )
                )
            except (json.JSONDecodeError, KeyError):
                continue
        return entries

    def _reconstruct_report(self, data: dict) -> ValidationReport:
        return ValidationReport(
            report_id=data["report_id"],
            request_id=data["request_id"],
            ifc_path=Path(data["ifc_path"]),
            created_at=data["created_at"],
            requirements=tuple(
                self._reconstruct_requirement(r) for r in data.get("requirements", [])
            ),
            issues=tuple(self._reconstruct_issue(i) for i in data.get("issues", [])),
            summary=self._reconstruct_summary(data.get("summary", {})),
            drawing_annotations=tuple(
                self._reconstruct_annotation(a) for a in data.get("drawing_annotations", [])
            ),
            drawing_assets=tuple(
                self._reconstruct_drawing_asset(a) for a in data.get("drawing_assets", [])
            ),
            clash_results=tuple(
                self._reconstruct_clash_result(c) for c in data.get("clash_results", [])
            ),
            project_name=data.get("project_name"),
            discipline=data.get("discipline"),
        )

    def _reconstruct_requirement(self, data: dict) -> ParsedRequirement:
        return ParsedRequirement(
            rule_id=data["rule_id"],
            ifc_entity=data.get("ifc_entity"),
            rule_scope=RuleScope(data["rule_scope"])
            if data.get("rule_scope")
            else RuleScope.IFC_PROPERTY,
            target_ref=data.get("target_ref"),
            property_set=data.get("property_set"),
            property_name=data.get("property_name"),
            operator=ComparisonOperator(data["operator"])
            if data.get("operator")
            else ComparisonOperator.EQUALS,
            expected_value=data.get("expected_value"),
            unit=data.get("unit"),
            source=data.get("source", ""),
            source_kind=SourceKind(data["source_kind"])
            if data.get("source_kind")
            else SourceKind.STRUCTURED_TEXT,
            evidence_text=data.get("evidence_text"),
            instructions=data.get("instructions"),
            evidence_modality=data.get("evidence_modality"),
        )

    def _reconstruct_issue(self, data: dict) -> ValidationIssue:
        problem_zone_data = data.get("problem_zone")
        remark_data = data.get("remark")
        return ValidationIssue(
            rule_id=data["rule_id"],
            severity=Severity(data["severity"]),
            message=data["message"],
            ifc_entity=data.get("ifc_entity"),
            category=FindingCategory(data["category"])
            if data.get("category")
            else FindingCategory.IFC_VALIDATION,
            target_ref=data.get("target_ref"),
            property_set=data.get("property_set"),
            property_name=data.get("property_name"),
            operator=ComparisonOperator(data["operator"]) if data.get("operator") else None,
            expected_value=data.get("expected_value"),
            observed_value=data.get("observed_value"),
            unit=data.get("unit"),
            element_guid=data.get("element_guid"),
            problem_zone=ProblemZone(**problem_zone_data) if problem_zone_data else None,
            remark=GeneratedRemark(**remark_data) if remark_data else None,
        )

    def _reconstruct_summary(self, data: dict) -> ValidationSummary:
        return ValidationSummary(
            requirement_count=data.get("requirement_count", 0),
            issue_count=data.get("issue_count", 0),
            error_count=data.get("error_count", 0),
            warning_count=data.get("warning_count", 0),
            passed=data.get("passed", False),
            drawing_annotation_count=data.get("drawing_annotation_count", 0),
            generated_remark_count=data.get("generated_remark_count", 0),
        )

    def _reconstruct_annotation(self, data: dict) -> DrawingAnnotation:
        problem_zone_data = data.get("problem_zone")
        return DrawingAnnotation(
            annotation_id=data["annotation_id"],
            sheet_id=data["sheet_id"],
            target_ref=data["target_ref"],
            measure_name=data["measure_name"],
            observed_value=data["observed_value"],
            unit=data.get("unit"),
            problem_zone=ProblemZone(**problem_zone_data) if problem_zone_data else None,
            source=data.get("source", "drawing-text"),
        )

    def _reconstruct_drawing_asset(self, data: dict) -> DrawingAsset:
        return DrawingAsset(
            asset_id=data["asset_id"],
            sheet_id=data["sheet_id"],
            page_number=data.get("page_number"),
            media_type=data.get("media_type", "image/png"),
            coordinate_width=data.get("coordinate_width"),
            coordinate_height=data.get("coordinate_height"),
            stored_filename=data.get("stored_filename"),
            source_path=Path(data["source_path"]) if data.get("source_path") else None,
        )

    def _reconstruct_clash_result(self, data: dict) -> ClashResult:
        return ClashResult(
            element_a_guid=data["element_a_guid"],
            element_b_guid=data["element_b_guid"],
            clash_type=data["clash_type"],
            distance=data["distance"],
            description=data["description"],
        )
