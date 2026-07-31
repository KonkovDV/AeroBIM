"""Offline bundle manifest logic (docker-free unit tests): hashing and verify
must catch missing files and content drift; docker integration runs manually
(evidence: audit/evidence/offline-bundle-smoke-2026-07-31.json)."""

from __future__ import annotations

import json
from pathlib import Path

from aerobim.tools.offline_bundle import _BUNDLE_FILES, build_manifest, verify_manifest


def _make_bundle(tmp_path: Path) -> Path:
    for name in _BUNDLE_FILES:
        (tmp_path / name).write_bytes(f"content-of-{name}".encode())
    manifest = build_manifest(tmp_path, image_id="sha256:test")
    (tmp_path / "BUNDLE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp_path


def test_intact_bundle_verifies_clean(tmp_path: Path) -> None:
    bundle = _make_bundle(tmp_path)
    assert verify_manifest(bundle) == []


def test_tampered_file_is_detected(tmp_path: Path) -> None:
    bundle = _make_bundle(tmp_path)
    (bundle / "requirements-lock.txt").write_bytes(b"tampered")
    problems = verify_manifest(bundle)
    assert any("sha256 mismatch: requirements-lock.txt" in p for p in problems)


def test_missing_file_is_detected(tmp_path: Path) -> None:
    bundle = _make_bundle(tmp_path)
    (bundle / "Dockerfile").unlink()
    problems = verify_manifest(bundle)
    assert any("missing: Dockerfile" in p for p in problems)


def test_manifest_declares_honest_scope(tmp_path: Path) -> None:
    manifest = build_manifest(_make_bundle(tmp_path), image_id="sha256:test")
    assert manifest["claim_level"] == "image_bundle_only"
    assert "NOT VERIFIED" in str(manifest["scope_honesty"])
