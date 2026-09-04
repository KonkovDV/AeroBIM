"""Measure IFC open RSS on a local file — fixture-only by default.

Does not change the git default of ``AEROBIM_MAX_IFC_BYTES`` (SPF 256 MiB).
Files over the model ingest cap are classified and not opened. Files over
the SPF cap and under ingest open via RocksDB. OA-16 (owner-local RSS on a
file larger than 256 MiB) does not raise the SPF default; omit
``--write-docs-evidence`` and write JSON under ``.local/``.
Customer paths must not be written to ``docs/evidence``.
Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.core.security.upload_limits import DEV_DEFAULT_UPLOAD_BYTES
from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.ifc_size_policy import (
    CLAIM_BOUNDARY,
    analyze_cap_from_env,
    classify_ifc_bytes,
    ingest_cap_from_env,
)
from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_model


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def read_rss_bytes() -> int | None:
    """Best-effort RSS. None when the host cannot report it."""

    try:
        import psutil

        return int(psutil.Process().memory_info().rss)
    except Exception:  # noqa: S110 — optional psutil
        pass
    if sys.platform != "win32":
        try:
            import resource

            usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if sys.platform == "darwin":
                return int(usage)
            return int(usage) * 1024
        except Exception:  # noqa: S110 — optional resource
            pass
        return None
    try:
        return _windows_working_set_bytes()
    except Exception:
        return None


def _windows_working_set_bytes() -> int:
    import ctypes
    from ctypes import wintypes

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(ProcessMemoryCounters)
    # getattr: ctypes.windll is Windows-only; Linux CI mypy has no attr.
    windll = getattr(ctypes, "windll", None)
    if windll is None:
        raise OSError("ctypes.windll unavailable")
    handle = windll.kernel32.GetCurrentProcess()
    ok = windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
    if not ok:
        raise OSError("GetProcessMemoryInfo failed")
    return int(counters.WorkingSetSize)


def _is_committed_sample(path: Path, root: Path) -> bool:
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return relative.as_posix().startswith("samples/")


def measure_ifc_open_rss(
    path: Path,
    *,
    repo: Path | None = None,
    analyze_cap_bytes: int | None = None,
    ingest_cap_bytes: int | None = None,
) -> dict[str, Any]:
    """Open when the ingest envelope allows it. Never claims customer SLA."""

    root = repo or repo_root()
    resolved = path.resolve()
    size = resolved.stat().st_size if resolved.is_file() else 0
    cap = int(analyze_cap_bytes) if analyze_cap_bytes is not None else analyze_cap_from_env()
    ingest = int(ingest_cap_bytes) if ingest_cap_bytes is not None else ingest_cap_from_env()
    decision = classify_ifc_bytes(
        size,
        analyze_cap_bytes=cap,
        ingest_cap_bytes=ingest,
    )
    rss_before = read_rss_bytes()
    opened = False
    rss_after: int | None = None
    error: str | None = None
    if not resolved.is_file():
        error = "not_a_file"
    elif decision.analyze_allowed:
        try:
            open_ifc_model(resolved)
            opened = True
            rss_after = read_rss_bytes()
        except Exception as exc:
            error = type(exc).__name__
    delta = None
    if rss_before is not None and rss_after is not None:
        delta = max(0, rss_after - rss_before)
    sample = _is_committed_sample(resolved, root)
    return {
        "artifact_type": "ifc_open_rss_probe",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_level": "fixture_only" if sample else "local_uncommitted",
        "checkpoint": CHECKPOINT,
        "raises_default_cap": False,
        "analyze_cap_differs_from_git_default": cap != DEV_DEFAULT_UPLOAD_BYTES,
        "opened": opened,
        "file_bytes": size,
        "sample_in_git": sample,
        "rss_before_bytes": rss_before,
        "rss_after_bytes": rss_after,
        "rss_delta_bytes": delta,
        "representative_scale": False,
        "tiny_fixture_rss_delta_is_import_noise": size < 1_048_576,
        "error": error,
        "size_decision": decision.as_dict(),
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ifc",
        type=Path,
        default=None,
        help="IFC path. Default: committed wall-pset-ifc2x3 fixture.",
    )
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--write-docs-evidence",
        action="store_true",
        help="Write docs/evidence only for committed samples/ paths.",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    ifc = args.ifc or (root / "samples" / "ifc" / "wall-pset-ifc2x3.ifc")
    payload = measure_ifc_open_rss(ifc, repo=root)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    out = args.output or (root / "artifacts" / "quality" / "ifc-open-rss-probe.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    if args.write_docs_evidence:
        if not payload["sample_in_git"]:
            print("refusing --write-docs-evidence for a path outside samples/", file=sys.stderr)
            return 2
        evidence = root / "docs" / "evidence" / "ifc-open-rss-probe-latest.json"
        evidence.write_text(text, encoding="utf-8")
        print(f"docs_evidence={evidence}")
    print(
        json.dumps(
            {
                "status": "EXECUTED",
                "opened": payload["opened"],
                "file_bytes": payload["file_bytes"],
                "band": payload["size_decision"]["band"],
                "rss_delta_bytes": payload["rss_delta_bytes"],
                "raises_default_cap": False,
                "checkpoint": CHECKPOINT,
                "output": str(out),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
