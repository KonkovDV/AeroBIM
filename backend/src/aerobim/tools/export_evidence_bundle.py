"""Export a reproducible evidence bundle for a project-package benchmark pack.

Claim boundary: fixture packs prove Shared-gate honesty and provenance, not
customer accuracy, CDE import, or ≤30 min customer SLA.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, is_dataclass, replace
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from time import perf_counter
from typing import Any

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.tools.benchmark_project_package import load_benchmark_pack, repo_root

_SCHEMA_VERSION = "1.0.0"
_FORBIDDEN = (
    "customer accuracy >90%",
    "customer SLA ≤30 min",
    "CDE BCF import proven",
    "MEP system clash delivered",
    "native DWG ready",
    "independent calculation correctness",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return _json_safe(asdict(value))
    return str(value)


def _collect_source_paths(pack_path: Path, repo: Path) -> list[Path]:
    payload = json.loads(pack_path.read_text(encoding="utf-8"))
    request = payload.get("request") or {}
    paths: list[Path] = [pack_path]
    for key in (
        "ifc_path",
        "requirement_path",
        "ids_path",
        "technical_spec_path",
        "calculation_path",
    ):
        raw = request.get(key)
        if raw:
            paths.append((repo / str(raw)).resolve())
    drawings = request.get("drawings") or []
    if isinstance(drawings, list):
        for item in drawings:
            if isinstance(item, dict) and item.get("path"):
                paths.append((repo / str(item["path"])).resolve())
    return paths


def _capability_coverage(report: Any) -> dict[str, Any]:
    caps = getattr(report, "capabilities", None)
    if caps is None:
        return {"present": False, "fields": {}}
    data = _json_safe(asdict(caps))
    fields: dict[str, Any] = {}
    if isinstance(data, dict):
        for name, status in data.items():
            if isinstance(status, dict) and "status" in status:
                fields[name] = status
            elif status is not None:
                fields[name] = status
    return {"present": True, "fields": fields}


def _derived_outcome(report: Any, coverage: dict[str, Any]) -> str:
    passed = bool(getattr(report.summary, "passed", False))
    if passed:
        return "PASS"
    fields = coverage.get("fields") or {}
    blocking_non_ok = False
    for status in fields.values():
        if not isinstance(status, dict):
            continue
        state = str(status.get("status") or "").lower()
        if state in {"failed", "skipped", "missing", "not_verified", "not_implemented"}:
            blocking_non_ok = True
            break
    if blocking_non_ok and int(getattr(report.summary, "error_count", 0) or 0) == 0:
        return "BLOCKED"
    if int(getattr(report.summary, "issue_count", 0) or 0) > 0:
        return "FAILED"
    return "FAILED"


def export_evidence_bundle(
    *,
    pack_path: Path,
    output_dir: Path,
    storage_dir: Path | None = None,
) -> dict[str, Any]:
    repo = repo_root().resolve()
    pack_path = pack_path.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source_files: list[dict[str, str]] = []
    for path in _collect_source_paths(pack_path, repo):
        if not path.is_file():
            source_files.append(
                {
                    "path": str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path),
                    "sha256": "",
                    "status": "missing",
                }
            )
            continue
        rel = str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path)
        source_files.append({"path": rel, "sha256": _sha256_file(path), "status": "ok"})

    benchmark_pack = load_benchmark_pack(pack_path, repo_root_path=repo)
    settings = Settings.from_env()
    if storage_dir is not None:
        settings = replace(settings, storage_dir=storage_dir.resolve())
    container = bootstrap_container(settings)
    analyze = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)

    request = replace(
        benchmark_pack.request,
        request_id=f"evidence-bundle-{benchmark_pack.pack_id}",
    )
    started = perf_counter()
    report = analyze.execute(request)
    elapsed_ms = round((perf_counter() - started) * 1000.0, 3)

    coverage = _capability_coverage(report)
    derived = _derived_outcome(report, coverage)
    report_payload = _json_safe(asdict(report))
    if isinstance(report_payload, dict):
        report_payload["ifc_path"] = str(report.ifc_path)

    findings = _json_safe(list(report.issues))
    timings = {
        "analyze_elapsed_ms": elapsed_ms,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    manifest = {
        "artifact_type": "aerobim_evidence_bundle",
        "schema_version": _SCHEMA_VERSION,
        "pack_id": benchmark_pack.pack_id,
        "pack_version": benchmark_pack.pack_version,
        "pack_path": str(pack_path.relative_to(repo))
        if pack_path.is_relative_to(repo)
        else str(pack_path),
        "report_id": report.report_id,
        "summary_passed": bool(report.summary.passed),
        "derived_outcome": derived,
        "issue_count": report.summary.issue_count,
        "error_count": report.summary.error_count,
        "warning_count": report.summary.warning_count,
        "source_files": source_files,
        "forbidden_claims": list(_FORBIDDEN),
        "claim_boundary": (
            "summary.passed is Shared-gate technical status (ADR-001), "
            "not Shared→Published / contractual fitness."
        ),
        "timings": timings,
        "code_version": "aerobim-backend",
    }

    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output_dir / "report.json").write_text(
        json.dumps(report_payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    (output_dir / "findings.json").write_text(
        json.dumps(findings, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    (output_dir / "capability_coverage.json").write_text(
        json.dumps(coverage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output_dir / "timings.json").write_text(
        json.dumps(timings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    readme = f"""# AeroBIM evidence bundle

Pack: `{manifest["pack_path"]}`  
Report: `{report.report_id}`  
`summary.passed` (Shared-gate): `{manifest["summary_passed"]}`  
Derived outcome (docs mapping): `{derived}`

## Reproduce

```bash
cd backend
python -m aerobim.tools.export_evidence_bundle \\
  --pack {manifest["pack_path"]} \\
  --output {output_dir}
```

## Claim boundary

- Fixture / synthetic packs ≠ customer accuracy or Samolet SLA.
- BCF structural export is separate; CDE import is NOT_VERIFIED until Tier-2 evidence.
- Forbidden: {", ".join(_FORBIDDEN)}.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Export reproducible evidence bundle for a project-package pack "
            "(fixture honesty; not customer claims)."
        )
    )
    parser.add_argument(
        "--pack",
        type=Path,
        default=repo_root() / "samples" / "benchmarks" / "project-package-techlab-demo.json",
        help="Benchmark pack JSON (repo-relative paths)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output directory for the evidence bundle",
    )
    parser.add_argument(
        "--storage-dir",
        type=Path,
        default=None,
        help="Optional isolated storage directory",
    )
    args = parser.parse_args()
    manifest = export_evidence_bundle(
        pack_path=args.pack,
        output_dir=args.output,
        storage_dir=args.storage_dir,
    )
    print(json.dumps({"ok": True, "manifest": manifest}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
