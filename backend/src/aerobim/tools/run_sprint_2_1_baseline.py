"""Sprint 2.1 engineering baseline runner (fixture/synthetic only).

Never claims product accuracy or customer SLA. Writes JSON + Markdown artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must be a JSON object")
    return payload


def _score_mutations(mutations: dict[str, Any]) -> dict[str, Any]:
    """Score mutation SSOT honesty: detected vs known_undetected / control."""

    defects = mutations.get("defects") or []
    if not isinstance(defects, list):
        return {"tp": 0, "fp": 0, "fn": 0, "precision": None, "recall": None, "f1": None}
    # Without a live analyze of mutated copies, we report *declared* ground-truth
    # inventory only (engineering baseline), not measured TP/FP.
    finding = sum(1 for d in defects if isinstance(d, dict) and d.get("expected_status") == "finding")
    not_verifiable = sum(
        1 for d in defects if isinstance(d, dict) and d.get("expected_status") == "not_verifiable"
    )
    return {
        "declared_finding_cases": finding,
        "declared_not_verifiable_cases": not_verifiable,
        "tp": None,
        "fp": None,
        "fn": None,
        "precision": None,
        "recall": None,
        "f1": None,
        "note": (
            "TP/FP/FN require mutation apply + analyze; Sprint 2.1 CLI reports "
            "declared ground-truth inventory + pack timing only unless --run-analyze"
        ),
    }


def run_baseline(
    *,
    pack_path: Path,
    iterations: int,
    warmup_iterations: int,
    run_analyze: bool,
) -> dict[str, Any]:
    repo = _repo_root()
    pack = _load_json(pack_path)
    if pack.get("customer_evidence") is True:
        raise ValueError("customer_evidence=true forbidden in Sprint 2.1 engineering baseline")
    claim = pack.get("claim_level") or "engineering_baseline_only"
    if claim not in {"engineering_baseline_only", "fixture_only", "synthetic_only"}:
        raise ValueError(f"disallowed claim_level for sprint baseline: {claim}")

    files = [repo / rel for rel in (pack.get("files") or [])]
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing pack files: {missing}")

    file_hashes = {
        str(path.relative_to(repo)).replace("\\", "/"): {
            "sha256": _sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in files
    }
    total_bytes = sum(int(meta["bytes"]) for meta in file_hashes.values())

    mutations_path = pack.get("mutations")
    mutations: dict[str, Any] = {}
    if mutations_path:
        mutations = _load_json(repo / str(mutations_path))
    scores = _score_mutations(mutations)

    # Warmup / timed iterations: hash verification loop (deterministic, no network).
    for _ in range(max(0, warmup_iterations)):
        for path in files:
            _sha256_file(path)

    timings: list[float] = []
    for _ in range(max(1, iterations)):
        started = time.perf_counter()
        for path in files:
            _sha256_file(path)
        timings.append(time.perf_counter() - started)

    analyze_block: dict[str, Any] = {
        "requested": run_analyze,
        "status": "skipped",
        "reason": "default off; use --run-analyze for package analyze timing",
    }
    if run_analyze:
        analyze_block = {
            "requested": True,
            "status": "not_implemented_in_lightweight_cli",
            "reason": (
                "Full AnalyzeProjectPackageUseCase wiring is available via "
                "export_evidence_bundle / API; Sprint 2.1 CLI keeps hash+mutation inventory "
                "reproducible without DI bootstrap in this gate"
            ),
        }

    commit = _git_sha(repo)
    return {
        "artifact_type": "sprint_2_1_baseline",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "package_id": pack.get("package_id"),
        "commit": commit,
        "dataset_class": pack.get("dataset_class"),
        "customer_evidence": False,
        "claim_level": claim,
        "warning": (
            "Engineering baseline on public/fixture/synthetic package only. "
            "Does not confirm product accuracy, customer SLA ≤30 min, or close RT-001."
        ),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "pack": {
            "path": str(pack_path).replace("\\", "/"),
            "file_count": len(files),
            "total_bytes": total_bytes,
            "files": file_hashes,
        },
        "metrics": {
            **scores,
            "time_total_mean_s": sum(timings) / len(timings),
            "time_total_samples_s": timings,
            "time_to_first_finding": None,
            "clashes_expected": len(pack.get("expected_clashes") or []),
            "clashes_detected": None,
            "failed_capabilities": [],
            "review_required": None,
            "summary_outcome": None,
            "summary_passed": None,
        },
        "analyze": analyze_block,
        "tz_traceability": [
            {
                "requirement": "коллизии",
                "measured": "clash precision/recall",
                "status": "not_measured_in_lightweight_cli",
                "evidence": "use ifcclash pack + expected clashes",
            },
            {
                "requirement": "расчётные ошибки",
                "measured": "evidence matching (Level B)",
                "status": "partial",
                "evidence": "samples/benchmarks/injected-defects-level-b.json",
            },
            {
                "requirement": "≤30 минут",
                "measured": "scoped SLA",
                "status": "not_customer",
                "evidence": "fixture SLA honesty only",
            },
        ],
        "pdf_generation": "PDF_GENERATION_BLOCKED",
    }


def _write_markdown(report: dict[str, Any], path: Path) -> None:
    metrics = report.get("metrics") or {}
    lines = [
        "# Sprint 2.1 engineering baseline",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- commit: `{report.get('commit')}`",
        f"- package_id: `{report.get('package_id')}`",
        f"- claim_level: `{report.get('claim_level')}`",
        f"- customer_evidence: `{report.get('customer_evidence')}`",
        "",
        "> " + str(report.get("warning")),
        "",
        "## Metrics",
        "",
        f"- declared_finding_cases: {metrics.get('declared_finding_cases')}",
        f"- declared_not_verifiable_cases: {metrics.get('declared_not_verifiable_cases')}",
        f"- TP/FP/FN: {metrics.get('tp')}/{metrics.get('fp')}/{metrics.get('fn')}",
        f"- time_total_mean_s: {metrics.get('time_total_mean_s')}",
        f"- pdf_generation: {report.get('pdf_generation')}",
        "",
        "## Reproduction",
        "",
        "```bash",
        "python -m aerobim.tools.run_sprint_2_1_baseline \\",
        "  --pack ../samples/benchmarks/sprint-2-1/baseline-package.json \\",
        "  --output ../artifacts/sprint-2-1/baseline.json \\",
        "  --report ../artifacts/sprint-2-1/baseline.md",
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--warmup-iterations", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, default=None)
    parser.add_argument("--run-analyze", action="store_true")
    args = parser.parse_args(argv)

    report = run_baseline(
        pack_path=args.pack.resolve(),
        iterations=args.iterations,
        warmup_iterations=args.warmup_iterations,
        run_analyze=bool(args.run_analyze),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_markdown(report, args.report)
    if args.pdf is not None:
        # Do not invent a binary PDF. Record blocker next to requested path.
        marker = args.pdf.with_suffix(args.pdf.suffix + ".blocked.txt")
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(
            "PDF_GENERATION_BLOCKED\nSee companion Markdown/HTML report.\n",
            encoding="utf-8",
        )
    print(json.dumps({"ok": True, "output": str(args.output), "report": str(args.report)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
