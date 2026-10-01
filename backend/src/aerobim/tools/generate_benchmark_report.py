"""Generate publication-grade benchmark report (Markdown + JSON artifacts)."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from aerobim.tools.benchmark_project_package import repo_root
from aerobim.tools.evaluate_extraction import ExtractionQualityReport, _evaluate_manifest
from aerobim.tools.run_ablation_study import AblationStudyReport, _default_packs, run_ablation


def _pip_freeze_hash() -> str:
    try:
        freeze = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=False,
        )
        if freeze.returncode != 0:
            return "unavailable"
        return hashlib.sha256(freeze.stdout.encode("utf-8")).hexdigest()[:16]
    except OSError:
        return "unavailable"


def _ifc_release() -> str:
    try:
        import ifcopenshell

        return getattr(ifcopenshell, "version", lambda: "unknown")()
    except Exception:
        return "unknown"


def generate_report(output_dir: Path) -> dict[str, object]:
    repo = repo_root()
    manifest = repo / "samples" / "benchmarks" / "russian-aec-ground-truth.json"
    extraction: ExtractionQualityReport = _evaluate_manifest(manifest)
    ablation: AblationStudyReport = run_ablation(
        _default_packs(), output_dir / "ablation-study-report.json"
    )

    generated_at = datetime.now(UTC).isoformat()
    env_block = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "pip_freeze_hash": _pip_freeze_hash(),
        "ifc_release": _ifc_release(),
    }

    payload: dict[str, object] = {
        "artifact_type": "academic_benchmark_report",
        "generated_at": generated_at,
        "environment": env_block,
        "extraction_quality": extraction,
        "ablation_study": ablation,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"benchmark-report-{generated_at[:10]}.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        f"# AeroBIM Benchmark Report ({generated_at[:10]})",
        "",
        "## Environment",
        "",
        f"- Platform: `{env_block['platform']}`",
        f"- Python: `{env_block['python_version']}`",
        f"- pip freeze hash: `{env_block['pip_freeze_hash']}`",
        f"- ifcopenshell: `{env_block['ifc_release']}`",
        "",
        "## Extraction quality (RU corpus)",
        "",
        f"- Macro F1: **{extraction['macro_f1']:.3f}**",
        f"- Macro precision: {extraction['macro_precision']:.3f}",
        f"- Macro recall: {extraction['macro_recall']:.3f}",
        f"- Fixtures: {len(extraction['fixtures'])}",
        "",
        "### Per-discipline F1",
        "",
        "| Discipline | Fixtures | Macro F1 |",
        "|---|---:|---:|",
    ]
    for discipline, metrics in sorted(extraction["per_discipline"].items()):
        md_lines.append(
            f"| {discipline} | {int(metrics.get('fixture_count', 0))} | "
            f"{metrics.get('macro_f1', 0):.3f} |"
        )

    md_lines.extend(
        [
            "",
            "## Multimodal ablation (A0–A3)",
            "",
            "| Mode | Issues | Requirements | Cross-doc |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in ablation["configurations"]:
        md_lines.append(
            f"| {row.get('ablation_mode', '?')} | {row.get('issue_count', 0)} | "
            f"{row.get('requirement_count', 0)} | {row.get('cross_document_issues', 0)} |"
        )

    md_lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "Deterministic multimodal QA kernel with provenance — not full-code compliance.",
            "",
            f"_Generated at {generated_at}_",
        ]
    )

    md_path = output_dir / f"benchmark-report-{generated_at[:10]}.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    payload["artifacts"] = {"json": str(json_path), "markdown": str(md_path)}
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate academic benchmark report bundle.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root() / "docs" / "evidence",
        help="Directory for Markdown and JSON artifacts",
    )
    args = parser.parse_args(argv)
    payload = generate_report(args.output_dir.resolve())
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
