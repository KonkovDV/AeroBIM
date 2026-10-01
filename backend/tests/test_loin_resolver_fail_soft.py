"""LOIN resolver fail-soft (offline-smoke finding): a missing manifest degrades
to no-metadata with a visible flag and must never raise at construction."""

from __future__ import annotations

from pathlib import Path

from aerobim.application.services.loin_metadata_resolver import LoinMetadataResolver


def test_missing_manifest_degrades_instead_of_crashing(tmp_path: Path) -> None:
    resolver = LoinMetadataResolver(manifest_path=tmp_path / "absent.json")
    assert resolver.available is False
    assert resolver.degrade_reason is not None
    assert resolver.resolve("REQ-FIRE-001") is None


def test_corrupt_manifest_degrades_instead_of_crashing(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    resolver = LoinMetadataResolver(manifest_path=bad)
    assert resolver.available is False
    assert resolver.resolve("ANY") is None


def test_repo_manifest_still_loads_positive_control() -> None:
    resolver = LoinMetadataResolver()
    assert resolver.available is True
    assert resolver.degrade_reason is None
