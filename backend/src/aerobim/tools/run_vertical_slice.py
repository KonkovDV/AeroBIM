"""Vertical slice demo (11.08.2026): one manifest → analyze → JSON/HTML artifacts.

Honest scope: PDF **text layer** (vector) extraction via RasterDrawingAnalyzer,
deterministic package rules, existing report/exports. This is **not** a claim of
trained CV, native DWG, or customer accuracy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[4]
_SRC = _REPO / "backend" / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from aerobim.application.use_cases.analyze_project_package import (  # noqa: E402
    AnalyzeProjectPackageUseCase,
)
from aerobim.core.config.settings import Settings  # noqa: E402
from aerobim.core.di.tokens import Tokens  # noqa: E402
from aerobim.domain.annotation_ifc_matching import (  # noqa: E402
    link_annotation_to_ifc_target,
)
from aerobim.domain.check_coverage import coverage_from_report, derive_report_scope  # noqa: E402
from aerobim.infrastructure.adapters.heuristic_layout_region_detector import (  # noqa: E402
    HeuristicLayoutRegionDetector,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container  # noqa: E402
from aerobim.presentation.http.report_html import render_report_html  # noqa: E402
from aerobim.tools.benchmark_project_package import load_benchmark_pack  # noqa: E402

_ALLOWED_DRAWING_SUFFIXES = {".pdf", ".txt", ".json"}
_SLIDE_BOUNDARY = (
    "fixture_only demo slice; heuristic region/OCR baseline; not product CV; "
    "not customer accuracy; not native DWG"
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finding_key(finding: dict[str, Any]) -> tuple[str, ...]:
    pz = finding.get("problem_zone") or {}
    return (
        str(finding.get("rule_id")),
        str(finding.get("target_ref")),
        str(pz.get("sheet_id")),
        str(pz.get("page_number")),
        str(finding.get("observed_value")),
        str(finding.get("expected_value")),
    )


def _load_pack_manifest(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Manifest not found: {resolved}")
    return resolved


def run_vertical_slice(manifest: Path, output_dir: Path) -> dict[str, Any]:
    pack_path = _load_pack_manifest(manifest)
    pack = load_benchmark_pack(pack_path)
    request = pack.request

    root = _REPO.resolve()
    input_entries: list[dict[str, Any]] = []

    def _add_input(kind: str, path: Path | None) -> None:
        if path is None:
            return
        p = Path(path).resolve()
        if not p.is_file():
            return
        input_entries.append(
            {
                "kind": kind,
                "path": str(p.relative_to(root)).replace("\\", "/"),
                "sha256": _sha256_file(p),
                "bytes": p.stat().st_size,
            }
        )

    _add_input("ifc", request.ifc_path)
    _add_input("ids", request.ids_path)
    if request.requirement_source is not None and request.requirement_source.path is not None:
        _add_input("requirements", request.requirement_source.path)
    if request.technical_spec_source is not None and request.technical_spec_source.path is not None:
        _add_input("technical_spec", request.technical_spec_source.path)
    if request.calculation_source is not None and request.calculation_source.path is not None:
        _add_input("calculation", request.calculation_source.path)

    for drawing in request.drawing_sources or []:
        drawing_path = drawing.path
        if drawing_path is None:
            input_entries.append(
                {
                    "path": "<inline>",
                    "status": "NOT_CHECKED",
                    "reason": "drawing source has no filesystem path",
                }
            )
            continue
        p = Path(drawing_path).resolve()
        if p.suffix.lower() not in _ALLOWED_DRAWING_SUFFIXES:
            input_entries.append(
                {
                    "path": str(drawing.path),
                    "status": "NOT_CHECKED",
                    "reason": f"unsupported format for this slice: {p.suffix}",
                }
            )
            continue
        input_entries.append(
            {
                "path": str(p.relative_to(root)).replace("\\", "/"),
                "sha256": _sha256_file(p),
                "bytes": p.stat().st_size,
                "sheet_id": drawing.sheet_id,
                "format": drawing.format,
            }
        )

    settings = Settings.from_env()
    container = bootstrap_container(settings)
    use_case: AnalyzeProjectPackageUseCase = container.resolve(
        Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE
    )
    report = use_case.execute(request)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_json_path = output_dir / "report.json"
    report_json_path.write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    scope = derive_report_scope(report)
    coverage = coverage_from_report(report, scope=scope).to_dict(report=report)
    public = asdict(report)
    public["coverage"] = coverage
    html_path = output_dir / "report.html"
    html_path.write_text(render_report_html(report.report_id, public), encoding="utf-8")

    # Evidence envelope: deterministic provenance per extracted drawing annotation.
    # P0: text-layer vs OCR flags — this demo PDF uses pdfminer text layer (not OCR).
    ocr_used = False
    text_layer_available = True
    for annotation in report.drawing_annotations:
        if annotation.source and "ocr" in annotation.source.lower():
            ocr_used = True
            text_layer_available = False
            break

    evidence_records: list[dict[str, Any]] = []
    for annotation in report.drawing_annotations:
        pz = annotation.problem_zone
        source_path = next(
            (
                str(e["path"])
                for e in input_entries
                if e.get("sheet_id") == annotation.sheet_id and "sha256" in e
            ),
            None,
        )
        input_sha = next(
            (
                e.get("sha256")
                for e in input_entries
                if e.get("sheet_id") == annotation.sheet_id and "sha256" in e
            ),
            None,
        )
        method = (
            "ocr"
            if annotation.source and "ocr" in annotation.source.lower()
            else "pdf_text_layer"
        )
        record = {
            "annotation_id": annotation.annotation_id,
            "method": method,
            "method_version": "raster-drawing-analyzer@1",
            "claim": (
                "OCR extraction, not engineering understanding"
                if method == "ocr"
                else "PDF text-layer extraction, not trained CV"
            ),
            "source_path": source_path,
            "source_sha256": input_sha,
            "page": pz.page_number if pz else None,
            "region_bbox": [pz.x, pz.y, pz.width, pz.height] if pz else None,
            "extracted_value": annotation.observed_value,
            "normalized_value": annotation.observed_value,
            "unit": annotation.unit,
            "target_ref": annotation.target_ref,
            "measure_name": annotation.measure_name,
            "sheet_id": annotation.sheet_id,
            "quality_flags": {
                "heuristic_baseline": True,
                "cv_verified": False,
                "ocr_used": method == "ocr",
                "text_layer_available": method == "pdf_text_layer",
                "low_confidence": False,
                "requires_expert": False,
            },
            "evidence_hash": hashlib.sha256(
                json.dumps(
                    {
                        "source_sha256": input_sha,
                        "annotation_id": annotation.annotation_id,
                        "value": annotation.observed_value,
                        "method": method,
                    },
                    sort_keys=True,
                ).encode("utf-8")
            ).hexdigest(),
        }
        evidence_records.append(record)

    # P1.1: heuristic layout regions (stamp/title/spec/dim) — HEURISTIC_BASELINE.
    detector = HeuristicLayoutRegionDetector()
    layout_regions: list[dict[str, Any]] = []
    for entry in input_entries:
        if entry.get("format") != "pdf" and not str(entry.get("path", "")).endswith(".pdf"):
            continue
        pdf_path = root / str(entry["path"])
        if not pdf_path.is_file():
            continue
        for region in detector.detect(pdf_path, sheet_id=str(entry.get("sheet_id") or "A-101")):
            layout_regions.append(asdict(region))

    # P3 scaffold: annotation → IFC candidate links (claimed GUID only; no invention).
    ifc_links = [
        link_annotation_to_ifc_target(ann, requirements=report.requirements).as_dict()
        for ann in report.drawing_annotations
    ]

    # P0 honesty: zero annotations on a raster/PDF request → not "no errors".
    raster_zero_yield = len(report.drawing_annotations) == 0 and any(
        str(e.get("path", "")).endswith((".pdf", ".png", ".jpg", ".jpeg", ".webp"))
        for e in input_entries
    )
    empty_ocr_status = (
        {
            "status": "INSUFFICIENT_DATA",
            "operator_status": "insufficient_data",
            "note": (
                "Zero drawing annotations from PDF/raster path — fail-closed "
                "(capabilities.raster FAILED); never treat as CHECKED_OK / no findings"
            ),
        }
        if raster_zero_yield
        else {
            "status": "CHECKED_WITH_EXTRACTION",
            "operator_status": "findings_or_annotations_present",
            "note": "At least one drawing annotation extracted",
        }
    )

    # CV phase status (roadmap P0–P4) — honest progress, not product claims.
    cv_phases = {
        "P0_ocr_raster": {
            "status": "baseline_ready",
            "claim": "OCR extraction, not engineering understanding",
            "ocr_used": ocr_used,
            "text_layer_available": text_layer_available,
            "empty_yield_policy": "INSUFFICIENT_DATA + raster FAILED (not silent pass)",
        },
        "P1_region_detector": {
            "status": "heuristic_baseline",
            "claim": "region detection: heuristic baseline, not trained CV",
            "roles": sorted(
                {
                    str(r.get("layout_role"))
                    for r in layout_regions
                    if isinstance(r.get("layout_role"), str)
                }
            ),
            "region_count": len(layout_regions),
            "hitl_required_count": sum(1 for r in layout_regions if r.get("hitl_required")),
        },
        "P2_symbol_spotting": {
            "status": "NOT_CHECKED",
            "claim": "symbol spotting deferred — research contour, not VLM-first",
            "note": "doors/windows count not claimed; requires CAD primitives + labeled corpus",
        },
        "P3_ifc_mapping": {
            "status": "candidate_links_only",
            "claim": "annotation-IFC candidate; ifc_guid unset until spatial confirm",
            "link_count": len(ifc_links),
            "confirmed_guid_count": sum(1 for link in ifc_links if link.get("ifc_guid")),
        },
        "P4_vlm_advisory": {
            "status": "guarded",
            "claim": "VLM advisory never changes summary.passed (ADR-001)",
            "summary_passed_source": "deterministic_engine_only",
            "observed_summary_passed": report.summary.passed,
        },
    }

    # Honest sidecar: explicit limitations and reproduction steps for the demo.
    limitations = {
        "artifact": "vertical-slice-limitations",
        "schema_version": "1.1.0",
        "claim_boundary": _SLIDE_BOUNDARY,
        "not_demonstrated": [
            "trained CV / symbol detection on drawing",
            "native DWG ingestion",
            "MEP system-aware clash",
            "customer corpus accuracy",
            "production-ready BCF/CDE integration",
            "whole-sheet VLM understanding",
        ],
        "cv_phases": cv_phases,
        "reproduce": {
            "command": (
                "python -m aerobim.tools.run_vertical_slice "
                "--manifest samples/demo/vertical-slice-2026-08-11/manifest.json "
                "--output artifacts/vertical-slice-2026-08-11"
            ),
            "cwd": "backend/",
            "inputs_sha256": {
                e["path"]: e.get("sha256") for e in input_entries if "sha256" in e
            },
        },
        "expert_decision_required": True,
    }
    limitations_path = output_dir / "LIMITATIONS.json"
    limitations_path.write_text(
        json.dumps(limitations, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    coverage_rows = coverage.get("sources") or []
    operator_counts: dict[str, int] = {}
    for row in coverage_rows if isinstance(coverage_rows, list) else []:
        if not isinstance(row, dict):
            continue
        fam_map = row.get("operator_status")
        if isinstance(fam_map, dict):
            for status in fam_map.values():
                if isinstance(status, str):
                    operator_counts[status] = operator_counts.get(status, 0) + 1

    annotations = [asdict(a) for a in report.drawing_annotations]
    findings = [asdict(i) for i in report.issues]
    finding_keys = [_finding_key(f) for f in findings]
    summary = {
        "artifact_type": "aerobim_vertical_slice",
        "schema_version": "1.0.0",
        "slice_id": pack.pack_id,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_boundary": _SLIDE_BOUNDARY,
        "manifest": str(pack_path.relative_to(root)).replace("\\", "/"),
        "inputs": input_entries,
        "report_id": report.report_id,
        "summary": asdict(report.summary),
        "operator_status_counts": operator_counts,
        "drawing_annotation_count": len(annotations),
        "finding_count": len(findings),
        "reproducibility": {
            "deterministic_order": "stable_rule_target_zone_key",
            "finding_keys": ["|".join(k) for k in finding_keys],
        },
        "artifacts": {
            "report_json": str(report_json_path.name),
            "report_html": str(html_path.name),
            "limitations": "LIMITATIONS.json",
        },
        "evidence": evidence_records,
        "layout_regions": layout_regions,
        "ifc_annotation_links": ifc_links,
        "empty_ocr_policy": empty_ocr_status,
        "cv_phases": cv_phases,
        "metrics": {
            "drawing_extraction_coverage": (
                len(annotations) / max(len(report.drawing_assets), 1)
                if report.drawing_assets
                else 0.0
            ),
            "annotation_count": len(annotations),
            "finding_count": len(findings),
            "requires_expert_count": operator_counts.get("expert_required", 0),
            "not_checked_count": operator_counts.get("not_checked", 0),
            "insufficient_data_count": operator_counts.get("insufficient_data", 0),
            "layout_region_count": len(layout_regions),
            "layout_hitl_count": sum(1 for r in layout_regions if r.get("hitl_required")),
            "ifc_candidate_link_count": len(ifc_links),
        },
        "honest_notes": [
            "PDF input uses text-layer extraction (vector), not trained CV",
            "OCR extraction, not engineering understanding, when raster path used",
            "region detection: heuristic baseline, not trained CV",
            "symbol spotting NOT_CHECKED (research contour)",
            "VLM advisory never changes summary.passed",
            "REQUIRES_EXPERT / INSUFFICIENT_DATA via coverage — never silent pass",
            "Original inputs are read-only in this slice",
        ],
    }
    summary_path = output_dir / "slice-summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary["_paths"] = {
        "report_json": str(report_json_path),
        "report_html": str(html_path),
        "summary": str(summary_path),
        "limitations": str(limitations_path),
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Benchmark-style pack manifest JSON for the slice",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Directory for report.json / report.html / slice-summary.json",
    )
    args = parser.parse_args()
    result = run_vertical_slice(args.manifest, args.output)
    print(json.dumps({k: v for k, v in result.items() if k != "_paths"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
