"""Verify BCF T2 CDE-import evidence pack (log + screenshot + hashes).

T1 structural ZIP ≠ T2. Without required files status stays NOT_VERIFIED.
Never emit CDE_READY / CDE interoperable from this tool.

Wave H (2026-07-25, SLSA-style artifact binding): ``hashes.json`` is no longer
trusted as-is — every entry naming a file in the evidence directory is
**recomputed** (SHA-256) and must match, and the BCF digest can be **bound** to
the T1 structural-handoff evidence so the import proof provably refers to the
same archive we exported. A stale or foreign hash pack can never flip
``claim_allowed``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

_REQUIRED = ("import-log.txt", "screenshot.png", "hashes.json")
_FORBIDDEN_CLAIMS = frozenset(
    {
        "CDE_READY",
        "CDE interoperable",
        "BCF ready for CDE",
        "BCF готов для СОД",
    }
)

_CHECKLIST_ITEMS: tuple[tuple[str, str], ...] = (
    (
        "import-log.txt",
        "CDE import log or timestamped operator note (product, version, topic count)",
    ),
    ("screenshot.png", "CDE UI screenshot with imported topics visible"),
    ("hashes.json", "SHA-256 of import-log.txt, screenshot.png, and bcf_zip_sha256"),
    ("STATUS.json", "status=VERIFIED and claim_allowed=true only after real import"),
    ("T1 structural evidence", "bcf_zip_sha256 must match T1 structural-handoff digest"),
)


def build_t2_checklist_report(*, directory: Path | None = None) -> dict[str, Any]:
    """Dry-run checklist — no claim_allowed flip; surfaces required artifacts."""

    present: list[str] = []
    missing: list[str] = []
    if directory is not None:
        present = [name for name in _REQUIRED if (directory / name).is_file()]
        missing = [name for name in _REQUIRED if name not in present]
    return {
        "artifact_type": "bcf_t2_evidence_checklist",
        "schema_version": "1.0.0",
        "tier": "T2",
        "dry_run": True,
        "claim_allowed": False,
        "status": "not_verified",
        "reason": "checklist dry-run — customer CDE import environment is not provided",
        "required_files": list(_REQUIRED),
        "present_files": present,
        "missing_files": missing,
        "checklist": [
            {"artifact": name, "description": description} for name, description in _CHECKLIST_ITEMS
        ],
        "forbidden_claims": sorted(_FORBIDDEN_CLAIMS),
        "directory": str(directory) if directory is not None else None,
    }


def _missing_artifact_reason(missing: list[str]) -> str:
    if not missing:
        return "customer CDE import environment is not provided"
    labels = ", ".join(missing)
    hints = "; ".join(
        f"{name}: {next(desc for art, desc in _CHECKLIST_ITEMS if art == name)}"
        for name in missing
        if any(art == name for art, _ in _CHECKLIST_ITEMS)
    )
    return f"missing T2 artifacts ({labels}) — {hints}"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_hash_entries(
    directory: Path,
    hash_details: dict[str, Any],
) -> tuple[bool, list[str], str | None]:
    """Recompute SHA-256 for every hash entry that names a file in the pack.

    Returns ``(hashes_verified, mismatches, bcf_sha256)``. Required files must
    have matching entries; entries pointing at absent files are mismatches.
    ``bcf_sha256`` is the declared digest of the BCF archive (key named like a
    ``*.bcf``/``*.bcfzip`` file or ``bcf_zip_sha256``) for T1 binding.
    """

    mismatches: list[str] = []
    bcf_sha256: str | None = None
    verified_names: set[str] = set()

    for raw_name, raw_value in hash_details.items():
        name = str(raw_name)
        value = str(raw_value).strip().lower()
        lowered = name.lower()
        if lowered == "bcf_zip_sha256" or lowered.endswith((".bcf", ".bcfzip")):
            bcf_sha256 = value or None
            # The exported archive itself is not part of the evidence dir;
            # its digest is bound against T1 structural evidence instead.
            candidate = directory / name
            if candidate.is_file() and _sha256_file(candidate) != value:
                mismatches.append(f"{name}: recomputed sha256 differs from hashes.json")
            continue
        candidate = directory / name
        if not candidate.is_file():
            mismatches.append(f"{name}: listed in hashes.json but file is absent")
            continue
        if _sha256_file(candidate) != value:
            mismatches.append(f"{name}: recomputed sha256 differs from hashes.json")
            continue
        verified_names.add(name)

    for required_name in ("import-log.txt", "screenshot.png"):
        if (directory / required_name).is_file() and required_name not in verified_names:
            if not any(mismatch.startswith(f"{required_name}:") for mismatch in mismatches):
                mismatches.append(f"{required_name}: no verified sha256 entry in hashes.json")

    return (not mismatches, mismatches, bcf_sha256)


def _load_structural_bcf_sha256(structural_evidence: Path) -> set[str]:
    """Collect BCF archive digests from a T1 structural-handoff JSON."""

    try:
        payload = json.loads(structural_evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    digests: set[str] = set()
    if isinstance(payload, dict):
        for key in ("bcf_21", "bcf_30"):
            entry = payload.get(key)
            if isinstance(entry, dict):
                sha = str(entry.get("sha256") or "").strip().lower()
                if sha:
                    digests.add(sha)
    return digests


def verify_bcf_t2_evidence_dir(
    directory: Path,
    *,
    structural_evidence: Path | None = None,
) -> dict[str, Any]:
    """Assess T2 evidence directory; claim_allowed only when complete + STATUS VERIFIED.

    ``claim_allowed`` additionally requires every hash entry to recompute
    correctly and — when ``structural_evidence`` is supplied — the declared BCF
    digest to match a T1 structural digest (artifact binding).
    """

    status_path = directory / "STATUS.json"
    present = [name for name in _REQUIRED if (directory / name).is_file()]
    missing = [name for name in _REQUIRED if name not in present]

    raw_status = "MISSING_STATUS_FILE"
    claim_allowed_flag = False
    if status_path.is_file():
        try:
            payload = json.loads(status_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                raw_status = str(payload.get("status") or "NOT_VERIFIED")
                claim_allowed_flag = bool(payload.get("claim_allowed"))
        except (OSError, json.JSONDecodeError) as exc:
            raw_status = f"STATUS_UNREADABLE:{exc}"

    hashes_ok = False
    hash_details: dict[str, Any] = {}
    hashes_path = directory / "hashes.json"
    if hashes_path.is_file():
        try:
            hash_details = json.loads(hashes_path.read_text(encoding="utf-8"))
            hashes_ok = isinstance(hash_details, dict) and bool(hash_details)
        except (OSError, json.JSONDecodeError) as exc:
            hash_details = {"error": str(exc)}

    hashes_verified = False
    hash_mismatches: list[str] = []
    declared_bcf_sha256: str | None = None
    if hashes_ok and isinstance(hash_details, dict):
        hashes_verified, hash_mismatches, declared_bcf_sha256 = _verify_hash_entries(
            directory, hash_details
        )

    bcf_binding: dict[str, Any] = {"checked": False, "matches": None}
    binding_ok = True
    if structural_evidence is not None:
        structural_digests = _load_structural_bcf_sha256(structural_evidence)
        matches = bool(declared_bcf_sha256) and declared_bcf_sha256 in structural_digests
        bcf_binding = {
            "checked": True,
            "structural_evidence": str(structural_evidence),
            "declared_bcf_sha256": declared_bcf_sha256,
            "structural_sha256_count": len(structural_digests),
            "matches": matches,
        }
        binding_ok = matches

    complete = (
        not missing
        and hashes_ok
        and hashes_verified
        and binding_ok
        and raw_status == "VERIFIED"
        and claim_allowed_flag
    )
    status = "available" if complete else "not_verified"
    if complete:
        reason = "T2 evidence complete"
    elif missing:
        reason = _missing_artifact_reason(missing)
    elif hash_mismatches:
        reason = f"T2 hash verification failed: {'; '.join(hash_mismatches)}"
    elif not binding_ok:
        reason = (
            "T2 BCF digest does not match T1 structural evidence — "
            "import proof refers to a different archive"
        )
    else:
        reason = f"T2 incomplete: status={raw_status}, missing={missing}"

    return {
        "artifact_type": "bcf_t2_evidence_verification",
        "schema_version": "1.1.0",
        "tier": "T2",
        "status": status,
        "raw_status": raw_status,
        "affects_pass": True,
        "reason": reason,
        "claim_allowed": complete,
        "required_files": list(_REQUIRED),
        "present_files": present,
        "missing_files": missing,
        "hashes_present": hashes_ok,
        "hashes_verified": hashes_verified,
        "hash_mismatches": hash_mismatches,
        "bcf_binding": bcf_binding,
        "hashes": hash_details if isinstance(hash_details, dict) else {},
        "forbidden_claims": sorted(_FORBIDDEN_CLAIMS),
        "directory": str(directory),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("audit/evidence/cde-import-proof"),
        help="T2 evidence directory",
    )
    parser.add_argument(
        "--structural-evidence",
        type=Path,
        default=None,
        help="T1 structural-handoff JSON to bind the BCF digest against",
    )
    parser.add_argument(
        "--checklist",
        action="store_true",
        help="Dry-run: print required T2 artifacts checklist (never claim_allowed)",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args(argv)
    if args.checklist:
        report = build_t2_checklist_report(
            directory=args.dir.resolve() if args.dir else None,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    report = verify_bcf_t2_evidence_dir(
        args.dir.resolve(),
        structural_evidence=(
            args.structural_evidence.resolve() if args.structural_evidence else None
        ),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not args.json and not report["claim_allowed"]:
        print(
            "\nT2 remains NOT_VERIFIED — do not claim CDE_READY / CDE interoperable.",
            file=sys.stderr,
        )
    return 0 if report["claim_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
