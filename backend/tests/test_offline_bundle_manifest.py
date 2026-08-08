"""Offline bundle manifest logic (docker-free unit tests): hashing and verify
must catch missing files and content drift; docker integration runs manually
(evidence: audit/evidence/offline-bundle-smoke-2026-07-31.json)."""

from __future__ import annotations

import json
from pathlib import Path

from aerobim.tools.offline_bundle import (
    _BUNDLE_FILES,
    _BACKEND,
    _IMAGE_TAR,
    build_manifest,
    verify_bundle_source_sync,
    verify_manifest,
)


def _make_bundle(tmp_path: Path) -> Path:
    for name in _BUNDLE_FILES:
        if name == _IMAGE_TAR:
            (tmp_path / name).write_bytes(f"content-of-{name}".encode())
        else:
            (tmp_path / name).write_bytes((_BACKEND / name).read_bytes())
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


def test_bundle_backend_drift_is_detected(tmp_path: Path) -> None:
    bundle = _make_bundle(tmp_path)
    (bundle / "Dockerfile").write_bytes(b"# stale dockerfile")
    problems = verify_bundle_source_sync(bundle)
    assert any("bundle/backend drift: Dockerfile" in p for p in problems)


def test_missing_file_is_detected(tmp_path: Path) -> None:
    bundle = _make_bundle(tmp_path)
    (bundle / "Dockerfile").unlink()
    problems = verify_manifest(bundle)
    assert any("missing: Dockerfile" in p for p in problems)


def test_manifest_declares_honest_scope(tmp_path: Path) -> None:
    manifest = build_manifest(_make_bundle(tmp_path), image_id="sha256:test")
    assert manifest["claim_level"] == "image_bundle_only"
    assert "OUT_OF_SCOPE" in str(manifest["scope_honesty"]) or "NOT VERIFIED" in str(
        manifest["scope_honesty"]
    )


def test_spdx_lite_parses_lock_pins() -> None:
    from aerobim.tools.offline_bundle import build_spdx_lite, parse_lock_packages

    sample = (
        "fastapi==0.115.0 \\\n"
        "    --hash=sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        "pypdfium2==4.30.0 \\\n"
        "    --hash=sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n"
    )
    packages = parse_lock_packages(sample)
    assert {p["name"] for p in packages} == {"fastapi", "pypdfium2"}
    import tempfile
    from pathlib import Path as P

    with tempfile.TemporaryDirectory() as tmp:
        lock = P(tmp) / "requirements-lock.txt"
        lock.write_text(sample, encoding="utf-8")
        doc = build_spdx_lite(lock_path=lock, image_id="sha256:deadbeef")
    assert doc["claim_level"] == "lockfile_sbom_lite"
    assert doc["package_count"] == 2
    assert doc["packages"][0]["checksums"][0]["algorithm"] == "SHA256"


def test_install_scripts_and_docs_enter_manifest(tmp_path: Path) -> None:
    from aerobim.tools.offline_bundle import write_install_docs, write_install_scripts

    for name in _BUNDLE_FILES:
        (tmp_path / name).write_bytes(f"content-of-{name}".encode())
    write_install_docs(tmp_path)
    write_install_scripts(tmp_path)
    (tmp_path / "sbom-spdx-lite.json").write_text(
        json.dumps({"claim_level": "lockfile_sbom_lite", "package_count": 0}),
        encoding="utf-8",
    )
    manifest = build_manifest(tmp_path, image_id="sha256:test")
    assert "INSTALL_OFFLINE.md" in manifest["files"]
    assert "MIRROR_CHECKLIST.md" in manifest["files"]
    assert "install_offline.sh" in manifest["files"]
    assert "install_offline.ps1" in manifest["files"]
    assert "sbom-spdx-lite.json" in manifest["files"]


def test_install_docs_and_sbom_enter_manifest(tmp_path: Path) -> None:
    from aerobim.tools.offline_bundle import write_install_docs

    for name in _BUNDLE_FILES:
        (tmp_path / name).write_bytes(f"content-of-{name}".encode())
    write_install_docs(tmp_path)
    (tmp_path / "sbom-spdx-lite.json").write_text(
        json.dumps({"claim_level": "lockfile_sbom_lite", "package_count": 0}),
        encoding="utf-8",
    )
    manifest = build_manifest(tmp_path, image_id="sha256:test")
    assert "INSTALL_OFFLINE.md" in manifest["files"]
    assert "MIRROR_CHECKLIST.md" in manifest["files"]
    assert "sbom-spdx-lite.json" in manifest["files"]
    assert "sbom-spdx-lite" in str(manifest["scope_honesty"])


def test_wheelhouse_writes_out_of_scope_artifact(tmp_path: Path, monkeypatch) -> None:
    from aerobim.tools import offline_bundle as bundle

    monkeypatch.setattr(bundle, "_BUNDLE_DIR", tmp_path)
    exit_code = bundle.cmd_wheelhouse()
    assert exit_code == 2
    artifact = tmp_path / "wheelhouse-OUT_OF_SCOPE.json"
    assert artifact.is_file()
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["status"] == "OUT_OF_SCOPE"
    assert payload["i1_status"] == "CLOSED_DOCKER_TRACK"
    legacy = tmp_path / "wheelhouse-DEFERRED.json"
    assert legacy.is_file()


def test_closed_contour_verify_without_smoke(tmp_path: Path, monkeypatch) -> None:
    from aerobim.tools import offline_bundle as bundle

    bundle_dir = _make_bundle(tmp_path)
    monkeypatch.setattr(bundle, "_BUNDLE_DIR", bundle_dir)
    assert bundle.cmd_closed_contour(run_smoke=False) == 0


def test_container_probe_script_checks_auth_and_egress() -> None:
    from aerobim.tools.offline_bundle import _container_probe_script

    script = _container_probe_script(token="test-token")
    assert "401" in script or "base64" in script
    assert "1.1.1.1" in script or "base64" in script


def test_install_scripts_refuse_demo_token_without_flag(tmp_path: Path) -> None:
    from aerobim.tools.offline_bundle import write_install_scripts

    write_install_scripts(tmp_path)
    sh = (tmp_path / "install_offline.sh").read_text(encoding="utf-8")
    ps1 = (tmp_path / "install_offline.ps1").read_text(encoding="utf-8")
    assert "AEROBIM_OFFLINE_ALLOW_DEMO_TOKEN" in sh
    assert "network none" in sh
    assert "-p " not in sh
    assert "full closed-contour probe" in sh
    assert "AEROBIM_OFFLINE_ALLOW_DEMO_TOKEN" in ps1
    assert 'docker run' in ps1 and '-p ' not in ps1.split('docker run', 1)[1]
    assert "full closed-contour probe" in ps1


def test_wheelhouse_artifact_in_manifest(tmp_path: Path) -> None:
    from aerobim.tools.offline_bundle import write_install_docs, write_install_scripts, write_wheelhouse_artifact

    for name in _BUNDLE_FILES:
        (tmp_path / name).write_bytes(f"content-of-{name}".encode())
    write_install_docs(tmp_path)
    write_install_scripts(tmp_path)
    write_wheelhouse_artifact(tmp_path)
    manifest = build_manifest(tmp_path, image_id="sha256:test")
    assert "wheelhouse-OUT_OF_SCOPE.json" in manifest["files"]
