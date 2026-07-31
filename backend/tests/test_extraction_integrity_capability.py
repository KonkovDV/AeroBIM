"""EXTRACTION_INTEGRITY capability wiring (P-003, MEP pattern):
default NOT_VERIFIED is verdict-neutral; FAILED can never read as a clean pass.
"""

from __future__ import annotations

from aerobim.application.services.capability_policy import build_signoff_policy
from aerobim.domain.models import CapabilityState, CapabilityStatus, ReportCapabilities


def test_default_is_not_verified_and_non_blocking() -> None:
    caps = ReportCapabilities()
    assert caps.extraction_integrity.status is CapabilityState.NOT_VERIFIED
    policy = build_signoff_policy(profile="development")
    # Default NOT_VERIFIED must not block: wiring lands without flipping verdicts.
    assert policy.summary_passed(error_count=0, capabilities=caps) is True


def test_failed_extraction_integrity_blocks_pass_in_every_profile() -> None:
    caps = ReportCapabilities(
        extraction_integrity=CapabilityStatus(
            CapabilityState.FAILED, "rendered text contradicts extracted text"
        )
    )
    for profile in ("development", "fixture", "samolet_pilot", "production"):
        policy = build_signoff_policy(profile=profile)
        assert policy.summary_passed(error_count=0, capabilities=caps) is False, profile
        assert "extraction_integrity" in policy.failed_capabilities_blocking_pass(caps)


def test_persisted_report_without_field_reconstructs_not_verified() -> None:
    from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore

    reconstruct = FilesystemAuditStore._reconstruct_capabilities
    caps = reconstruct(object.__new__(FilesystemAuditStore), {"clash": {"status": "ok"}})
    assert caps is not None
    assert caps.extraction_integrity.status is CapabilityState.NOT_VERIFIED
