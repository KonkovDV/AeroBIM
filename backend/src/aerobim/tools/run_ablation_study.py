"""Run multimodal ablation packs A0–A3 and emit comparison metrics."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import TypedDict

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import FindingCategory
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.tools.benchmark_project_package import load_benchmark_pack, repo_root


class AblationConfigurationRow(TypedDict):
    pack_id: str
    ablation_mode: str
    issue_count: int
    requirement_count: int
    cross_document_issues: int
    conflict_kind_breakdown: dict[str, int]
    category_breakdown: dict[str, int]


class AblationStudyReport(TypedDict):
    artifact_type: str
    pack_count: int
    configurations: list[AblationConfigurationRow]


def _default_packs() -> list[Path]:
    root = repo_root() / "samples" / "benchmarks"
    return [
        root / "project-package-ablation-a0.json",
        root / "project-package-ablation-a1.json",
        root / "project-package-ablation-a2.json",
        root / "project-package-ablation-a3.json",
    ]


def run_ablation(pack_paths: list[Path], output: Path | None) -> AblationStudyReport:
    repo = repo_root()
    container = bootstrap_container(Settings.from_env())
    use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)

    rows: list[AblationConfigurationRow] = []
    for pack_path in pack_paths:
        pack = load_benchmark_pack(pack_path, repo_root_path=repo)
        request = replace(pack.request, request_id=f"ablation-{pack.pack_id}")
        report = use_case.execute(request)

        conflict_counts = Counter(
            issue.conflict_kind.value for issue in report.issues if issue.conflict_kind is not None
        )
        category_counts = Counter(issue.category.value for issue in report.issues)

        rows.append(
            {
                "pack_id": pack.pack_id,
                "ablation_mode": str(
                    json.loads(pack_path.read_text(encoding="utf-8")).get(
                        "ablation_mode", pack.pack_id
                    )
                ),
                "issue_count": len(report.issues),
                "requirement_count": report.summary.requirement_count,
                "cross_document_issues": category_counts.get(
                    FindingCategory.CROSS_DOCUMENT.value, 0
                ),
                "conflict_kind_breakdown": dict(sorted(conflict_counts.items())),
                "category_breakdown": dict(sorted(category_counts.items())),
            }
        )

    payload: AblationStudyReport = {
        "artifact_type": "ablation_study_report",
        "pack_count": len(rows),
        "configurations": rows,
    }
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path = output.with_suffix(".md")
        md_path.write_text(_to_markdown_table(payload), encoding="utf-8")
    return payload


def _to_markdown_table(payload: AblationStudyReport) -> str:
    lines = [
        "# AeroBIM multimodal ablation study (paper table)",
        "",
        "| Mode | Pack | Requirements | Issues | Cross-doc | Category breakdown |",
        "|------|------|-------------:|-------:|----------:|--------------------|",
    ]
    for row in payload["configurations"]:
        cats = ", ".join(f"{k}={v}" for k, v in row["category_breakdown"].items()) or "—"
        lines.append(
            f"| {row['ablation_mode']} | `{row['pack_id']}` | {row['requirement_count']} | "
            f"{row['issue_count']} | {row['cross_document_issues']} | {cats} |"
        )
    lines.extend(
        [
            "",
            (
                "Modes: **A0** IDS-only → **A1** + IFC properties → "
                "**A2** + cross-document → **A3** reduced multimodal."
            ),
            "",
            (
                f"Pack count: {payload['pack_count']}. "
                "Regenerate via `python -m aerobim.tools.run_ablation_study`."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run AeroBIM ablation study (A0–A3).")
    parser.add_argument(
        "--output",
        type=Path,
        default=repo_root() / "artifacts" / "ablation-study-report.json",
        help="JSON output path",
    )
    parser.add_argument(
        "--pack",
        type=Path,
        action="append",
        default=None,
        help="Optional extra pack manifest (repeatable)",
    )
    args = parser.parse_args(argv)

    pack_paths = list(args.pack) if args.pack else _default_packs()
    for pack_path in pack_paths:
        if not pack_path.exists():
            print(f"Pack not found: {pack_path}", file=sys.stderr)
            return 1

    payload = run_ablation(pack_paths, args.output)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
