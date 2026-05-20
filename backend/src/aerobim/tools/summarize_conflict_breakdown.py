"""Summarize ConflictKind distribution for a benchmark or pilot pack."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import FindingCategory
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.tools.benchmark_project_package import load_benchmark_pack


def summarize_pack(pack_path: Path, repo_root: Path) -> dict[str, object]:
    benchmark_pack = load_benchmark_pack(pack_path, repo_root_path=repo_root)
    container = bootstrap_container(Settings.from_env())
    analyze_use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)
    request = replace(benchmark_pack.request, request_id="conflict-breakdown-001")
    report = analyze_use_case.execute(request)

    cross_doc = [issue for issue in report.issues if issue.category == FindingCategory.CROSS_DOCUMENT]
    breakdown = Counter(
        issue.conflict_kind.value if issue.conflict_kind is not None else "unset"
        for issue in cross_doc
    )

    return {
        "pack": pack_path.name,
        "total_issues": len(report.issues),
        "cross_document_issues": len(cross_doc),
        "conflict_kind_breakdown": dict(sorted(breakdown.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize ConflictKind counts for a benchmark pack")
    parser.add_argument(
        "--pack",
        type=Path,
        default=Path("samples/benchmarks/project-package-pilot-moscow-v1.json"),
        help="Benchmark manifest path relative to AeroBIM repo root",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[4]
    pack_path = args.pack if args.pack.is_absolute() else repo_root / args.pack
    payload = summarize_pack(pack_path, repo_root)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
