"""Sprint 2 synthetic baseline: mutation-apply → detect → TP/FP/FN + Wilson + p95.

claim_level=synthetic_only. Never closes RT-001. No customer data.
Extends the Sprint 2 demo SSOT runner — do not fork a competing fourth baseline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from collections import Counter
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
from aerobim.tools._cli_base import bootstrap_container

ENTITY_PRESENCE_REQ = "SAM-001|IFCWALL|Pset_WallCommon|FireRating|eq|REI60"
_WALL_LINE = "#6=IFCWALL('38FRviGan7WhU9JrK165gm',$,'Fixture Wall',$,$,$,$,$,$);"
CLAIM_LEVEL = "synthetic_only"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _git_sha(repo: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _mutate_ifc(base_text: str, mutation_id: str) -> str:
    if mutation_id == "LB-005":
        return "\n".join(line for line in base_text.splitlines() if not line.startswith("#8="))
    if mutation_id == "LB-006":
        return base_text.replace("IFCLABEL('REI60')", "IFCLABEL('REI45')")
    if mutation_id == "LB-007":
        return base_text.replace("IFCWALL(", "IFCCOLUMN(")
    if mutation_id == "LB-011":
        # Second wall with same GlobalId (from adversarial Level-B test).
        dup = _WALL_LINE.replace("#6=", "#906=", 1)
        return base_text.rstrip() + "\n" + dup + "\n"
    raise ValueError(mutation_id)


def _bootstrap_validate(repo: Path, tmp: Path) -> Any:
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
    severities = [i.severity.value for i in issues]
    return {
        "defect_id": defect_id,
        "tp": hit,
        "fn": not hit,
        "fp_rules": extras,
        "elapsed_s": round(elapsed, 6),
        "detected_rules": sorted(rule_ids),
        "severities": severities,
        "finding_kind": "remark",
    }


def _run_ifc_case(repo: Path, defect: dict[str, Any], use_case: Any, tmp: Path) -> dict[str, Any]:
    defect_id = str(defect["defect_id"])
    mutation_id = str(defect.get("mutation_id") or "")
    ifc_base = (repo / "samples" / "ifc" / "wall-fire-rating-rei60.ifc").read_text(encoding="utf-8")
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
            "No elements found for entity IFCWALL" in (i.message or "") for i in report.issues
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
    severities = [i.severity.value for i in report.issues]
    return {
        "defect_id": defect_id,
        "tp": hit,
        "fn": not hit,
        "fp_rules": extras,
        "elapsed_s": round(elapsed, 6),
        "detected_rules": sorted(set(detected)),
        "severities": severities,
        "finding_kind": "remark",
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
    """Minimal multi-block PDF (Helvetica) — no external deps required."""

    # Paginate ~50 lines per page for the 19-section brief.
    pages: list[list[str]] = []
    chunk: list[str] = []
    for line in lines:
        chunk.append(line)
        if len(chunk) >= 50:
            pages.append(chunk)
            chunk = []
    if chunk:
        pages.append(chunk)
    if not pages:
        pages = [["(empty)"]]

    objects: list[bytes] = []
    # We'll rebuild with correct page tree after streams are known.
    page_streams: list[bytes] = []
    for page_lines in pages:
        content_lines = ["BT /F1 9 Tf 40 780 Td 11 TL"]
        for i, line in enumerate(page_lines):
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
        page_streams.append("\n".join(content_lines).encode("latin-1", "replace"))

    # Object layout: 1=Catalog, 2=Pages, 3..=Page N, then contents, then font
    n_pages = len(page_streams)
    page_obj_nums = list(range(3, 3 + n_pages))
    content_obj_nums = list(range(3 + n_pages, 3 + 2 * n_pages))
    font_obj = 3 + 2 * n_pages

    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    kids = " ".join(f"{n} 0 R" for n in page_obj_nums)
    objects.append(
        f"2 0 obj<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>endobj\n".encode("ascii")
    )
    for page_num, content_num in zip(page_obj_nums, content_obj_nums, strict=True):
        objects.append(
            (
                f"{page_num} 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content_num} 0 R /Resources<< /Font<< /F1 {font_obj} 0 R >> >> >>"
                f"endobj\n"
            ).encode("ascii")
        )
    for content_num, stream in zip(content_obj_nums, page_streams, strict=True):
        objects.append(
            f"{content_num} 0 obj<< /Length {len(stream)} >>stream\n".encode("ascii")
            + stream
            + b"\nendstream\nendobj\n"
        )
    objects.append(
        f"{font_obj} 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n".encode(
            "ascii"
        )
    )
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


def _load_dataset_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"dataset manifest not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("dataset manifest must be a JSON object")
    if payload.get("artifact_type") != "sprint2_dataset_manifest":
        raise ValueError(
            f"unexpected artifact_type={payload.get('artifact_type')!r}; "
            "expected sprint2_dataset_manifest"
        )
    if not isinstance(payload.get("cases"), list) or not payload["cases"]:
        raise ValueError("dataset manifest missing non-empty cases[]")
    return payload


def _cheap_capabilities_snapshot() -> dict[str, Any]:
    return {
        "clash": {
            "status": "PARTIAL",
            "note": "fixture path exists; MEP system clash NOT_VERIFIED",
        },
        "ids": {"status": "VERIFIED_FIXTURE_ONLY"},
        "ifc_validation": {"status": "VERIFIED_FIXTURE_ONLY"},
        "llm_advisory": {
            "status": "ADVISORY_ONLY",
            "affects_summary_passed": False,
        },
        "mep_system_clash": {"status": "NOT_VERIFIED"},
        "native_dwg": {"status": "MISSING"},
        "bcf_cde": {"status": "PARTIAL", "note": "structural export only; not CDE-ready claim"},
        "customer_sla": {"status": "BLOCKED_BY_CUSTOMER_DATA"},
    }


def _rel_or_abs(repo: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def run_baseline(
    *,
    iterations: int = 5,
    dataset_manifest_path: Path | None = None,
) -> dict[str, Any]:
    repo = _repo_root()
    gt_path = repo / "samples" / "benchmarks" / "sprint2-synthetic-ground-truth.json"
    level_b_path = repo / "samples" / "benchmarks" / "injected-defects-level-b.json"
    gt = json.loads(gt_path.read_text(encoding="utf-8"))
    level_b = json.loads(level_b_path.read_text(encoding="utf-8"))
    planted = [d for d in (gt.get("planted_detectable") or []) if isinstance(d, dict)]
    cases_out: list[dict[str, Any]] = []
    timings: list[float] = []
    tp = fp = fn = 0
    severity_counter: Counter[str] = Counter()

    dataset_meta: dict[str, Any] | None = None
    if dataset_manifest_path is not None:
        dataset_meta = _load_dataset_manifest(dataset_manifest_path)

    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        use_case = _bootstrap_validate(repo, tmp)
        for iter_idx in range(max(1, iterations)):
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
                if iter_idx == 0:
                    cases_out.append(result)
                    if result["tp"]:
                        tp += 1
                    if result["fn"]:
                        fn += 1
                    fp += len(result.get("fp_rules") or [])
                    for sev in result.get("severities") or []:
                        severity_counter[str(sev)] += 1
                timings.append(result["elapsed_s"])
            _ = time.perf_counter() - iter_start

    trials_prec = tp + fp
    trials_rec = tp + fn
    wilson_p = wilson_interval(tp, trials_prec).as_dict() if trials_prec else None
    wilson_r = wilson_interval(tp, trials_rec).as_dict() if trials_rec else None
    case_times = [c["elapsed_s"] for c in cases_out]

    remarks_count = sum(1 for c in cases_out if c.get("finding_kind") == "remark" and c.get("tp"))
    clashes_count = 0  # honesty: no planted geometric clash pair in this sprint

    case_payloads = [_canonical_json(c) for c in sorted(cases_out, key=lambda x: x["defect_id"])]
    reproducibility_hash = _sha256_text("\n".join(case_payloads) + "\n")

    return {
        "artifact_type": "sprint2_synthetic_baseline",
        "schema_version": "1.1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "commit_sha": _git_sha(repo),
        "claim_level": CLAIM_LEVEL,
        "customer_precision_claim_publishable": False,
        "precision_claim_publishable": False,
        "customer_accuracy_not_established": True,
        "closes_rt001": False,
        "customer_evidence": False,
        "checkpoint": "NO_GO",
        "method_doc": "docs/pilot/SPRINT2_DETECTION_METRICS_METHOD_2026_08.md",
        "ground_truth": str(gt_path.relative_to(repo)).replace("\\", "/"),
        "dataset_manifest": _rel_or_abs(repo, dataset_manifest_path),
        "dataset_manifest_meta": (
            {
                "reproducibility_hash": dataset_meta.get("reproducibility_hash"),
                "case_count": dataset_meta.get("case_count"),
                "mode_b_classes": dataset_meta.get("mode_b_classes"),
                "claim_level": dataset_meta.get("claim_level"),
            }
            if dataset_meta
            else None
        ),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "implementation": platform.python_implementation(),
        },
        "tz_class_coverage": gt.get("tz_error_classes"),
        "limitations": [
            "Synthetic planted defects only; unplanted TZ classes unmeasured",
            "Ground truth complete by construction for planted detectable set",
            "No real customer packages",
            "TZ 90% threshold NOT confirmed",
            "Does not close RT-001",
            "Geometric clashes_count=0 by honesty (no planted clash IFC pair)",
            "Agreement kappa/alpha and nDCG: N/A (no dual-human / ranking labels in this run)",
        ],
        "reproducibility_hash": reproducibility_hash,
        "capabilities_snapshot": _cheap_capabilities_snapshot(),
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
            "time_per_case_mean_s": round(statistics.mean(case_times), 6) if case_times else None,
            "time_per_case_p95_s": _p95(case_times),
            "remarks_count": remarks_count,
            "clashes_count": clashes_count,
            "clashes_honesty_note": (
                "clashes_count is 0: geometric_clash_between_systems is not_planted_runnable "
                "in sprint2-synthetic-ground-truth; do not interpret as product clash quality"
            ),
            "severity_distribution": dict(sorted(severity_counter.items())),
            "agreement": {
                "status": "N/A",
                "reason": (
                    "No dual-human adjudicator CSV in this synthetic baseline; "
                    "measure_adjudicator_agreement requires customer/expert labels (RT-001)"
                ),
            },
            "ndcg": {
                "status": "N/A",
                "reason": "No ranking relevance labels supplied to this runner",
            },
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


def _banner_lines() -> list[str]:
    return [
        "> # SYNTHETIC/FIXTURE ONLY",
        "> # CUSTOMER ACCURACY NOT ESTABLISHED",
        "",
        "**Banner (mandatory):** `SYNTHETIC/FIXTURE ONLY` · `CUSTOMER ACCURACY NOT ESTABLISHED`",
        "",
    ]


def _render_markdown(report: dict[str, Any], *, json_path: Path) -> str:
    m = report["metrics"]
    lines = [
        "# Sprint 2 baseline report",
        "",
        *_banner_lines(),
        f"- generated_at: `{report['generated_at']}`",
        f"- commit_sha: `{report.get('commit_sha')}`",
        f"- claim_level: `{report['claim_level']}`",
        f"- customer_precision_claim_publishable: "
        f"`{report.get('customer_precision_claim_publishable')}`",
        f"- precision_claim_publishable: `{report.get('precision_claim_publishable')}`",
        f"- customer_accuracy_not_established: `{report.get('customer_accuracy_not_established')}`",
        f"- closes_rt001: `{report['closes_rt001']}`",
        f"- checkpoint: `{report['checkpoint']}`",
        f"- reproducibility_hash: `{report.get('reproducibility_hash')}`",
        "",
        "## 1. Goal",
        "",
        "Synthetic detection baseline on planted fixtures. Checkpoint **NO_GO**. "
        "Does not publish product accuracy.",
        "",
        "## 2. Commit SHA",
        "",
        f"`{report.get('commit_sha')}`",
        "",
        "## 3. Dataset",
        "",
        f"- ground_truth: `{report.get('ground_truth')}`",
        f"- dataset_manifest: `{report.get('dataset_manifest')}`",
        f"- dataset_meta: `{json.dumps(report.get('dataset_manifest_meta'), ensure_ascii=False)}`",
        "",
        "## 4. License / provenance",
        "",
        "Repo MIT fixtures + synthetic planted defects. No customer packs. "
        "Mode A open sources referenced inventory-only (not vendored here).",
        "",
        "## 5. Ground-truth method",
        "",
        f"See `{report.get('method_doc')}`. Match keys from planted_detectable.",
        "",
        "## 6. Environment",
        "",
        f"```json\n{json.dumps(report.get('environment'), indent=2)}\n```",
        "",
        "## 7. Reproduction commands",
        "",
        "```",
        "cd backend",
        ".venv\\Scripts\\python.exe -m aerobim.tools.export_sprint2_dataset_manifest",
        ".venv\\Scripts\\python.exe -m aerobim.tools.run_sprint2_synthetic_baseline "
        "--iterations 1 --dataset-manifest "
        "../samples/benchmarks/sprint2-dataset/MANIFEST.json",
        "```",
        "",
        "## 8. Speed table",
        "",
        "| metric | value |",
        "|---|---|",
        f"| time_per_case_mean_s | {m.get('time_per_case_mean_s')} |",
        f"| time_per_case_p95_s | {m.get('time_per_case_p95_s')} |",
        "",
        "## 9. Quality table",
        "",
        "| metric | value |",
        "|---|---|",
        f"| TP / FP / FN | {m['tp']} / {m['fp']} / {m['fn']} |",
        f"| precision | {m['precision']} |",
        f"| recall | {m['recall']} |",
        f"| Wilson prec lower | {(m.get('wilson_precision') or {}).get('lower')} |",
        f"| Wilson rec lower | {(m.get('wilson_recall') or {}).get('lower')} |",
        "",
        "## 10. Remarks",
        "",
        f"remarks_count = **{m.get('remarks_count')}** (deterministic engine findings).",
        "",
        "## 11. Clashes",
        "",
        f"clashes_count = **{m.get('clashes_count')}**. {m.get('clashes_honesty_note')}",
        "",
        "## 12. Severity distribution",
        "",
        f"```json\n{json.dumps(m.get('severity_distribution'), indent=2)}\n```",
        "",
        "## 13. Confusion / detection counts",
        "",
        f"TP={m['tp']} FP={m['fp']} FN={m['fn']} on planted detectable set "
        f"(n={m.get('n_planted_detectable')}).",
        "",
        "## 14. Agreement / nDCG",
        "",
        f"- agreement: {m.get('agreement')}",
        f"- ndcg: {m.get('ndcg')}",
        "",
        "## 15. Reproducibility hash",
        "",
        f"`{report.get('reproducibility_hash')}`",
        "",
        "## 16. Capabilities snapshot",
        "",
        f"```json\n{json.dumps(report.get('capabilities_snapshot'), indent=2)}\n```",
        "",
        "## 17. Claims boundary",
        "",
        "- claim_level=`synthetic_only`",
        "- customer_precision_claim_publishable=`false`",
        "- precision_claim_publishable=`false`",
        "- customer_accuracy_not_established=`true`",
        "- Forbidden: product accuracy, >90%, production-ready, native DWG, "
        "delivered MEP clash, calc independence, CDE-ready BCF, customer SLA from fixtures",
        "",
        "## 18. TZ map",
        "",
        "```json",
        json.dumps(report.get("tz_class_coverage"), indent=2, ensure_ascii=False),
        "```",
        "",
        "## 19. Limits / next steps",
        "",
    ]
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(
        [
            "",
            "- Next: customer dual adjudication (RT-001), planted clash IFC pair, "
            "licensed Mode A corpus under review.",
            "",
            f"JSON twin: `{json_path.as_posix()}`",
            "",
        ]
    )
    return "\n".join(lines)


def _render_html(report: dict[str, Any]) -> str:
    m = report["metrics"]
    return "\n".join(
        [
            "<!DOCTYPE html>",
            '<html lang="en"><head><meta charset="utf-8"/>',
            "<title>Sprint 2 baseline report</title>",
            "<style>body{font-family:Segoe UI,sans-serif;max-width:900px;margin:2rem auto;"
            "line-height:1.45} code{background:#f4f4f4;padding:0 .25rem}"
            ".banner{font-size:1.6rem;font-weight:700;color:#7a1f1f;margin:1rem 0}</style>",
            "</head><body>",
            "<h1>Sprint 2 baseline report</h1>",
            '<p class="banner">SYNTHETIC/FIXTURE ONLY</p>',
            '<p class="banner">CUSTOMER ACCURACY NOT ESTABLISHED</p>',
            f"<p><strong>claim_level</strong>: <code>{report['claim_level']}</code> · "
            f"checkpoint <code>{report['checkpoint']}</code> · "
            f"publishable <code>{report.get('customer_precision_claim_publishable')}</code> · "
            f"customer_accuracy_not_established "
            f"<code>{report.get('customer_accuracy_not_established')}</code></p>",
            f"<p>commit <code>{report.get('commit_sha')}</code></p>",
            f"<p>TP/FP/FN = {m['tp']}/{m['fp']}/{m['fn']} · "
            f"precision={m['precision']} · recall={m['recall']}</p>",
            f"<p>remarks_count={m.get('remarks_count')} · "
            f"clashes_count={m.get('clashes_count')}</p>",
            f"<p>reproducibility_hash=<code>{report.get('reproducibility_hash')}</code></p>",
            "<p>Agreement/nDCG: N/A (see JSON). "
            "Synthetic fixtures only — not customer evidence.</p>",
            "</body></html>",
            "",
        ]
    )


def _pdf_lines(report: dict[str, Any]) -> list[str]:
    m = report["metrics"]
    return [
        "*** SYNTHETIC/FIXTURE ONLY ***",
        "*** CUSTOMER ACCURACY NOT ESTABLISHED ***",
        "AeroBIM Sprint 2 baseline report",
        "1 Goal: synthetic detection baseline; checkpoint NO_GO",
        f"2 Commit: {report.get('commit_sha')}",
        f"3 Dataset: {report.get('ground_truth')} manifest={report.get('dataset_manifest')}",
        "4 License: repo MIT fixtures; no customer packs",
        f"5 GT method: {report.get('method_doc')}",
        f"6 Env: {report.get('environment')}",
        "7 Repro: export_sprint2_dataset_manifest + run_sprint2_synthetic_baseline",
        f"8 Speed: mean={m.get('time_per_case_mean_s')} p95={m.get('time_per_case_p95_s')}",
        f"9 Quality: TP/FP/FN={m['tp']}/{m['fp']}/{m['fn']} P={m['precision']} R={m['recall']}",
        f"10 Remarks: remarks_count={m.get('remarks_count')}",
        f"11 Clashes: clashes_count={m.get('clashes_count')} (honesty: not planted)",
        f"12 Severity: {m.get('severity_distribution')}",
        f"13 Confusion: TP={m['tp']} FP={m['fp']} FN={m['fn']}",
        f"14 Agreement/nDCG: N/A — {(m.get('agreement') or {}).get('reason')}",
        f"15 Repro hash: {report.get('reproducibility_hash')}",
        f"16 Capabilities: {report.get('capabilities_snapshot')}",
        "17 Claims: synthetic_only; customer_precision_claim_publishable=false; "
        "precision_claim_publishable=false; customer_accuracy_not_established=true",
        "18 TZ map: see JSON twin tz_class_coverage",
        "19 Limits: no customer packs; 90% NOT confirmed; RT-001 open; NO_GO",
        f"generated_at={report['generated_at']}",
    ]


def _write_brief_aliases(
    *,
    repo: Path,
    report: dict[str, Any],
    out_json: Path,
    out_md: Path,
    out_pdf: Path,
    day: str = "2026-08-06",
) -> dict[str, Path]:
    """Principal-brief exact filenames (aliases of the canonical report set)."""

    evidence = repo / "docs" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    brief_md = evidence / f"SPRINT2_BASELINE_REPORT_{day}.md"
    brief_pdf = evidence / f"SPRINT2_BASELINE_REPORT_{day}.pdf"
    brief_md.write_bytes(out_md.read_bytes())
    brief_pdf.write_bytes(out_pdf.read_bytes())
    written["brief_md"] = brief_md
    written["brief_pdf"] = brief_pdf

    evidence_alias = {
        **report,
        "artifact_type": "sprint2_baseline_evidence_alias",
        "alias_of": str(out_json.relative_to(repo)).replace("\\", "/")
        if out_json.is_relative_to(repo)
        else str(out_json),
        "alias_note": (
            "Thin wrapper / twin of sprint2-baseline-report.json for tracker filename lock. "
            "Same synthetic payload; not a second measurement."
        ),
        "canonical_artifact_type": report.get("artifact_type"),
    }
    evidence_json = evidence / "sprint2-baseline-evidence.json"
    evidence_json.write_text(
        json.dumps(evidence_alias, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    written["evidence_json"] = evidence_json
    return written


def write_reports(
    report: dict[str, Any],
    *,
    out_json: Path,
    out_md: Path,
    out_pdf: Path,
    out_html: Path | None = None,
    also_dated: bool = True,
    also_brief_aliases: bool = False,
    brief_day: str = "2026-08-06",
) -> dict[str, Path]:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = _render_markdown(report, json_path=out_json)
    out_md.write_text(md, encoding="utf-8")
    _write_simple_pdf(out_pdf, _pdf_lines(report))
    written: dict[str, Path] = {"json": out_json, "md": out_md, "pdf": out_pdf}
    if out_html is not None:
        out_html.write_text(_render_html(report), encoding="utf-8")
        written["html"] = out_html
    repo = _repo_root()
    if also_dated:
        day = datetime.now(tz=UTC).date().isoformat()
        dated_dir = repo / "docs" / "evidence"
        for suffix, src in (
            (".json", out_json),
            (".md", out_md),
            (".pdf", out_pdf),
        ):
            dest = dated_dir / f"sprint2-synthetic-baseline-{day}{suffix}"
            dest.write_bytes(src.read_bytes())
            written[f"dated{suffix}"] = dest
    if also_brief_aliases:
        written.update(
            _write_brief_aliases(
                repo=repo,
                report=report,
                out_json=out_json,
                out_md=out_md,
                out_pdf=out_pdf,
                day=brief_day,
            )
        )
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument(
        "--dataset-manifest",
        type=Path,
        default=None,
        help="Optional Sprint 2 dataset MANIFEST.json path",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--output-pdf", type=Path, default=None)
    parser.add_argument("--output-html", type=Path, default=None)
    parser.add_argument(
        "--no-dated-alias",
        action="store_true",
        help="Skip writing dated sprint2-synthetic-baseline-* twins",
    )
    parser.add_argument(
        "--no-brief-alias",
        action="store_true",
        help="Skip principal-brief SPRINT2_BASELINE_REPORT_* / evidence aliases",
    )
    args = parser.parse_args(argv)
    repo = _repo_root()
    manifest_path = args.dataset_manifest
    if manifest_path is not None and not manifest_path.is_absolute():
        manifest_path = (Path.cwd() / manifest_path).resolve()
    report = run_baseline(iterations=args.iterations, dataset_manifest_path=manifest_path)
    evidence = repo / "docs" / "evidence"
    out_json = args.output_json or (evidence / "sprint2-baseline-report.json")
    out_md = args.output_md or (evidence / "sprint2-baseline-report.md")
    out_pdf = args.output_pdf or (evidence / "sprint2-baseline-report.pdf")
    out_html = args.output_html or (evidence / "sprint2-baseline-report.html")
    written = write_reports(
        report,
        out_json=out_json,
        out_md=out_md,
        out_pdf=out_pdf,
        out_html=out_html,
        also_dated=not args.no_dated_alias,
        also_brief_aliases=not args.no_brief_alias,
    )
    print(
        json.dumps(
            {
                "paths": {k: str(v) for k, v in written.items()},
                "metrics": report["metrics"],
                "claim_level": report["claim_level"],
                "customer_precision_claim_publishable": report[
                    "customer_precision_claim_publishable"
                ],
                "reproducibility_hash": report["reproducibility_hash"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
