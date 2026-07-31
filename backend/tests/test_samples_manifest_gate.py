"""Samples dataset manifest gate (P-010/P-013): every file under samples/ must be
listed with a matching sha256; vendored buildingSMART schemas must carry
attribution and must never claim an invented license."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SAMPLES = _REPO_ROOT / "samples"
_MANIFEST = _SAMPLES / "DATASET_MANIFEST.json"


def _manifest() -> dict[str, object]:
    return json.loads(_MANIFEST.read_text(encoding="utf-8"))


def _entries() -> dict[str, dict[str, object]]:
    files = _manifest()["files"]
    assert isinstance(files, list)
    return {str(e["path"]): e for e in files if isinstance(e, dict)}


def _sha256(path: Path) -> str:
    data = path.read_bytes()
    # Match committed LF text on Windows CRLF worktrees (see export_samples_manifest).
    if b"\r\n" in data and b"\x00" not in data[:8192]:
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            pass
        else:
            data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def test_every_samples_file_is_listed_and_hashes_match() -> None:
    entries = _entries()
    on_disk = {
        p.relative_to(_SAMPLES).as_posix(): p
        for p in sorted(_SAMPLES.rglob("*"))
        if p.is_file() and p.name != "DATASET_MANIFEST.json"
    }
    missing = sorted(set(on_disk) - set(entries))
    stale = sorted(set(entries) - set(on_disk) - {"DATASET_MANIFEST.json"})
    assert not missing, f"samples files not in DATASET_MANIFEST.json: {missing[:10]}"
    assert not stale, f"manifest entries without files: {stale[:10]}"
    drift = [rel for rel, path in on_disk.items() if entries[rel]["sha256"] != _sha256(path)]
    assert not drift, (
        "manifest hash drift (regenerate: python -m aerobim.tools.export_samples_manifest): "
        f"{drift[:10]}"
    )


def test_vendored_buildingsmart_schemas_carry_attribution() -> None:
    entries = _entries()
    vendored = [e for e in entries.values() if str(e["provenance"]) == "third_party_vendored"]
    assert len(vendored) >= 9, "expected the 9 vendored BCF/IDS XSD schemas"
    for entry in vendored:
        assert entry["attribution_required"] is True
        assert "buildingSMART" in str(entry["source"])
        # No invented license terms: status stays review_pending until legal review.
        assert entry["license_status"] == "review_pending"


def test_fixtures_never_claim_customer_evidence() -> None:
    for entry in _entries().values():
        if str(entry["provenance"]) == "project_authored_fixture":
            assert "fixture" in str(entry["production_use"])
