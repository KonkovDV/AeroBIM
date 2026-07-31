"""Release attestation: every evidence artifact it binds must exist and hash."""

from __future__ import annotations

from aerobim.tools.export_release_attestation import build_attestation


def test_attestation_binds_all_evidence_artifacts() -> None:
    payload = build_attestation()
    assert payload["commit"], "git commit sha required"
    assert payload["tree_sha"], "git tree sha required"
    for key in (
        "claims_lock_sha256",
        "dependency_lock_sha256",
        "dev_lock_sha256",
        "sbom_sha256",
        "runtime_baseline_sha256",
        "license_inventory_sha256",
    ):
        value = payload[key]
        assert isinstance(value, str) and len(value) == 64, f"{key} must be a sha256"


def test_attestation_never_fakes_pipeline_fields() -> None:
    payload = build_attestation()
    # docker_digest / test_run_id are release-pipeline facts; a local run must
    # leave them null rather than inventing values.
    assert payload["docker_digest"] is None
    assert payload["test_run_id"] is None
