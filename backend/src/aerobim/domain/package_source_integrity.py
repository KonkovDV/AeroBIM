"""Package source hash chain (RT-021 eng) — read-only inventory of original bytes.

Honesty: never rewrites sources; never claims УКЭП / crypto verify. Builds an
ordered SHA-256 manifest so any later normalize/re-save can be detected as a
hash mismatch against the intake inventory.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CLAIM_BOUNDARY = (
    "Engineering hash inventory of package source bytes (read-only open). "
    "Not УКЭП validation; not legal integrity of qualified signatures. "
    "Mismatch vs intake inventory means originals may have been rewritten."
)


@dataclass(frozen=True)
class SourceHashEntry:
    relative_path: str
    sha256: str
    bytes: int


def sha256_file_readonly(path: Path) -> tuple[str, int]:
    """SHA-256 of file bytes via read-only open; returns (hex, size)."""

    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def build_package_source_hash_chain(
    *,
    root: Path,
    paths: Sequence[Path],
    package_id: str | None = None,
) -> dict[str, Any]:
    """Ordered hash chain for package sources under ``root`` (fail on escape)."""

    root_resolved = root.resolve()
    entries: list[SourceHashEntry] = []
    missing: list[str] = []
    escaped: list[str] = []

    for raw in paths:
        path = Path(raw)
        if not path.is_file():
            missing.append(str(path))
            continue
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(root_resolved).as_posix()
        except ValueError:
            escaped.append(str(resolved))
            continue
        digest, size = sha256_file_readonly(resolved)
        entries.append(SourceHashEntry(relative_path=relative, sha256=digest, bytes=size))

    entries_sorted = tuple(sorted(entries, key=lambda item: item.relative_path))
    chain_material = "\n".join(f"{item.relative_path}:{item.sha256}" for item in entries_sorted)
    chain_digest = hashlib.sha256(chain_material.encode("utf-8")).hexdigest()

    return {
        "artifact_type": "package_source_hash_chain",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "package_id": package_id,
        "root": root_resolved.as_posix(),
        "entry_count": len(entries_sorted),
        "entries": [
            {
                "relative_path": item.relative_path,
                "sha256": item.sha256,
                "bytes": item.bytes,
            }
            for item in entries_sorted
        ],
        "chain_sha256": chain_digest,
        "missing_paths": missing,
        "escaped_paths": escaped,
        "claim_boundary": CLAIM_BOUNDARY,
        "status": ("ok" if entries_sorted and not missing and not escaped else "incomplete"),
    }


def compare_hash_chains(
    expected: dict[str, Any],
    observed: dict[str, Any],
) -> dict[str, Any]:
    """Compare two chain artifacts; mismatches mean sources changed after intake."""

    exp_map = {
        str(item.get("relative_path")): str(item.get("sha256") or "").lower()
        for item in (expected.get("entries") or ())
        if isinstance(item, dict)
    }
    obs_map = {
        str(item.get("relative_path")): str(item.get("sha256") or "").lower()
        for item in (observed.get("entries") or ())
        if isinstance(item, dict)
    }
    mismatches: list[str] = []
    for path, digest in exp_map.items():
        actual = obs_map.get(path)
        if actual is None:
            mismatches.append(f"missing:{path}")
        elif actual != digest:
            mismatches.append(f"changed:{path}")
    for path in obs_map:
        if path not in exp_map:
            mismatches.append(f"extra:{path}")
    chain_ok = (
        str(expected.get("chain_sha256") or "") == str(observed.get("chain_sha256") or "")
        and not mismatches
    )
    return {
        "artifact_type": "package_source_hash_chain_diff",
        "match": chain_ok and not mismatches,
        "mismatches": mismatches,
        "claim_boundary": CLAIM_BOUNDARY,
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "SourceHashEntry",
    "build_package_source_hash_chain",
    "compare_hash_chains",
    "sha256_file_readonly",
]
