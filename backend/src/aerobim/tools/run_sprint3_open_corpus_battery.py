"""Sprint 3 maximal open-corpus battery — regression, BSI, IFC-Bench, schema suite.

Writes committed evidence under ``docs/evidence/`` and ``audit/evidence/``.
Claim boundary: fixture/open-bench regression and timing only — NOT product accuracy.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.tools.benchmark_project_package import (
    benchmark_schema_suite,
    schema_suite_pack_paths,
    write_ifc_release_evidence,
)
from aerobim.tools.run_ifc_bench_smoke import evaluate_dataset
from aerobim.tools.run_open_corpora_profiles import (
    CLAIM_BOUNDARY,
    repo_root,
    run_all_profiles,
)

INTERNAL_DATA = Path(
    os.environ.get("AEROBIM_INTERNAL_DATA") or (repo_root().parent / "aerobim-internal-data")
)
INTERNAL_SCRIPTS = INTERNAL_DATA / "scripts"


def _write_evidence(
    payload: dict[str, Any],
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    profiles = payload.get("open_corpora", {}).get("profiles", {})
    regression = profiles.get("regression", {})
    bsi = profiles.get("regression_bsi", {})
    ifc_bench = payload.get("ifc_bench", {})
    lines = [
        "# Sprint 3 — open corpus battery",
        "",
        f"Generated: `{payload.get('generated_at')}`",
        "",
        f"**claim_boundary:** {CLAIM_BOUNDARY}",
        "",
        "## Summary",
        "",
        "| Rail | Result |",
        "|---|---|",
        f"| Fixture regression (n=7) | {regression.get('cases_matched')}/{regression.get('cases_run')} "
        f"(pass={regression.get('regression_pass')}) |",
    ]
    if bsi:
        lines.append(
            f"| BSI TestCases (n={bsi.get('cases_run')}) | raw "
            f"{bsi.get('binary_match_rate')} adjusted "
            f"{bsi.get('adjusted_binary_match_rate')} (pass={bsi.get('regression_pass')}) |"
        )
    for version, row in ifc_bench.items():
        if isinstance(row, dict) and row.get("summary"):
            summary = row["summary"]
            lines.append(
                f"| IFC-Bench {version} smoke | scored={summary.get('scored')} "
                f"matched={summary.get('matched')} |"
            )
    schema = payload.get("ifc_schema_suite", {})
    if schema.get("grouped"):
        lines.extend(["", "## IFC schema-suite (fixture)", ""])
        by_schema = schema["grouped"].get("by_schema", {})
        lines.append("| Schema | p50 ms | p95 ms | issues |")
        lines.append("|---|---:|---:|---:|")
        for name, metrics in sorted(by_schema.items()):
            if not isinstance(metrics, dict):
                continue
            timing = metrics.get("timing_ms", {})
            issues_raw = metrics.get("issue_count")
            if isinstance(issues_raw, dict):
                issues_display = issues_raw.get("last") or issues_raw.get("max")
            else:
                issues_display = issues_raw
            lines.append(
                f"| {name} | {timing.get('p50')} | {timing.get('p95')} | {issues_display} |"
            )
    lines.extend(
        [
            "",
            "## Reproduce",
            "",
            "```bash",
            "cd backend",
            "python -m aerobim.tools.run_sprint3_open_corpus_battery",
            "```",
            "",
        ]
    )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")


def _run_ifc_bench(root: Path, *, version: str) -> dict[str, Any] | None:
    if not root.is_dir():
        return None
    try:
        return evaluate_dataset(root, version=version)
    except Exception as exc:
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}


def _run_internal_script(name: str) -> dict[str, Any]:
    script = INTERNAL_SCRIPTS / name
    if not script.is_file():
        return {"status": "skipped", "reason": "script missing"}
    proc = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(INTERNAL_DATA),
    )
    return {
        "status": "ok" if proc.returncode == 0 else "failed",
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-4000:] if proc.stdout else "",
        "stderr_tail": proc.stderr[-2000:] if proc.stderr else "",
    }


def run_battery(
    *,
    include_bsi: bool = True,
    run_internal: bool = True,
) -> dict[str, Any]:
    root = repo_root()
    generated_at = datetime.now(tz=UTC).isoformat()

    open_corpora = run_all_profiles(repo=root, mode="full", include_bsi=include_bsi)

    ifc_bench: dict[str, Any] = {}
    for version, subdir in (("v1", ".local/ifc-bench"), ("v2", ".local/ifc-bench-v2")):
        result = _run_ifc_bench(root / subdir, version=version)
        if result is not None:
            ifc_bench[version] = result

    schema_payload = benchmark_schema_suite(
        pack_paths=schema_suite_pack_paths(),
        iterations=20,
        warmup_iterations=2,
        storage_dir=None,
        group_by="schema",
    )
    write_ifc_release_evidence(
        schema_payload,
        json_path=root / "audit" / "evidence" / "ifc-release-benchmark-2026-08.json",
        markdown_path=root / "docs" / "evidence" / "ifc-release-benchmark-2026-08.md",
    )

    internal: dict[str, Any] = {}
    if run_internal and INTERNAL_DATA.is_dir():
        for script in (
            "run_sprint3_week_ifc_metrics.py",
            "run_internal_corpus_continuation.py",
            "run_large_open_aerobim.py",
        ):
            internal[script] = _run_internal_script(script)

    profiles = open_corpora.get("profiles", {})
    regression = profiles.get("regression", {})
    bsi = profiles.get("regression_bsi", {})
    battery_pass = bool(regression.get("regression_pass")) and (
        not include_bsi or not bsi or bool(bsi.get("regression_pass"))
    )

    return {
        "artifact_type": "sprint3_open_corpus_battery",
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "claim_boundary": CLAIM_BOUNDARY,
        "checkpoint": CHECKPOINT,
        "battery_pass": battery_pass,
        "open_corpora": open_corpora,
        "ifc_bench": ifc_bench,
        "ifc_schema_suite": schema_payload,
        "internal_runs": internal,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-bsi",
        action="store_true",
        help="Skip regression-bsi (290 cases; saves ~15 min)",
    )
    parser.add_argument(
        "--skip-internal",
        action="store_true",
        help="Skip aerobim-internal-data runner scripts",
    )
    args = parser.parse_args(argv)

    payload = run_battery(
        include_bsi=not args.skip_bsi,
        run_internal=not args.skip_internal,
    )
    root = repo_root()
    json_path = root / "audit" / "evidence" / "sprint3-open-corpus-battery-2026-08.json"
    md_path = root / "docs" / "evidence" / "sprint3-open-corpus-battery-2026-08.md"
    _write_evidence(payload, json_path=json_path, markdown_path=md_path)
    print(json.dumps({"battery_pass": payload["battery_pass"], "json": str(json_path)}, indent=2))
    return 0 if payload["battery_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
