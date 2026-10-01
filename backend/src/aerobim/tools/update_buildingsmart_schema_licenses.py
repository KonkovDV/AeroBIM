"""Update DATASET_MANIFEST buildingSMART schema licenses (RT-W-01)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SAMPLES = ROOT / "samples"
MANIFEST = SAMPLES / "DATASET_MANIFEST.json"

REDISTRIBUTION = "allowed under CC BY-ND 4.0 with attribution; no derivatives"
LICENSE_URL = "https://creativecommons.org/licenses/by-nd/4.0/"
NOTE = (
    "RT-W-01: upstream BCF-XML and IDS LICENSE files are CC BY-ND 4.0 "
    "(buildingSMART International Ltd.)"
)


def _sha(path: Path) -> tuple[str, int]:
    """Match export_samples_manifest: hash LF-normalized text on Windows CRLF trees."""
    data = path.read_bytes()
    size = len(data)
    if b"\r\n" in data and b"\x00" not in data[:8192]:
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            pass
        else:
            data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest(), size


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    updated = 0
    for entry in manifest["files"]:
        if entry.get("license_status") != "review_pending":
            continue
        path = SAMPLES / entry["path"]
        digest, size = _sha(path)
        entry["sha256"] = digest
        entry["bytes"] = size
        entry["license_status"] = "cc_by_nd_4.0"
        entry["attribution_required"] = True
        entry["redistribution"] = REDISTRIBUTION
        entry["license_url"] = LICENSE_URL
        if entry["path"].startswith("bcf-xsd"):
            entry["upstream_license_url"] = (
                "https://github.com/buildingSMART/BCF-XML/blob/release_3_0/LICENSE"
            )
        else:
            entry["upstream_license_url"] = (
                "https://github.com/buildingSMART/IDS/blob/development/LICENSE"
            )
        entry["verified_at"] = "2026-08-04"
        entry["verification_note"] = NOTE
        updated += 1

    existing = {entry["path"] for entry in manifest["files"]}
    for rel in (
        "bcf-xsd/LICENSE_CC_BY_ND_4.0.txt",
        "bcf-xsd/NOTICE",
        "ids-xsd/LICENSE_CC_BY_ND_4.0.txt",
        "ids-xsd/NOTICE",
    ):
        if rel in existing:
            continue
        digest, size = _sha(SAMPLES / rel)
        manifest["files"].append(
            {
                "path": rel,
                "sha256": digest,
                "bytes": size,
                "provenance": "third_party_vendored",
                "source": "buildingSMART International (BCF/IDS license notice)",
                "license_status": "cc_by_nd_4.0",
                "attribution_required": True,
                "redistribution": REDISTRIBUTION,
                "license_url": LICENSE_URL,
                "production_use": "attribution / license notice",
                "personal_data": False,
                "verified_at": "2026-08-04",
                "verification_note": NOTE,
            }
        )

    manifest["note"] = (
        "license/provenance map of the public fixture corpus; fixtures are synthetic "
        "and never customer evidence (corpus_kind=fixture); vendored buildingSMART "
        "BCF/IDS schemas are CC BY-ND 4.0 (verified 2026-08-04 RT-W-01) with NOTICE "
        "+ LICENSE files"
    )
    manifest["generated_at"] = datetime.now(tz=UTC).isoformat()
    manifest["file_count"] = len(manifest["files"])
    manifest["vendored_count"] = sum(
        1 for entry in manifest["files"] if entry.get("provenance") == "third_party_vendored"
    )
    pending = sum(
        1 for entry in manifest["files"] if entry.get("license_status") == "review_pending"
    )
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"updated={updated} pending_left={pending} files={manifest['file_count']}")


if __name__ == "__main__":
    main()
