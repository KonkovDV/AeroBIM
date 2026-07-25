"""Verify an exported AeroBIM evidence bundle (tamper-evident, fail-closed).

SLSA-style separation of duties: the exporter writes ``output_file_sha256``;
this independent verifier **recomputes** every digest and cross-checks the
manifest against the hashed artifacts so a bundle cannot silently drift into
dual truth (edited findings.json, flipped PASS in report.html — RTATOM-G04
class). Claim boundary: tamper-evidence within the bundle, not cryptographic
authenticity — there is no signature; fixture packs still prove Shared-gate
honesty only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.name}: unreadable JSON: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{path.name}: expected JSON object")
        return None
    return payload


def verify_evidence_bundle(bundle_dir: Path) -> dict[str, Any]:
    """Verify bundle integrity + manifest/artifact consistency.

    ``ok`` only when every declared artifact exists, every declared digest
    recomputes, and cross-checks hold. Never fakes a pass: any unreadable or
    missing piece is a finding.
    """

    errors: list[str] = []
    manifest_path = bundle_dir / "manifest.json"
    if not manifest_path.is_file():
        return {
            "artifact_type": "aerobim_evidence_bundle_verification",
            "schema_version": "1.0.0",
            "ok": False,
            "verification": "failed",
            "errors": ["manifest.json missing"],
            "bundle_dir": str(bundle_dir),
        }

    manifest = _load_json(manifest_path, errors)
    hashes_checked = 0
    if manifest is not None:
        if manifest.get("artifact_type") != "aerobim_evidence_bundle":
            errors.append(f"unexpected artifact_type: {manifest.get('artifact_type')!r}")

        artifacts = manifest.get("artifacts")
        declared_names = [str(name) for name in artifacts] if isinstance(artifacts, dict) else []
        if not declared_names:
            errors.append("manifest.artifacts missing or empty")
        for name in declared_names:
            if not (bundle_dir / name).is_file():
                errors.append(f"declared artifact missing: {name}")

        output_hashes = manifest.get("output_file_sha256")
        if not isinstance(output_hashes, dict) or not output_hashes:
            errors.append("manifest.output_file_sha256 missing or empty")
            output_hashes = {}
        # Every declared artifact except the manifest itself must be hashed.
        for name in declared_names:
            if name != "manifest.json" and name not in output_hashes:
                errors.append(f"artifact has no digest entry: {name}")
        for name, declared in output_hashes.items():
            target = bundle_dir / str(name)
            if not target.is_file():
                errors.append(f"digest entry for absent file: {name}")
                continue
            recomputed = _sha256_file(target)
            hashes_checked += 1
            if recomputed != str(declared).strip().lower():
                errors.append(f"digest mismatch: {name}")

        # Dual-truth cross-checks against the hashed artifacts (RTATOM-G04 class).
        report = None
        report_path = bundle_dir / "report.json"
        if report_path.is_file():
            report = _load_json(report_path, errors)
        if report is not None:
            summary = report.get("summary") or {}
            if bool(summary.get("passed")) != bool(manifest.get("summary_passed_ambient")):
                errors.append("report.json summary.passed != manifest.summary_passed_ambient")
            if int(summary.get("issue_count") or 0) != int(manifest.get("issue_count") or 0):
                errors.append("report.json issue_count != manifest.issue_count")

        findings_path = bundle_dir / "findings.json"
        if findings_path.is_file():
            try:
                findings = json.loads(findings_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                findings = None
                errors.append(f"findings.json: unreadable JSON: {exc}")
            if isinstance(findings, list) and len(findings) != int(
                manifest.get("issue_count") or 0
            ):
                errors.append("findings.json length != manifest.issue_count")

        html_path = bundle_dir / "report.html"
        if html_path.is_file():
            html_text = html_path.read_text(encoding="utf-8")
            expected = (
                "summary.passed=PASSED"
                if manifest.get("summary_passed")
                else ("summary.passed=FAILED")
            )
            if expected not in html_text:
                errors.append(
                    "report.html Shared-gate status does not match manifest.summary_passed"
                )

        run_manifest_path = bundle_dir / "run_manifest.json"
        if run_manifest_path.is_file():
            run_manifest = _load_json(run_manifest_path, errors)
            if run_manifest is not None:
                declared_hash = str(manifest.get("reproducibility_hash") or "")
                actual_hash = str(run_manifest.get("reproducibility_hash") or "")
                if declared_hash != actual_hash:
                    errors.append("reproducibility_hash differs between manifest and run_manifest")

    return {
        "artifact_type": "aerobim_evidence_bundle_verification",
        "schema_version": "1.0.0",
        "ok": not errors,
        "verification": "passed" if not errors else "failed",
        "hashes_checked": hashes_checked,
        "errors": errors,
        "bundle_dir": str(bundle_dir),
        "claim_boundary": (
            "tamper-evidence within the bundle only; no signature — "
            "fixture packs prove Shared-gate honesty, not customer claims"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True, help="Bundle directory")
    args = parser.parse_args(argv)
    result = verify_evidence_bundle(args.bundle.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        print("\nEvidence bundle verification FAILED.", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
