"""Profile package analyze per-contour timings on a benchmark pack."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from time import perf_counter

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.package_trace import PackageTraceCollector
from aerobim.domain.run_manifest import build_run_manifest
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.tools.benchmark_project_package import (
    default_pack_path,
    load_benchmark_pack,
    repo_root,
)


def profile_package_trace(
    *,
    pack_path: Path,
    output_path: Path,
    storage_dir: Path | None = None,
) -> dict[str, object]:
    repo = repo_root().resolve()
    pack = load_benchmark_pack(pack_path.resolve(), repo_root_path=repo)
    settings = Settings.from_env()
    if storage_dir is not None:
        settings = replace(settings, storage_dir=storage_dir.resolve())
    container = bootstrap_container(settings)
    analyze = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)

    collector = PackageTraceCollector()
    analyze._package_trace_collector = collector  # noqa: SLF001 — profiling hook
    request = replace(pack.request, request_id=f"profile-{pack.pack_id}")
    started = perf_counter()
    report = analyze.execute(request)
    total_ms = round((perf_counter() - started) * 1000.0, 3)

    manifest = build_run_manifest(
        report,
        request_id=request.request_id,
        pack_id=pack.pack_id,
    )
    payload: dict[str, object] = {
        "artifact_type": "aerobim_package_profile_trace",
        "schema_version": "1.0.0",
        "pack_id": pack.pack_id,
        "pack_path": str(pack_path),
        "request_id": request.request_id,
        "analyze_total_ms": total_ms,
        "summary_passed": bool(report.summary.passed),
        "summary_outcome": getattr(getattr(report.summary, "outcome", None), "value", None),
        "reproducibility_hash": manifest.reproducibility_hash,
        "contour_trace": collector.as_dict(),
        "forbidden_claims": [
            "customer SLA <=30 min",
            "product accuracy >90%",
            "optimization complete",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Profile per-contour package analyze timings.")
    parser.add_argument(
        "--pack",
        type=Path,
        default=default_pack_path(),
        help="Benchmark pack JSON path",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=repo_root() / "docs" / "evidence" / "package-profile-trace-latest.json",
        help="Output JSON path",
    )
    parser.add_argument("--storage-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    profile_package_trace(
        pack_path=args.pack,
        output_path=args.output,
        storage_dir=args.storage_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
