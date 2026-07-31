"""Export a license/provenance manifest for every file under samples/ (P-010/P-013).

Two provenance classes only, assigned by location:
- samples/bcf-xsd/**, samples/ids-xsd/** -> vendored buildingSMART schemas
  (third-party; attribution required; license status = review_pending -- we do
  not invent license terms, legal review confirms redistribution conditions);
- everything else -> project-authored synthetic fixtures (repo MIT, no real
  project data, no personal data by construction).

Regenerate on any samples/ change; the committed manifest is gated by
backend/tests/test_samples_manifest_gate.py (every file listed, hashes match).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3].parent
_SAMPLES = _REPO_ROOT / "samples"
_VENDORED_PREFIXES = ("bcf-xsd/", "ids-xsd/")


def _looks_text(data: bytes) -> bool:
    if b"\x00" in data[:8192]:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _sha256(path: Path) -> str:
    """Hash bytes as committed on Linux CI (LF text), not Windows CRLF worktrees."""
    data = path.read_bytes()
    if b"\r\n" in data and _looks_text(data):
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def _entry(path: Path) -> dict[str, object]:
    rel = path.relative_to(_SAMPLES).as_posix()
    vendored = rel.startswith(_VENDORED_PREFIXES)
    if vendored:
        return {
            "path": rel,
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
            "provenance": "third_party_vendored",
            "source": "buildingSMART International (BCF 2.1/3.0 and IDS 1.0 XML schemas)",
            "license_status": "review_pending",
            "attribution_required": True,
            "redistribution": "verify against buildingSMART license before re-publishing",
            "production_use": "schema validation only",
            "personal_data": False,
        }
    return {
        "path": rel,
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
        "provenance": "project_authored_fixture",
        "source": "authored for AeroBIM tests/benchmarks; synthetic content",
        "license_status": "repo_mit",
        "attribution_required": False,
        "redistribution": "allowed under repo MIT",
        "production_use": "fixture only; never customer evidence",
        "personal_data": False,
    }


def build_manifest() -> dict[str, object]:
    files = sorted(p for p in _SAMPLES.rglob("*") if p.is_file())
    entries = [_entry(path) for path in files]
    return {
        "artifact_type": "samples_dataset_manifest",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "note": (
            "license/provenance map of the public fixture corpus; fixtures are "
            "synthetic and never customer evidence (corpus_kind=fixture); vendored "
            "buildingSMART schemas carry attribution and a review_pending license "
            "status rather than an invented one"
        ),
        "file_count": len(entries),
        "vendored_count": sum(1 for e in entries if e["provenance"] == "third_party_vendored"),
        "files": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export samples dataset manifest")
    parser.add_argument("--out", type=Path, default=_SAMPLES / "DATASET_MANIFEST.json")
    args = parser.parse_args()
    payload = build_manifest()
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"manifest written: {args.out} ({payload['file_count']} files)")


if __name__ == "__main__":
    main()
