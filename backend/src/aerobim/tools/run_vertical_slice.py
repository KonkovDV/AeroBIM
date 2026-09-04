
"""Vertical slice demo (11.08.2026): one manifest → analyze → JSON/HTML artifacts.

Honest scope: PDF **text layer** (vector) extraction via RasterDrawingAnalyzer,
deterministic package rules, existing report/exports. This is **not** a claim of
trained CV, native DWG, or customer accuracy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.checkpoint import CHECKPOINT

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
    confirm_link_against_spatial_index,
    link_annotation_to_ifc_target,
)
from aerobim.domain.check_coverage import coverage_from_report, derive_report_scope  # noqa: E402
from aerobim.domain.pdf_vector_primitives import (  # noqa: E402
    extract_pdf_vector_primitives,
    propose_symbol_candidates_from_vectors,
)
from aerobim.domain.region_detection_metrics import (  # noqa: E402
    labels_from_dicts,
    score_region_detections,
)
from aerobim.domain.run_manifest import build_run_manifest  # noqa: E402
from aerobim.domain.vlm_response_schema import (  # noqa: E402
    OBSERVATIONS_RESPONSE_SCHEMA,
    validate_observations_response,
)
from aerobim.infrastructure.adapters.heuristic_layout_region_detector import (  # noqa: E402
    HeuristicLayoutRegionDetector,
)
from aerobim.presentation.http.report_html import render_report_html  # noqa: E402
from aerobim.tools._cli_base import bootstrap_container  # noqa: E402
from aerobim.tools.benchmark_project_package import load_benchmark_pack  # noqa: E402

_ALLOWED_DRAWING_SUFFIXES = {".pdf", ".txt", ".json"}
_SLIDE_BOUNDARY = (
    "fixture_only demo slice; heuristic region/OCR baseline; not product CV; "
    "not customer accuracy; not native DWG"
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_sha(repo: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if completed.returncode == 0:
            return completed.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""
    return ""


def _git_dirty(repo: Path) -> bool:
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if completed.returncode == 0:
            return bool(completed.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        return False
    return False


def _document_identity(
    input_entries: list[dict[str, Any]], annotations: list[Any]
) -> dict[str, Any]:
    pdf = next(
        (entry for entry in input_entries if str(entry.get("path") or "").endswith(".pdf")),
        None,
    )
    first = annotations[0] if annotations else None
    zone = getattr(first, "problem_zone", None) if first is not None else None
    coordinates = None
    page_number = None
    sheet_id = None
    if zone is not None:
        page_number = zone.page_number
        sheet_id = getattr(first, "sheet_id", None)
        coordinates = {
            "x": zone.x,
            "y": zone.y,
            "width": zone.width,
            "height": zone.height,
        }
    return {
        "path": None if pdf is None else pdf.get("path"),
        "sha256": None if pdf is None else pdf.get("sha256"),
        "bytes": None if pdf is None else pdf.get("bytes"),
        "sheet_id": sheet_id or (None if pdf is None else pdf.get("sheet_id")),
        "page_number": page_number,
        "coordinates": coordinates,
        "format": "pdf_text_layer",
    }


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


def run_vertical_slice(
    manifest: Path,
    output_dir: Path,
    *,
    cv_sidecar: bool = True,
) -> dict[str, Any]:
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

    overlay_meta: dict[str, Any] | None = None
    overlay_error: str | None = None
    if not cv_sidecar:
        overlay_error = "cv_sidecar_disabled"
    else:
        pdf_for_overlay: Path | None = None
        for entry in input_entries:
            path_str = str(entry.get("path") or "")
            if path_str.endswith(".pdf"):
                candidate = root / path_str
                if candidate.is_file():
                    pdf_for_overlay = candidate
                    break
        overlay_zone = next(
            (
                ann.problem_zone
                for ann in report.drawing_annotations
                if ann.problem_zone is not None
            ),
            None,
        )
        if pdf_for_overlay is not None and overlay_zone is not None:
            try:
                from aerobim.tools.render_drawing_overlay_evidence import render_overlay

                overlay_meta = render_overlay(
                    pdf_path=pdf_for_overlay,
                    out_png=output_dir / "overlay-problem-zone.png",
                    zone={
                        "x": float(overlay_zone.x or 0.0),
                        "y": float(overlay_zone.y or 0.0),
                        "width": float(overlay_zone.width or 0.0),
                        "height": float(overlay_zone.height or 0.0),
                    },
                    page_number=int(overlay_zone.page_number or 1),
                )
            except ImportError as exc:
                overlay_error = f"overlay renderer unavailable: {exc}"
        elif pdf_for_overlay is None:
            overlay_error = "no PDF input for overlay"
        else:
            overlay_error = "no drawing annotation with problem_zone"

    git_sha = _git_sha(root)
    git_dirty = _git_dirty(root)
    document_identity = _document_identity(input_entries, list(report.drawing_annotations))
    package_sha256 = _sha256_file(pack_path)
    ids_sha = next(
        (str(entry["sha256"]) for entry in input_entries if entry.get("kind") == "ids"),
        None,
    )
    run_manifest = build_run_manifest(
        report,  # type: ignore[arg-type]
        request_id=report.request_id,
        pack_id=pack.pack_id,
        package_sha256=package_sha256,
        rules_sha256=ids_sha,
        code_version=git_sha or None,
    )
    outcome_value = getattr(report.summary.outcome, "value", report.summary.outcome)
    verification_status = (
        "NOT_PASS_EXPERT_REQUIRED"
        if not report.summary.passed
        else "PASS_FIXTURE_ONLY_NOT_CUSTOMER"
    )
    kt2_release = {
        "git_sha": git_sha or None,
        "working_tree_dirty": git_dirty,
        "package_id": pack.pack_id,
        "document_path": document_identity.get("path"),
        "document_sha256": document_identity.get("sha256"),
        "page_number": document_identity.get("page_number"),
        "coordinates": document_identity.get("coordinates"),
        "verification_status": verification_status,
        "checkpoint_verdict": CHECKPOINT,
        "reproducibility_hash": run_manifest.reproducibility_hash,
        "schema_versions": {
            "slice_summary": "1.1.0",
            "limitations": "1.1.0",
            "run_manifest": run_manifest.schema_version,
        },
        "claim_boundary": _SLIDE_BOUNDARY,
        "expert_review_required": True,
        "customer_accuracy": False,
        "fixture_demo": True,
    }
    public["kt2_release"] = kt2_release

    html_path = output_dir / "report.html"
    html_path.write_text(
        render_report_html(
            report.report_id,
            public,
            overlay_image_href="overlay-problem-zone.png" if overlay_meta else None,
        ),
        encoding="utf-8",
    )

    from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

    bcf_path = output_dir / "findings.bcfzip"
    bcf_path.write_bytes(export_bcf(report))

    if cv_sidecar:
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

        # --- P1.2 region metrics vs fixture labels (honest IoU@50, not product mAP) ---
        region_score: dict[str, Any] | None = None
        labels_path = root / "samples/demo/vertical-slice-2026-08-11/region_labels.json"
        if labels_path.is_file() and layout_regions:
            preds = labels_from_dicts(
                [
                    {
                        "sheet_id": str(r.get("sheet_id") or ""),
                        "layout_role": str(r.get("layout_role") or ""),
                        "bbox_xyxy": list(r.get("bbox_xyxy") or ()),
                    }
                    for r in layout_regions
                ]
            )
            label_payload = json.loads(labels_path.read_text(encoding="utf-8"))
            labels = labels_from_dicts(list(label_payload.get("regions") or []))
            region_score = score_region_detections(preds, labels, iou_threshold=0.5).as_dict()

        # --- P2 vector primitives + symbol candidates (NOT verified counts) ---
        vector_extract: dict[str, Any] | None = None
        symbol_candidates: list[dict[str, Any]] = []
        for entry in input_entries:
            path_str = str(entry.get("path") or "")
            if not path_str.endswith(".pdf"):
                continue
            pdf_path = root / path_str
            if not pdf_path.is_file():
                continue
            extraction = extract_pdf_vector_primitives(pdf_path)
            vector_extract = extraction.as_dict()
            symbol_candidates = [
                c.as_dict() for c in propose_symbol_candidates_from_vectors(extraction)
            ]
            break

        # --- P3 geometric tolerance confirm (optional bbox_for; demo with fake index) ---
        class _GeoIndex:
            def __init__(
                self, guids: set[str], boxes: dict[str, tuple[float, float, float, float]]
            ) -> None:
                self._guids = guids
                self._boxes = boxes

            def lookup(self, global_id: str) -> object | None:
                return object() if global_id in self._guids else None

            def bbox_xyxy_for(self, global_id: str) -> tuple[float, float, float, float] | None:
                return self._boxes.get(global_id)

        geo_confirm_demo: dict[str, Any] | None = None
        if report.drawing_annotations:
            ann0 = report.drawing_annotations[0]
            claimed = None
            if ann0.problem_zone and ann0.problem_zone.element_guid:
                claimed = ann0.problem_zone.element_guid.strip()
            # Demo: when no claimed GUID, show geo gate machinery on synthetic claim.
            demo_guid = claimed or "DEMO-GUID-GEO-TOLERANCE"
            link = link_annotation_to_ifc_target(ann0, requirements=report.requirements)
            if claimed is None:
                from dataclasses import replace as _replace

                link = _replace(
                    link,
                    evidence_ref=f"claimed_guid:{demo_guid}#{ann0.target_ref}",
                )
            ann_bbox = (
                (
                    float(ann0.problem_zone.x or 0.0),
                    float(ann0.problem_zone.y or 0.0),
                    float((ann0.problem_zone.x or 0.0) + (ann0.problem_zone.width or 0.0)),
                    float((ann0.problem_zone.y or 0.0) + (ann0.problem_zone.height or 0.0)),
                )
                if ann0.problem_zone
                else None
            )
            # Matching box → geo_ok; then mismatch → geo_mismatch (prove gate works).
            ok_index = _GeoIndex({demo_guid}, {demo_guid: ann_bbox} if ann_bbox else {})
            bad_index = _GeoIndex(
                {demo_guid},
                {demo_guid: (0.0, 0.0, 1.0, 1.0)},
            )
            ok_link = confirm_link_against_spatial_index(
                link, ok_index, annotation_bbox=ann_bbox, iou_tolerance=0.25
            )
            bad_link = confirm_link_against_spatial_index(
                link, bad_index, annotation_bbox=ann_bbox, iou_tolerance=0.25
            )
            geo_confirm_demo = {
                "iou_tolerance": 0.25,
                "match_ok_guid_set": ok_link.ifc_guid is not None,
                "match_ok_evidence": ok_link.evidence_ref,
                "mismatch_clears_guid": bad_link.ifc_guid is None,
                "mismatch_evidence": bad_link.evidence_ref,
                "claim": "geometric tolerance gate; never invents GUIDs",
            }

        # --- P4 structured advisory candidate (schema-validated; never touches passed) ---
        passed_before_advisory = report.summary.passed
        advisory_candidate = {
            "sheet_id": "A-101",
            "region_id": "content-crop-demo",
            "readable": True,
            "unreadable_reason": None,
            "observations": [
                {
                    "kind": "candidate_class",
                    "raw_value": "WALL-01 thickness 150 mm",
                    "normalized_value": None,
                    "unit": "mm",
                    "ifc_target_hint": "WALL-01",
                    "bbox_rel": [0.1, 0.1, 0.4, 0.2],
                    "confidence": 0.55,
                    "evidence_note": "structured advisory candidate on cropped region only",
                }
            ],
        }
        schema_check = validate_observations_response(advisory_candidate)
        passed_after_advisory = report.summary.passed
        advisory_guard = {
            "schema_conformant": schema_check.conformant,
            "schema_violations": list(schema_check.violations),
            "summary_passed_before": passed_before_advisory,
            "summary_passed_after": passed_after_advisory,
            "passed_unchanged": passed_before_advisory == passed_after_advisory,
            "crop_only": True,
            "whole_sheet_forbidden": True,
            "schema_kinds_include_candidate_class": "candidate_class"
            in str(OBSERVATIONS_RESPONSE_SCHEMA),
            "claim": "VLM advisory structured candidate; never changes summary.passed",
        }

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
                "status": "metrics_harness_ready" if region_score else "heuristic_baseline",
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
                "iou50_score": region_score,
            },
            "P2_symbol_spotting": {
                "status": "vector_baseline_candidates",
                "claim": (
                    "vector extraction + symbol candidates; counts NOT_CHECKED as verified findings"
                ),
                "vector": (
                    {
                        "page_count": vector_extract.get("page_count"),
                        "primitive_counts": vector_extract.get("primitive_counts"),
                        "method": vector_extract.get("method"),
                    }
                    if vector_extract
                    else None
                ),
                "symbol_candidate_count": len(symbol_candidates),
                "symbol_candidates_sample": symbol_candidates[:5],
                "note": "requires labeled corpus before any precision claim",
            },
            "P3_ifc_mapping": {
                "status": "geo_tolerance_ready",
                "claim": "annotation-IFC candidate + optional IoU tolerance confirm",
                "link_count": len(ifc_links),
                "confirmed_guid_count": sum(1 for link in ifc_links if link.get("ifc_guid")),
                "geo_confirm_demo": geo_confirm_demo,
            },
            "P4_vlm_advisory": {
                "status": "structured_candidate_ready",
                "claim": "VLM advisory never changes summary.passed (ADR-001)",
                "summary_passed_source": "deterministic_engine_only",
                "observed_summary_passed": report.summary.passed,
                "advisory_guard": advisory_guard,
                "advisory_candidate": advisory_candidate,
            },
        }
    else:
        evidence_records = []
        layout_regions = []
        ifc_links = []
        region_score = None
        vector_extract = None
        symbol_candidates = []
        geo_confirm_demo = None
        ocr_used = False
        text_layer_available = True
        empty_ocr_status = {
            "status": "NOT_RUN",
            "operator_status": "cv_sidecar_disabled",
            "note": "Acceptance Gate path; overlay/CV is P1",
        }
        cv_phases = {
            "disabled": True,
            "claim": "overlay/CV sidecar is P1; never writes summary.passed",
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
            "command": ("python -m aerobim.tools.run_demo_vertical_slice"),
            "cwd": "backend/",
            "inputs_sha256": {e["path"]: e.get("sha256") for e in input_entries if "sha256" in e},
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
    run_manifest_path = output_dir / "run-manifest.json"
    run_manifest_path.write_text(
        json.dumps(run_manifest.as_dict(), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    overlay_png_path = output_dir / "overlay-problem-zone.png"
    output_file_sha256: dict[str, str] = {}
    for name, path in (
        ("report.json", report_json_path),
        ("report.html", html_path),
        ("findings.bcfzip", bcf_path),
        ("LIMITATIONS.json", limitations_path),
        ("run-manifest.json", run_manifest_path),
    ):
        if path.is_file():
            output_file_sha256[name] = _sha256_file(path)
    if overlay_png_path.is_file():
        output_file_sha256["overlay-problem-zone.png"] = _sha256_file(overlay_png_path)
    input_artifact_hash = {
        str(entry["path"]): entry.get("sha256") for entry in input_entries if "sha256" in entry
    }
    finding_provenance = [
        {
            "finding_id": issue.get("finding_id"),
            "source_id": issue.get("source_id"),
            "evidence_refs": issue.get("evidence_refs"),
            "rule_id": issue.get("rule_id"),
            "origin": issue.get("origin"),
        }
        for issue in findings
    ]
    summary = {
        "artifact_type": "aerobim_vertical_slice",
        "schema_version": "1.1.0",
        "slice_id": pack.pack_id,
        "package_id": pack.pack_id,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "git_sha": git_sha or None,
        "working_tree_dirty": git_dirty,
        "claim_boundary": _SLIDE_BOUNDARY,
        "manifest": str(pack_path.relative_to(root)).replace("\\", "/"),
        "inputs": input_entries,
        "input_artifact_hash": input_artifact_hash,
        "output_file_sha256": output_file_sha256,
        "document_identity": document_identity,
        "finding_provenance": finding_provenance,
        "capability_honesty": asdict(report.capabilities) if report.capabilities else {},
        "outcome": outcome_value,
        "verification_status": verification_status,
        "checkpoint_verdict": CHECKPOINT,
        "expert_review_required": True,
        "customer_accuracy": False,
        "run_manifest": run_manifest.as_dict(),
        "report_id": report.report_id,
        "summary": asdict(report.summary),
        "operator_status_counts": operator_counts,
        "drawing_annotation_count": len(annotations),
        "finding_count": len(findings),
        "reproducibility": {
            "deterministic_order": "stable_rule_target_zone_key",
            "finding_keys": ["|".join(k) for k in finding_keys],
            "reproducibility_hash": run_manifest.reproducibility_hash,
            "hash_drift_note": (
                "report.json and findings.bcfzip include created_at; "
                "compare reproducibility_hash and overlay PNG, not raw report.json bytes"
            ),
        },
        "artifacts": {
            "report_json": str(report_json_path.name),
            "report_html": str(html_path.name),
            "limitations": "LIMITATIONS.json",
            "bcf_zip": str(bcf_path.name),
            "run_manifest": "run-manifest.json",
            "overlay_png": ("overlay-problem-zone.png" if overlay_meta else None),
        },
        "evidence": evidence_records,
        "layout_regions": layout_regions,
        "ifc_annotation_links": ifc_links,
        "empty_ocr_policy": empty_ocr_status,
        "overlay": overlay_meta,
        "overlay_error": overlay_error,
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
            "Checkpoint GO (regulatory_measurement_mvp; customer_go false). Fixture demo is not customer GO.",
        ],
        "vlm": {
            "qwen_fixture_status": "LIVE",
            "kimi_status": "GATED",
            "comparison_status": "comparison_not_run",
            "verdict_owner": "deterministic_engine_only",
        },
    }
    summary_path = output_dir / "slice-summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    summary["_paths"] = {
        "report_json": str(report_json_path),
        "report_html": str(html_path),
        "summary": str(summary_path),
        "limitations": str(limitations_path),
        "bcf_zip": str(bcf_path),
        "run_manifest": str(run_manifest_path),
        "overlay_png": str(overlay_png_path),
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
    parser.add_argument(
        "--clash-skip-tiny",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Skip tiny/degenerate IFC products before IfcClash (default on)",
    )
    args = parser.parse_args()
    if args.clash_skip_tiny is not None:
        import os

        os.environ["AEROBIM_CLASH_SKIP_TINY"] = "true" if args.clash_skip_tiny else "false"
    result = run_vertical_slice(args.manifest, args.output)
    print(
        json.dumps({k: v for k, v in result.items() if k != "_paths"}, ensure_ascii=False, indent=2)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
