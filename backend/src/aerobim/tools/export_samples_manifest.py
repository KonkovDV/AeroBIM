"""Export a license/provenance manifest for every file under samples/ (P-010/P-013).

Provenance classes:
- samples/bcf-xsd/**, samples/ids-xsd/** -> vendored buildingSMART schemas
  (committed rows keep CC BY-ND 4.0 after RT-W-01; do not full-rebuild);
- samples/ids/moexp/** -> third-party official MOEXP IDS/mappings (not a
  Samolet profile);
- samples/ids/moscow-agr/** -> official Moscow AGR IDS (stroimprosto);
- samples/ids/spbexp/** -> official SPb GAU CGE IDS;
- samples/agr/dgp/** -> official ДГП AGR XML/XSD examples;
- samples/xsd/minstroy/*.xsd -> official MinStroy XSD (intake only);
- everything else -> project-authored synthetic fixtures (repo MIT, no real
  project data, no personal data by construction).

Prefer ``--merge-missing`` so existing vendored license rows stay intact.
The committed manifest is gated by backend/tests/test_samples_manifest_gate.py.
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


def _official(
    path: Path,
    *,
    source: str,
    redistribution: str,
) -> dict[str, object]:
    rel = path.relative_to(_SAMPLES).as_posix()
    return {
        "path": rel,
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
        "provenance": "third_party_official",
        "source": source,
        "license_status": "publisher_terms",
        "attribution_required": True,
        "redistribution": redistribution,
        "production_use": "fixture engine coverage only; never customer evidence",
        "personal_data": False,
    }


def _entry(path: Path) -> dict[str, object]:
    rel = path.relative_to(_SAMPLES).as_posix()
    if rel.startswith("ids/moexp/"):
        return _official(
            path,
            source=(
                "GAU MO / MOEXP published IDS and IFC4 mappings (moexp.ru); "
                "not a Samolet customer profile"
            ),
            redistribution="redistributed as published; see samples/ids/moexp/SOURCE.md",
        )
    if rel.startswith("ids/moscow-agr/"):
        return _official(
            path,
            source=(
                "Moscow DGP / stroimprosto published AGR IDS; not a Samolet "
                "profile and not the frozen moscow_agr DI port"
            ),
            redistribution=("redistributed as published; see samples/ids/moscow-agr/SOURCE.md"),
        )
    if rel.startswith("ids/spbexp/"):
        return _official(
            path,
            source=("SPb GAU CGE published IDS 1.0; not a Samolet customer profile"),
            redistribution="redistributed as published; see samples/ids/spbexp/SOURCE.md",
        )
    if rel.startswith("agr/dgp/"):
        return _official(
            path,
            source=("Moscow DGP / stroimprosto AGR TEP example + Vedomost XSD; not a Samolet pack"),
            redistribution="redistributed as published; see samples/agr/dgp/SOURCE.md",
        )
    if rel.startswith("xsd/minstroy/") and rel.endswith(".xsd"):
        return _official(
            path,
            source=(
                "MinStroy published XML Schema (minstroyrf.gov.ru/tim/xml-skhemy); "
                "intake pre-check only; not RT-001 CLOSED"
            ),
            redistribution="redistributed as published; see samples/xsd/minstroy/SOURCE.md",
        )
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


def _refresh_hash(entry: dict[str, object], path: Path) -> dict[str, object]:
    """Update sha256/bytes only. Keep provenance and license rows intact."""

    out = dict(entry)
    out["sha256"] = _sha256(path)
    out["bytes"] = path.stat().st_size
    return out


def merge_missing_into(existing: dict[str, object]) -> dict[str, object]:
    """Add on-disk samples files that are not listed. Preserve existing rows.

    Full rebuild would reset vendored buildingSMART rows to review_pending and
    break the CC BY-ND gate. Merge-only is the honest local fix. Hashes of
    already-listed files are refreshed so the gate matches the worktree.
    """

    files_raw = existing.get("files")
    if not isinstance(files_raw, list):
        raise ValueError("manifest files must be a list")
    by_path: dict[str, dict[str, object]] = {}
    for item in files_raw:
        if isinstance(item, dict) and item.get("path"):
            by_path[str(item["path"])] = item
    for path in sorted(p for p in _SAMPLES.rglob("*") if p.is_file()):
        rel = path.relative_to(_SAMPLES).as_posix()
        if rel == "DATASET_MANIFEST.json":
            continue
        if rel in by_path:
            by_path[rel] = _refresh_hash(by_path[rel], path)
            continue
        by_path[rel] = _entry(path)
    merged = dict(existing)
    merged_files = [by_path[key] for key in sorted(by_path)]
    merged["files"] = merged_files
    merged["file_count"] = len(merged_files)
    merged["vendored_count"] = sum(
        1
        for entry in merged_files
        if isinstance(entry, dict) and entry.get("provenance") == "third_party_vendored"
    )
    merged["generated_at"] = datetime.now(tz=UTC).isoformat()
    return merged


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
    parser.add_argument(
        "--merge-missing",
        action="store_true",
        help="Keep existing rows (including CC BY-ND vendored schemas) and add missing files",
    )
    args = parser.parse_args()
    if args.merge_missing and args.out.is_file():
        loaded = json.loads(args.out.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("existing manifest must be a JSON object")
        payload = merge_missing_into(loaded)
    else:
        payload = build_manifest()
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"manifest written: {args.out} ({payload['file_count']} files)")


if __name__ == "__main__":
    main()
