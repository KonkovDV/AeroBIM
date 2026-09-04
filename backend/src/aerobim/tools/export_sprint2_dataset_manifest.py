
"""Regenerate the deterministic Sprint 2 dataset track (Mode B cases + Mode A inventory).

claim_level=synthetic_only. Never invents customer orgs/results. Does not download
external corpora — Mode A inventory references docs/dataset open-source search only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from aerobim.domain.checkpoint import CHECKPOINT

SCHEMA_VERSION = "1.0.0"
CLAIM_LEVEL = "synthetic_only"
GENERATOR = "export_sprint2_dataset_manifest"
SEED = 20260806
# Fixed stamp for byte-identical regen (content identity via reproducibility_hash).
GENERATED_AT = "2026-08-06T00:00:00+00:00"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _case(
    *,
    case_id: str,
    case_class: str,
    source_package: str,
    expected_findings: list[str],
    severity: str,
    rule_id: str,
    evidence_refs: list[str],
    ground_truth_source: str,
    seed: int = SEED,
    notes: str | None = None,
) -> dict[str, Any]:
    body = {
        "case_id": case_id,
        "case_class": case_class,
        "source_package": source_package,
        "expected_findings": expected_findings,
        "severity": severity,
        "rule_id": rule_id,
        "evidence_refs": evidence_refs,
        "ground_truth_source": ground_truth_source,
        "generator": GENERATOR,
        "seed": seed,
        "schema_version": SCHEMA_VERSION,
        "status": "synthetic",
        "claim_level": CLAIM_LEVEL,
        "customer_precision_claim_publishable": False,
    }
    if notes:
        body["notes"] = notes
    body["sha256"] = _sha256_text(_canonical_json(body))
    return body


def _mode_b_ifc_ids(_repo: Path, gt: dict[str, Any]) -> list[dict[str, Any]]:
    planted = [
        d
        for d in (gt.get("planted_detectable") or [])
        if isinstance(d, dict)
        and (str(d.get("runner") or "").startswith("ifc") or d.get("runner") == "duplicate_guid")
    ]
    ifc_rel = "samples/ifc/wall-fire-rating-rei60.ifc"
    ids_rel = "samples/ids/wall-fire-rating.ids"
    gt_rel = "samples/benchmarks/sprint2-synthetic-ground-truth.json"
    cases: list[dict[str, Any]] = []
    for defect in planted:
        defect_id = str(defect["defect_id"])
        cases.append(
            _case(
                case_id=f"s2-ifc-{defect_id}",
                case_class="ifc_ids_property",
                source_package=ifc_rel,
                expected_findings=[str(defect["match_key"])],
                severity=str(defect.get("expected_severity") or "error"),
                rule_id=str(defect["match_key"]),
                evidence_refs=[
                    ifc_rel,
                    ids_rel,
                    f"gt:{defect_id}",
                    f"mutation:{defect.get('mutation_id') or 'LB-011'}",
                ],
                ground_truth_source=gt_rel,
                notes=f"runner={defect.get('runner')}",
            )
        )
    return cases


def _mode_b_cross_doc(_repo: Path, gt: dict[str, Any]) -> list[dict[str, Any]]:
    planted = [
        d
        for d in (gt.get("planted_detectable") or [])
        if isinstance(d, dict) and d.get("runner") == "calculation_text"
    ]
    level_b = "samples/benchmarks/injected-defects-level-b.json"
    gt_rel = "samples/benchmarks/sprint2-synthetic-ground-truth.json"
    cases: list[dict[str, Any]] = []
    for defect in planted:
        defect_id = str(defect["defect_id"])
        cases.append(
            _case(
                case_id=f"s2-xdoc-{defect_id}",
                case_class="cross_document_calc",
                source_package=level_b,
                expected_findings=[str(defect["match_key"])],
                severity=str(defect.get("expected_severity") or "warning"),
                rule_id=str(defect["match_key"]),
                evidence_refs=[
                    level_b,
                    f"gt:{defect_id}",
                    str(defect.get("locus") or "calculation"),
                ],
                ground_truth_source=gt_rel,
                notes="load/calc mismatch from Level-B / Sprint 2 planted set",
            )
        )
    return cases


def _mode_b_drawing_ocr(repo: Path) -> list[dict[str, Any]]:
    drawing_cases_path = (
        repo / "samples" / "benchmarks" / "drawing-advisory" / "cases-synthetic.json"
    )
    drawing_rel = "samples/benchmarks/drawing-advisory/cases-synthetic.json"
    cases: list[dict[str, Any]] = []
    if drawing_cases_path.is_file():
        payload = json.loads(drawing_cases_path.read_text(encoding="utf-8"))
        for row in payload.get("cases") or []:
            if not isinstance(row, dict):
                continue
            cid = str(row.get("case_id") or "")
            if not cid:
                continue
            raw_expected = row.get("expected")
            expected: dict[str, Any] = raw_expected if isinstance(raw_expected, dict) else {}
            cases.append(
                _case(
                    case_id=f"s2-draw-{cid}",
                    case_class="drawing_pdf_ocr_degraded",
                    source_package=drawing_rel,
                    expected_findings=[
                        f"schema_conformant={expected.get('schema_conformant')}",
                        f"hitl_count={expected.get('hitl_count')}",
                    ],
                    severity="info",
                    rule_id="DRAWING-ADVISORY-GROUNDING",
                    evidence_refs=[drawing_rel, f"drawing-advisory:{cid}"],
                    ground_truth_source=drawing_rel,
                    notes="Synthetic VLM/drawing-advisory fixture; not product OCR accuracy",
                )
            )
    # Reference generate_degraded_scans without requiring generated PNGs in-tree.
    cases.append(
        _case(
            case_id="s2-degraded-scan-protocol",
            case_class="drawing_pdf_ocr_degraded",
            source_package="backend/src/aerobim/tools/generate_degraded_scans.py",
            expected_findings=["degraded_variant_manifest"],
            severity="info",
            rule_id="DEGRADED-SCAN-PROVENANCE",
            evidence_refs=[
                "backend/src/aerobim/tools/generate_degraded_scans.py",
                "docs/pilot/VLM_OCR_COMPARISON_PROTOCOL_2026_08.md",
            ],
            ground_truth_source="generate_degraded_scans (seed=20260726 default)",
            seed=20260726,
            notes=(
                "Protocol reference case: regenerate PNG variants via generate_degraded_scans; "
                "not a customer scan"
            ),
        )
    )
    return cases


def build_mode_a_inventory(repo: Path) -> dict[str, Any]:
    """Reference open sources from the search results doc — no downloads."""

    search_doc = "docs/dataset/OPEN_SOURCE_SEARCH_RESULTS_2026_08_04.md"
    search_path = repo / Path(search_doc)
    return {
        "artifact_type": "sprint2_mode_a_inventory",
        "schema_version": SCHEMA_VERSION,
        "claim_level": CLAIM_LEVEL,
        "customer_precision_claim_publishable": False,
        "download_performed": False,
        "note": (
            "Inventory-only references from open-source search. Licenses must be "
            "verified at primary URLs before vendoring. No customer packs."
        ),
        "source_doc": search_doc,
        "source_doc_present": search_path.is_file(),
        "sources": [
            {
                "id": "ifc-bench-v2",
                "status": "VERIFIED_INVENTORY",
                "url": "https://huggingface.co/datasets/sylvainHellin/ifc-bench",
                "license_note": "QA CC BY 4.0; per-model licenses vary (GPLv3 isolation)",
                "vendored": False,
            },
            {
                "id": "kaan",
                "status": "PARTIAL_DO_NOT_VENDOR",
                "url": None,
                "license_note": "Primary open license not found",
                "vendored": False,
            },
            {
                "id": "osarch-examples",
                "status": "PARTIAL",
                "url": "https://wiki.osarch.org/index.php/AEC_Open_Data_directory",
                "license_note": "Check per-file before use",
                "vendored": False,
            },
            {
                "id": "batchplan",
                "status": "PARTIAL",
                "url": "https://github.com/byildiz/BatchPlan",
                "license_note": "MIT tool; pythonocc blocker for local use",
                "vendored": False,
            },
        ],
    }


def build_manifest(repo: Path | None = None) -> dict[str, Any]:
    root = repo or _repo_root()
    gt_path = root / "samples" / "benchmarks" / "sprint2-synthetic-ground-truth.json"
    if not gt_path.is_file():
        raise FileNotFoundError(f"missing ground truth: {gt_path}")
    gt = json.loads(gt_path.read_text(encoding="utf-8"))

    cases = _mode_b_ifc_ids(root, gt) + _mode_b_cross_doc(root, gt) + _mode_b_drawing_ocr(root)
    # Stable order for byte determinism
    cases = sorted(cases, key=lambda c: str(c["case_id"]))
    # Detect identity leakage across classes (same case_id must not appear twice)
    ids = [str(c["case_id"]) for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case_id in Sprint 2 dataset (identity leakage)")

    case_payloads = [_canonical_json(c) for c in cases]
    reproducibility_hash = _sha256_text("\n".join(case_payloads) + "\n")

    classes = sorted({str(c["case_class"]) for c in cases})
    if len(classes) < 3:
        raise ValueError(f"expected >=3 case classes, got {classes}")

    evidence_hashes = {
        "samples/ifc/wall-fire-rating-rei60.ifc": _sha256_file(
            root / "samples" / "ifc" / "wall-fire-rating-rei60.ifc"
        ),
        "samples/ids/wall-fire-rating.ids": _sha256_file(
            root / "samples" / "ids" / "wall-fire-rating.ids"
        ),
        "samples/benchmarks/sprint2-synthetic-ground-truth.json": _sha256_file(gt_path),
        "samples/benchmarks/injected-defects-level-b.json": _sha256_file(
            root / "samples" / "benchmarks" / "injected-defects-level-b.json"
        ),
        "samples/benchmarks/drawing-advisory/cases-synthetic.json": _sha256_file(
            root / "samples" / "benchmarks" / "drawing-advisory" / "cases-synthetic.json"
        ),
    }

    return {
        "artifact_type": "sprint2_dataset_manifest",
        "schema_version": SCHEMA_VERSION,
        "generated_at": GENERATED_AT,
        "claim_level": CLAIM_LEVEL,
        "customer_precision_claim_publishable": False,
        "customer_evidence": False,
        "closes_rt001": False,
        "checkpoint": CHECKPOINT,
        "generator": GENERATOR,
        "seed": SEED,
        "mode_b_classes": classes,
        "case_count": len(cases),
        "reproducibility_hash": reproducibility_hash,
        "evidence_file_sha256": evidence_hashes,
        "forbidden_claims": [
            "product_accuracy",
            "gt_90_percent",
            "production_ready",
            "native_dwg",
            "delivered_mep_clash",
            "calc_independence",
            "cde_ready_bcf",
            "customer_sla_from_fixtures",
        ],
        "cases": cases,
    }


def write_artifacts(
    *,
    repo: Path | None = None,
    out_dir: Path | None = None,
) -> dict[str, Path]:
    root = repo or _repo_root()
    target = out_dir or (root / "samples" / "benchmarks" / "sprint2-dataset")
    target.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(root)
    # Freeze generated_at for byte-stable twin writes in the same invocation
    # by reusing the already-built payload.
    mode_a = build_mode_a_inventory(root)
    mode_a["linked_manifest_reproducibility_hash"] = manifest["reproducibility_hash"]

    manifest_path = target / "MANIFEST.json"
    mode_a_path = target / "MODE_A_INVENTORY.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    mode_a_path.write_text(
        json.dumps(mode_a, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {"manifest": manifest_path, "mode_a": mode_a_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Default: samples/benchmarks/sprint2-dataset",
    )
    args = parser.parse_args(argv)
    paths = write_artifacts(out_dir=args.out_dir)
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "ok": True,
                "manifest": str(paths["manifest"]),
                "mode_a": str(paths["mode_a"]),
                "case_count": manifest["case_count"],
                "reproducibility_hash": manifest["reproducibility_hash"],
                "claim_level": manifest["claim_level"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
