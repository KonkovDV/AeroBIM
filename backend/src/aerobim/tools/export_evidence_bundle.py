"""Export a reproducible evidence bundle for a project-package benchmark pack.

Claim boundary: fixture packs prove Shared-gate honesty and provenance, not
customer accuracy, CDE import, or ≤30 min customer SLA.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import subprocess
from dataclasses import asdict, is_dataclass, replace
from datetime import UTC, datetime
from enum import Enum
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import perf_counter
from typing import Any

from aerobim.application.services.capability_policy import (
    build_signoff_policy,
    normalize_signoff_profile,
)
from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.tools.benchmark_project_package import load_benchmark_pack, repo_root

_SCHEMA_VERSION = "1.0.0"
_FORBIDDEN = (
    "customer accuracy >90%",
    "customer SLA <=30 min",
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


def _derived_outcome(
    report: Any,
    coverage: dict[str, Any],
    *,
    passed: bool | None = None,
) -> str:
    summary_outcome = getattr(getattr(report, "summary", None), "outcome", None)
    if summary_outcome is not None:
        raw = getattr(summary_outcome, "value", summary_outcome)
        text = str(raw).strip().lower()
        mapping = {
            "pass": "PASS",
            "pass_with_warnings": "PASS_WITH_WARNINGS",
            "review_required": "REVIEW_REQUIRED",
            "blocked": "BLOCKED",
            "failed": "FAILED",
        }
        if text in mapping:
            return mapping[text]

    effective_passed = (
        bool(passed) if passed is not None else bool(getattr(report.summary, "passed", False))
    )
    if effective_passed:
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


def _resolve_code_version(repo: Path) -> dict[str, str]:
    package_version = "unknown"
    try:
        package_version = version("aerobim-backend")
    except PackageNotFoundError:
        package_version = "0.1.0-dev"
    git_sha = ""
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if completed.returncode == 0:
            git_sha = completed.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        git_sha = ""
    label = f"aerobim-backend@{package_version}"
    if git_sha:
        label = f"{label}+{git_sha}"
    return {"label": label, "package_version": package_version, "git_sha": git_sha}


def _render_bundle_html(
    *,
    report: Any,
    pack_id: str,
    derived: str,
    coverage: dict[str, Any],
    code_version: str,
    enforced_passed: bool,
) -> str:
    esc = html.escape
    status = "PASSED" if enforced_passed else "FAILED"
    rows: list[str] = []
    for issue in list(report.issues)[:200]:
        rows.append(
            "<tr>"
            f"<td>{esc(str(getattr(issue, 'severity', '')))}</td>"
            f"<td>{esc(str(getattr(issue, 'rule_id', '')))}</td>"
            f"<td>{esc(str(getattr(issue, 'category', '')))}</td>"
            f"<td>{esc(str(getattr(issue, 'message', '')))}</td>"
            "</tr>"
        )
    if not rows:
        rows.append("<tr><td colspan='4'>No findings</td></tr>")
    cap_rows: list[str] = []
    fields = coverage.get("fields") or {}
    if isinstance(fields, dict):
        for name, status_obj in sorted(fields.items()):
            if isinstance(status_obj, dict):
                state = str(status_obj.get("status") or "")
                reason = str(status_obj.get("reason") or "")
            else:
                state = str(status_obj)
                reason = ""
            cap_rows.append(
                f"<tr><td>{esc(name)}</td><td>{esc(state)}</td><td>{esc(reason)}</td></tr>"
            )
    if not cap_rows:
        cap_rows.append("<tr><td colspan='3'>No capability fields</td></tr>")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>AeroBIM evidence — {esc(pack_id)}</title>
<style>
body {{ font-family: Segoe UI, sans-serif; margin: 1.5rem; color: #1a1a1a; }}
.pass {{ color: #0a7a32; }} .fail {{ color: #b00020; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; vertical-align: top; }}
th {{ background: #f4f4f4; }}
small {{ color: #555; }}
</style></head><body>
<h1>AeroBIM evidence bundle</h1>
<p><small>code: {esc(code_version)} · Shared-gate only (ADR-001)</small></p>
<p>Pack: <code>{esc(pack_id)}</code> · Report: <code>{esc(report.report_id)}</code></p>
<p class="{"pass" if enforced_passed else "fail"}">
  summary.passed={status} · derived_outcome={esc(derived)} ·
  errors={report.summary.error_count} warnings={report.summary.warning_count}
  issues={report.summary.issue_count}
</p>
<h2>Capability coverage</h2>
<table><thead><tr><th>Capability</th><th>Status</th><th>Reason</th></tr></thead>
<tbody>{"".join(cap_rows)}</tbody></table>
<h2>Findings (first 200)</h2>
<table><thead><tr><th>Severity</th><th>Rule</th><th>Category</th><th>Message</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table>
</body></html>
"""


