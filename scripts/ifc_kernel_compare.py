#!/usr/bin/env python3
"""Measure one IfcOpenShell kernel on the repo's IFC fixtures and a project package.

Used by .github/workflows/ifc-kernel-compare.yml to compare 0.8.5 vs 0.9 on
the same runner class: entity counts per fixture, package findings, wall time
and peak RSS. Fixture-only numbers; not customer evidence.
"""

from __future__ import annotations

import argparse
import json
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _entity_counts() -> dict[str, dict[str, object]]:
    import ifcopenshell
    from aerobim.infrastructure.adapters.ifc_file_open import (
        open_ifc_model,
        reset_ifc_parse_cache_for_tests,
    )

    rows: dict[str, dict[str, object]] = {}
    for path in sorted((REPO / "samples").rglob("*.ifc")):
        rel = path.relative_to(REPO).as_posix()
        reset_ifc_parse_cache_for_tests()
        started = time.perf_counter()
        try:
            model = open_ifc_model(path)
            rows[rel] = {
                "schema": str(model.schema),
                "entities": sum(1 for _ in model),
                "ms": round((time.perf_counter() - started) * 1000, 2),
            }
        except Exception as exc:  # noqa: BLE001 - recorded, compared across kernels
            rows[rel] = {"error": f"{type(exc).__name__}: {str(exc)[:160]}"}
    rows["_kernel"] = {"ifcopenshell": str(ifcopenshell.version)}
    return rows


def _package(pack: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "sla.json"
        started = time.perf_counter()
        subprocess.run(
            [
                sys.executable,
                "-m",
                "aerobim.tools.measure_package_sla",
                "--pack",
                pack,
                "--max-minutes",
                "30.0",
                "--iterations",
                "1",
                "--warmup-iterations",
                "0",
                "--output",
                str(out),
            ],
            cwd=REPO,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        wall = time.perf_counter() - started
        data = json.loads(out.read_text(encoding="utf-8"))
    run = data["cold_run"]["benchmark"]["measured_runs"][0]
    return {
        "pack": pack,
        "issue_count": run["issue_count"],
        "requirement_count": run["requirement_count"],
        "analyze_ms": run["elapsed_ms"],
        "process_wall_s": round(wall, 3),
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = {"package": _package(args.pack), "fixtures": _entity_counts()}
    args.out.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
