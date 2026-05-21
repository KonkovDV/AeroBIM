"""Measure project-package analysis SLA against Samolet TechLab target (≤ 30 min)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from aerobim.tools.benchmark_project_package import (
    benchmark_project_package,
    default_pack_path,
    repo_root,
)


def measure_package_sla(
    pack_path: Path,
    *,
    max_minutes: float,
    iterations: int = 1,
    warmup_iterations: int = 0,
) -> dict[str, object]:
    payload = benchmark_project_package(
        pack_path=pack_path,
        iterations=iterations,
        warmup_iterations=warmup_iterations,
        storage_dir=None,
    )
    summary = payload["summary"]
    max_ms = float(summary["max_ms"])
    avg_ms = float(summary["avg_ms"])
    max_minutes_observed = round(max_ms / 60_000.0, 4)
    avg_minutes_observed = round(avg_ms / 60_000.0, 4)
    sla_pass = max_minutes_observed <= max_minutes

    return {
        "artifact_type": "samolet_package_sla",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "customer_reference": "https://i.moscow/techlab/samolet",
        "sla_target_minutes": max_minutes,
        "sla_pass": sla_pass,
        "max_minutes_observed": max_minutes_observed,
        "avg_minutes_observed": avg_minutes_observed,
        "benchmark": payload,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure analyze/project-package wall time vs Samolet ≤30 min SLA"
    )
    parser.add_argument(
        "--pack",
        type=Path,
        default=default_pack_path(),
        help="Benchmark pack manifest (default: pilot-moscow if exists, else baseline)",
    )
    parser.add_argument(
        "--max-minutes",
        type=float,
        default=30.0,
        help="SLA ceiling in minutes (Samolet task page default: 30)",
    )
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--warmup-iterations", type=int, default=0)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    pilot_pack = repo_root() / "samples" / "benchmarks" / "project-package-pilot-moscow-v1.json"
    pack_path = args.pack
    if pack_path == default_pack_path() and pilot_pack.exists():
        pack_path = pilot_pack

    result = measure_package_sla(
        pack_path,
        max_minutes=args.max_minutes,
        iterations=args.iterations,
        warmup_iterations=args.warmup_iterations,
    )
    serialized = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.output.with_suffix(".tmp")
        tmp.write_text(serialized, encoding="utf-8")
        tmp.replace(args.output)
    else:
        print(serialized)

    if not result["sla_pass"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