def _write_logs_snippet(
    *,
    output_dir: Path,
    pack_id: str,
    report: Any,
    derived: str,
    elapsed_ms: float,
    code_version: str,
    enforced_passed: bool,
) -> None:
    lines = [
        f"generated_at={datetime.now(UTC).isoformat()}",
        f"code_version={code_version}",
        f"pack_id={pack_id}",
        f"report_id={report.report_id}",
        f"summary_passed={bool(enforced_passed)}",
        f"summary_passed_ambient={bool(report.summary.passed)}",
        f"derived_outcome={derived}",
        f"issue_count={report.summary.issue_count}",
        f"error_count={report.summary.error_count}",
        f"warning_count={report.summary.warning_count}",
        f"analyze_elapsed_ms={elapsed_ms}",
        "claim_boundary=summary.passed is Shared-gate (ADR-001), not Shared→Published",
    ]
    caps = getattr(report, "capabilities", None)
    if caps is not None:
        for name in (
            "clash",
            "ids",
            "ifc_validation",
            "raster",
            "dwg_dxf",
            "mep_system_clash",
            "calculation_match",
            "quantity",
        ):
            status = getattr(caps, name, None)
            if status is None:
                continue
            state = getattr(status, "status", status)
            state_value = getattr(state, "value", state)
            reason = getattr(status, "reason", None) or ""
            lines.append(f"capability.{name}={state_value}" + (f" ({reason})" if reason else ""))
    (output_dir / "logs_snippet.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    missing_sources: list[str] = []
    for path in _collect_source_paths(pack_path, repo):
        if not path.is_file():
            rel = str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path)
            source_files.append({"path": rel, "sha256": "", "status": "missing"})
            missing_sources.append(rel)
            continue
        rel = str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path)
        source_files.append({"path": rel, "sha256": _sha256_file(path), "status": "ok"})
    if missing_sources:
        raise FileNotFoundError(
            "Evidence bundle refuses missing pack inputs: " + ", ".join(missing_sources)
        )

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
    ambient_profile = normalize_signoff_profile(settings.signoff_profile)
    # RT C13: evidence-bundle PASS claims always evaluate under production policy.
    enforced_profile = "production"
    enforced_policy = build_signoff_policy(profile=enforced_profile)
    enforced_passed = enforced_policy.summary_passed(
        error_count=int(report.summary.error_count),
        capabilities=report.capabilities,
    )
    derived = _derived_outcome(report, coverage, passed=enforced_passed)
    code_meta = _resolve_code_version(repo)
    report_payload = _json_safe(asdict(report))
    if isinstance(report_payload, dict):
        report_payload["ifc_path"] = str(report.ifc_path)

    findings = _json_safe(list(report.issues))
    timings = {
        "analyze_elapsed_ms": elapsed_ms,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    runtime_settings = {
        "environment": settings.environment,
        "signoff_profile": settings.signoff_profile,
        "signoff_profile_ambient": ambient_profile,
        "signoff_profile_enforced": enforced_profile,
        "require_clash": settings.require_clash,
        "require_bsi_schema": settings.require_bsi_schema,
        "require_mep_system_clash": settings.require_mep_system_clash,
        "allow_anonymous_dev": settings.allow_anonymous_dev,
    }
    artifacts = {
        "manifest.json": True,
        "report.json": True,
        "findings.json": True,
        "capability_coverage.json": True,
        "timings.json": True,
        "report.html": True,
        "logs_snippet.txt": True,
        "README.md": True,
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
        "summary_passed": bool(enforced_passed),
        "summary_passed_ambient": bool(report.summary.passed),
        "summary_passed_enforced": bool(enforced_passed),
        "signoff_profile_ambient": ambient_profile,
        "signoff_profile_enforced": enforced_profile,
        "derived_outcome": derived,
        "issue_count": report.summary.issue_count,
        "error_count": report.summary.error_count,
        "warning_count": report.summary.warning_count,
        "source_files": source_files,
        "runtime_settings": runtime_settings,
        "forbidden_claims": list(_FORBIDDEN),
        "claim_boundary": (
            "summary.passed is Shared-gate technical status (ADR-001), "
            "not Shared→Published / contractual fitness. "
            "Bundle PASS claims are evaluated under production sign-off policy."
        ),
        "timings": timings,
        "code_version": code_meta["label"],
        "package_version": code_meta["package_version"],
        "git_sha": code_meta["git_sha"],
        "artifacts": artifacts,
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
    (output_dir / "report.html").write_text(
        _render_bundle_html(
            report=report,
            pack_id=benchmark_pack.pack_id,
            derived=derived,
            coverage=coverage,
            code_version=code_meta["label"],
            enforced_passed=bool(enforced_passed),
        ),
        encoding="utf-8",
    )
    _write_logs_snippet(
        output_dir=output_dir,
        pack_id=benchmark_pack.pack_id,
        report=report,
        derived=derived,
        elapsed_ms=elapsed_ms,
        code_version=code_meta["label"],
        enforced_passed=bool(enforced_passed),
    )

    readme = f"""# AeroBIM evidence bundle

Pack: `{manifest["pack_path"]}`  
Report: `{report.report_id}`  
`summary.passed` (Shared-gate): `{manifest["summary_passed"]}`  
Derived outcome (docs mapping): `{derived}`  
Code: `{code_meta["label"]}`

## Artifacts

- `manifest.json` — pack identity, hashes, Shared-gate + derived outcome
- `report.json` / `findings.json` / `capability_coverage.json`
- `report.html` — offline review surface
- `timings.json` / `logs_snippet.txt`
- `README.md` — this file

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

    output_hashes: dict[str, str] = {}
    for name in artifacts:
        path = output_dir / name
        if path.is_file() and name != "manifest.json":
            output_hashes[name] = _sha256_file(path)
    manifest["output_file_sha256"] = output_hashes
    # Re-write manifest with output hashes (manifest hash intentionally omitted).
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
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
    payload = json.dumps({"ok": True, "manifest": manifest}, indent=2, ensure_ascii=False)
    try:
        print(payload)
    except UnicodeEncodeError:
        # Windows consoles often use cp1251/cp866; ASCII-escape keeps the CLI usable.
        print(json.dumps({"ok": True, "manifest": manifest}, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
