"""Sprint 2 synthetic baseline: mutation-apply → detect → TP/FP/FN + Wilson + p95.

claim_level=synthetic_only. Never closes RT-001. No customer data.
"""

from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import RequirementSource, SourceKind, ValidationRequest
from aerobim.domain.study_design import wilson_interval
from aerobim.infrastructure.adapters.spreadsheet_load_evidence_adapter import (
    SpreadsheetLoadEvidenceAdapter,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container

ENTITY_PRESENCE_REQ = "SAM-001|IFCWALL|Pset_WallCommon|FireRating|eq|REI60"
_WALL_LINE = "#6=IFCWALL('38FRviGan7WhU9JrK165gm',$,'Fixture Wall',$,$,$,$,$,$);"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _mutate_ifc(base_text: str, mutation_id: str) -> str:
    if mutation_id == "LB-005":
        return "\n".join(
            line for line in base_text.splitlines() if not line.startswith("#8=")
        )
    if mutation_id == "LB-006":
        return base_text.replace("IFCLABEL('REI60')", "IFCLABEL('REI45')")
    if mutation_id == "LB-007":
        return base_text.replace("IFCWALL(", "IFCCOLUMN(")
    if mutation_id == "LB-011":
        # Second wall with same GlobalId (from adversarial Level-B test).
        dup = _WALL_LINE.replace("#6=", "#906=", 1)
        return base_text.rstrip() + "\n" + dup + "\n"
    raise ValueError(mutation_id)


def _bootstrap_validate(repo: Path, tmp: Path):
    settings = Settings(
        application_name="aerobim-sprint2-baseline",
        environment="test",
        host="127.0.0.1",
        port=8080,
        storage_dir=tmp / "var",
        debug=True,
    )
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    container = bootstrap_container(settings)
    return container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE)


def _run_calc_case(repo: Path, defect: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    defect_id = str(defect["defect_id"])
    level_b = {
        d["defect_id"]: d
        for d in (catalog.get("defects") or [])
        if isinstance(d, dict) and "defect_id" in d
    }
    src = level_b.get(defect_id) or {}
    text = str(src.get("calculation_text") or "")
    started = time.perf_counter()
    request = ValidationRequest(
        request_id=f"sprint2-{defect_id}",
        ifc_path=repo / "samples" / "ifc" / "walls-multi-entity.ifc",
        requirement_source=RequirementSource(
            text="", source_kind=SourceKind.STRUCTURED_TEXT, source_id="sprint2"
        ),
        calculation_source=RequirementSource(
            text=text, source_kind=SourceKind.CALCULATION, source_id=defect_id
        ),
    )
    issues = SpreadsheetLoadEvidenceAdapter().verify(request)
    elapsed = time.perf_counter() - started
    rule_ids = {i.rule_id for i in issues}
    expected = str(defect["match_key"])
    hit = expected in rule_ids
    extras = sorted(r for r in rule_ids if r != expected)
    return {
        "defect_id": defect_id,
        "tp": hit,
        "fn": not hit,
        "fp_rules": extras,
        "elapsed_s": round(elapsed, 6),
        "detected_rules": sorted(rule_ids),
    }


def _run_ifc_case(
    repo: Path, defect: dict[str, Any], use_case: Any, tmp: Path
) -> dict[str, Any]:
    defect_id = str(defect["defect_id"])
    mutation_id = str(defect.get("mutation_id") or "")
    ifc_base = (repo / "samples" / "ifc" / "wall-fire-rating-rei60.ifc").read_text(
        encoding="utf-8"
    )
    ids_path = repo / "samples" / "ids" / "wall-fire-rating.ids"
    ifc_path = tmp / f"{defect_id}.ifc"
    ifc_path.write_text(_mutate_ifc(ifc_base, mutation_id), encoding="utf-8")
    req = ""
    if defect.get("runner") == "ifc_ids_mutation_with_presence":
        req = ENTITY_PRESENCE_REQ
    started = time.perf_counter()
    report = use_case.execute(
        ValidationRequest(
            request_id=f"sprint2-{defect_id}",
            ifc_path=ifc_path,
            requirement_source=RequirementSource(text=req),
            ids_path=ids_path,
        )
    )
    elapsed = time.perf_counter() - started
    expected = str(defect["match_key"])
    if expected == "ENTITY-PRESENCE-IFCWALL":
        hit = any(
            "No elements found for entity IFCWALL" in (i.message or "")
            for i in report.issues
        )
        detected = [
            i.rule_id
            for i in report.issues
            if "No elements found for entity IFCWALL" in (i.message or "")
        ] or [i.rule_id for i in report.issues]
    else:
        hit = any(i.rule_id == expected for i in report.issues)
        detected = [i.rule_id for i in report.issues]
    extras = sorted({r for r in detected if r != expected and r})
    return {
        "defect_id": defect_id,
        "tp": hit,
        "fn": not hit,
        "fp_rules": extras,
        "elapsed_s": round(elapsed, 6),
        "detected_rules": sorted(set(detected)),
    }


def _p95(samples: list[float]) -> float | None:
    if not samples:
        return None
    if len(samples) == 1:
        return samples[0]
    ordered = sorted(samples)
    # Nearest-rank p95
    idx = max(0, min(len(ordered) - 1, int(0.95 * (len(ordered) - 1) + 0.5)))
    return ordered[idx]


def _write_simple_pdf(path: Path, lines: list[str]) -> None:
    """Minimal single-page PDF (Helvetica) — no external deps."""

    content_lines = ["BT /F1 10 Tf 50 780 Td 12 TL"]
    for i, line in enumerate(lines[:55]):
        safe = (
            line.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
            .encode("ascii", "replace")
            .decode("ascii")
        )
        if i == 0:
            content_lines.append(f"({safe}) Tj")
        else:
            content_lines.append(f"T* ({safe}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", "replace")
    objects: list[bytes] = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objects.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n"
    )
    objects.append(
        f"4 0 obj<< /Length {len(stream)} >>stream\n".encode("ascii")
        + stream
        + b"\nendstream\nendobj\n"
    )
    objects.append(b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n")
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(out))
        out.extend(obj)
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode(
            "ascii"
        )
    )
    path.write_bytes(bytes(out))


