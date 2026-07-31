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


def test_pipeline_fields_are_bound_when_provided() -> None:
    # RTV-01: the release pipeline must be able to bind the built image digest
    # and the CI run id (previously hardcoded null even in CI).
    payload = build_attestation(docker_digest="sha256:deadbeef", test_run_id="42-1")
    assert payload["docker_digest"] == "sha256:deadbeef"
    assert payload["test_run_id"] == "42-1"


def test_field_semantics_disambiguates_null() -> None:
    # RTV-02: null must not conflate "file missing" with "pipeline field not run".
    payload = build_attestation()
    semantics = payload["field_semantics"]
    assert isinstance(semantics, dict)
    assert "MISSING" in semantics["evidence_sha256"]
    assert "NOT_RUN" in semantics["docker_digest"]
