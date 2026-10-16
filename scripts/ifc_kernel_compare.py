#!/usr/bin/env python3
"""Measure one IfcOpenShell kernel on the repo's IFC fixtures and a project package.

Used by .github/workflows/ifc-kernel-compare.yml to compare 0.8.5 vs 0.9 on
the same runner class: entity counts per fixture, package findings, wall time
and peak RSS. Fixture-only numbers; not customer evidence.
"""

from __future__ import annotations

import argparse
import json
import os
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


def _run_child(cmd: list[str]) -> tuple[float, int]:
    """Run one child; return (wall seconds, that child's own peak RSS in KiB)."""

    started = time.perf_counter()
    proc = subprocess.Popen(cmd, cwd=REPO, stdout=subprocess.DEVNULL)
    _, status, usage = os.wait4(proc.pid, 0)
    proc.returncode = os.waitstatus_to_exitcode(status)
    wall = time.perf_counter() - started
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)
    return wall, int(usage.ru_maxrss)


_OPEN_PROBE = """
import json, resource, sys, time
from pathlib import Path
from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_model
started = time.perf_counter()
model = open_ifc_model(Path(sys.argv[1]))
opened = time.perf_counter() - started
row = {
    "schema": str(model.schema),
    "entities": sum(1 for _ in model),
    "products": len(model.by_type("IfcProduct")),
    "walls": len(model.by_type("IfcWall")),
    "open_s": round(opened, 3),
    "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
}
Path(sys.argv[2]).write_text(json.dumps(row), encoding="utf-8")
"""


def _external(path: Path, pack: str) -> dict[str, object]:
    """Open probe + full package run on one large real model, each in its own child."""

    with tempfile.TemporaryDirectory() as tmp:
        probe_out = Path(tmp) / "probe.json"
        _run_child([sys.executable, "-c", _OPEN_PROBE, str(path), str(probe_out)])
        probe = json.loads(probe_out.read_text(encoding="utf-8"))
        spec = json.loads((REPO / pack).read_text(encoding="utf-8"))
        spec["pack_id"] = f"{spec['pack_id']}-external-{path.stem}"
        # Pack paths must stay inside the repo (benchmark loader refuses escapes).
        spec["request"]["ifc_path"] = path.resolve().relative_to(REPO).as_posix()
        ext_pack = Path(tmp) / f"pack-{path.stem}.json"
        ext_pack.write_text(json.dumps(spec), encoding="utf-8")
        package = _package(str(ext_pack))
    package["pack"] = f"{pack} with ifc_path={path.name}"
    return {"open": probe, "package": package}


def _package(pack: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "sla.json"
        wall, peak_rss = _run_child(
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
            ]
        )
        data = json.loads(out.read_text(encoding="utf-8"))
    run = data["cold_run"]["benchmark"]["measured_runs"][0]
    return {
        "pack": pack,
        "issue_count": run["issue_count"],
        "requirement_count": run["requirement_count"],
        "analyze_ms": run["elapsed_ms"],
        "process_wall_s": round(wall, 3),
        "peak_rss_kib": peak_rss,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--external-dir",
        type=Path,
        default=None,
        help="Directory of large real IFC models (scripts/fetch_external_ifc.py)",
    )
    args = parser.parse_args()
    result: dict[str, object] = {
        "package": _package(args.pack),
        "fixtures": _entity_counts(),
    }
    if args.external_dir is not None:
        result["external"] = {
            path.name: _external(path, args.pack)
            for path in sorted(args.external_dir.glob("*.ifc"))
        }
    args.out.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