def run_baseline(*, iterations: int = 5) -> dict[str, Any]:
    repo = _repo_root()
    gt_path = repo / "samples" / "benchmarks" / "sprint2-synthetic-ground-truth.json"
    level_b_path = repo / "samples" / "benchmarks" / "injected-defects-level-b.json"
    gt = json.loads(gt_path.read_text(encoding="utf-8"))
    level_b = json.loads(level_b_path.read_text(encoding="utf-8"))
    planted = [d for d in (gt.get("planted_detectable") or []) if isinstance(d, dict)]
    # Skip optional duplicate_guid live probe if runner marks optional — still run LB-011.
    cases_out: list[dict[str, Any]] = []
    timings: list[float] = []
    tp = fp = fn = 0

    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        use_case = _bootstrap_validate(repo, tmp)
        for _ in range(max(1, iterations)):
            iter_start = time.perf_counter()
            for defect in planted:
                runner = defect.get("runner")
                if runner == "calculation_text":
                    result = _run_calc_case(repo, defect, level_b)
                elif runner in {
                    "ifc_ids_mutation",
                    "ifc_ids_mutation_with_presence",
                    "duplicate_guid",
                }:
                    if runner == "duplicate_guid":
                        defect = dict(defect)
                        defect["mutation_id"] = "LB-011"
                        defect["runner"] = "ifc_ids_mutation"
                    result = _run_ifc_case(repo, defect, use_case, tmp)
                else:
                    continue
                if _ == 0:
                    cases_out.append(result)
                    if result["tp"]:
                        tp += 1
                    if result["fn"]:
                        fn += 1
                    fp += len(result.get("fp_rules") or [])
                timings.append(result["elapsed_s"])
            # pack wall time for this iteration (sum of case times already in timings;
            # also record full-iter wall)
            _ = time.perf_counter() - iter_start

    trials_prec = tp + fp
    trials_rec = tp + fn
    wilson_p = (
        wilson_interval(tp, trials_prec).as_dict() if trials_prec else None
    )
    wilson_r = wilson_interval(tp, trials_rec).as_dict() if trials_rec else None
    case_times = [c["elapsed_s"] for c in cases_out]
    return {
        "artifact_type": "sprint2_synthetic_baseline",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_level": "synthetic_only",
        "closes_rt001": False,
        "customer_evidence": False,
        "checkpoint": "NO_GO",
        "method_doc": "docs/pilot/SPRINT2_DETECTION_METRICS_METHOD_2026_08.md",
        "ground_truth": str(gt_path.relative_to(repo)).replace("\\", "/"),
        "tz_class_coverage": gt.get("tz_error_classes"),
        "limitations": [
            "Synthetic planted defects only; unplanted TZ classes unmeasured",
            "Ground truth complete by construction for planted detectable set",
            "No real customer packages",
            "TZ 90% threshold NOT confirmed",
            "Does not close RT-001",
        ],
        "metrics": {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(tp / trials_prec, 6) if trials_prec else None,
            "recall": round(tp / trials_rec, 6) if trials_rec else None,
            "wilson_precision": wilson_p,
            "wilson_recall": wilson_r,
            "n_planted_detectable": len(cases_out),
            "n_below_planner_halfwidth_008": True,
            "time_per_case_mean_s": round(statistics.mean(case_times), 6)
            if case_times
            else None,
            "time_per_case_p95_s": _p95(case_times),
            "llm_overlay": {
                "status": "not_run_in_synthetic_detection_baseline",
                "note": (
                    "Detection TP/FP/FN are deterministic engine paths. "
                    "LLM overlay is verdict-neutral; cost bake-off is Block 5."
                ),
            },
        },
        "cases": cases_out,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--output-pdf", type=Path, default=None)
    args = parser.parse_args(argv)
    report = run_baseline(iterations=args.iterations)
    repo = _repo_root()
    day = datetime.now(tz=UTC).date().isoformat()
    out_json = args.output_json or (
        repo / "docs" / "evidence" / f"sprint2-synthetic-baseline-{day}.json"
    )
    out_md = args.output_md or (
        repo / "docs" / "evidence" / f"sprint2-synthetic-baseline-{day}.md"
    )
    out_pdf = args.output_pdf or (
        repo / "docs" / "evidence" / f"sprint2-synthetic-baseline-{day}.pdf"
    )
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    m = report["metrics"]
    md = [
        "# Sprint 2 synthetic baseline",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- claim_level: `{report['claim_level']}`",
        f"- closes_rt001: `{report['closes_rt001']}`",
        f"- checkpoint: `{report['checkpoint']}`",
        "",
        "## Metrics",
        "",
        f"- TP/FP/FN: **{m['tp']}/{m['fp']}/{m['fn']}**",
        f"- precision: **{m['precision']}** (Wilson lower: {(m.get('wilson_precision') or {}).get('lower')})",
        f"- recall: **{m['recall']}** (Wilson lower: {(m.get('wilson_recall') or {}).get('lower')})",
        f"- time_per_case_p95_s: **{m['time_per_case_p95_s']}**",
        f"- n_planted: {m['n_planted_detectable']} (below planner half-width 0.08 target)",
        "",
        "## Limitations",
        "",
    ]
    md.extend(f"- {item}" for item in report["limitations"])
    md.extend(["", f"JSON twin: `{out_json.as_posix()}`", ""])
    out_md.write_text("\n".join(md), encoding="utf-8")
    _write_simple_pdf(
        out_pdf,
        [
            "AeroBIM Sprint 2 synthetic baseline",
            f"generated {report['generated_at']}",
            f"claim_level={report['claim_level']} closes_rt001={report['closes_rt001']}",
            f"TP/FP/FN={m['tp']}/{m['fp']}/{m['fn']}",
            f"precision={m['precision']} recall={m['recall']}",
            f"Wilson prec lower={(m.get('wilson_precision') or {}).get('lower')}",
            f"Wilson rec lower={(m.get('wilson_recall') or {}).get('lower')}",
            f"p95_case_s={m['time_per_case_p95_s']}",
            "LIMITATIONS: synthetic only; no customer packs; 90% NOT confirmed; NO_GO",
        ],
    )
    print(json.dumps({"json": str(out_json), "md": str(out_md), "pdf": str(out_pdf), "metrics": m}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
