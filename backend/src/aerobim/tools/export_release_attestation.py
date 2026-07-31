"""Export RELEASE_ATTESTATION.json: one machine-readable binding of commit, tree,
locks, Claims Lock, SBOM and baseline (external red-team P0: several competing
SSOTs make 'updated on date X' unprovable as a release fact).

Stdlib + git only. The attestation is generated per release/CI run and is NOT
committed (a committed one goes stale on the next commit by construction).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3].parent

_TRACKED = {
    "claims_lock_sha256": "audit/reports/CLAIMS_LOCK_2026_07_17.md",
    "dependency_lock_sha256": "backend/requirements-lock.txt",
    "dev_lock_sha256": "backend/requirements-dev-lock.txt",
    "sbom_sha256": "docs/evidence/sbom-backend-latest.json",
    "runtime_baseline_sha256": "docs/evidence/runtime-baseline-latest.json",
    "license_inventory_sha256": "audit/dependency_license_inventory.json",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, timeout=10, check=False
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def build_attestation() -> dict[str, object]:
    payload: dict[str, object] = {
        "artifact_type": "aerobim_release_attestation",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "commit": _git("rev-parse", "HEAD"),
        "tree_sha": _git("rev-parse", "HEAD^{tree}"),
        "working_tree_clean": _git("status", "--porcelain") == "",
        "note": (
            "binds the evidence set to one commit; regenerate per release/CI run; "
            "docker_digest and test_run_id are filled by the release pipeline "
            "(null here means 'not part of this attestation run', never 'verified')"
        ),
        "docker_digest": None,
        "test_run_id": None,
    }
    for key, rel in _TRACKED.items():
        path = _REPO_ROOT / rel
        payload[key] = _sha256(path) if path.is_file() else None
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Export release attestation JSON")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    payload = build_attestation()
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(serialized, encoding="utf-8")
        print(f"attestation written: {args.out}")
    else:
        print(serialized)


if __name__ == "__main__":
    main()
