"""P0-G wiring: EvidenceRecord generation from ValidationIssue.

These tests verify that `build_evidence_records` correctly bridges the old
`ValidationIssue` (stamped by `ensure_finding_provenance`) to the new
`EvidenceRecord` / `FindingProvenance` domain types introduced in PR #98.

All tests are pure-unit: no I/O, no external services.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aerobim.application.services.evidence_provenance_enricher import build_evidence_records
from aerobim.domain.evidence_provenance import ExtractionMethod
from aerobim.domain.finding_provenance import ensure_finding_provenance
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue, ValidationRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(
    *,
    tenant_id: str = "tenant-a",
    project_id: str = "proj-1",
    revision: str = "P1",
) -> ValidationRequest:
    return ValidationRequest(
        request_id="req-test-001",
        tenant_id=tenant_id,
        project_id=project_id,
        revision=revision,
    )


def _make_stamped_issue(
    rule_id: str = "IFC-001",
    origin: str = "deterministic",
    category: FindingCategory = FindingCategory.IFC_VALIDATION,
) -> ValidationIssue:
    raw = ValidationIssue(
        rule_id=rule_id,
        severity=Severity.ERROR,
        message="Test issue",
        category=category,
        source_id=f"src-{rule_id}",
        element_guid="3HHdKv9Q1AF8tqlA4eQGt9",
        origin=origin,
    )
    return ensure_finding_provenance(
        raw,
        tenant_id="tenant-a",
        project_id="proj-1",
        revision="P1",
        origin=origin,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBuildEvidenceRecords:
    def test_produces_one_record_per_stamped_issue(self) -> None:
        issues = [_make_stamped_issue("IFC-001"), _make_stamped_issue("IFC-002")]
        request = _make_request()

        records, provenances, summary = build_evidence_records(
            issues, request, signoff_profile="development", priority_profile="default"
        )

        assert len(records) == 2
        assert len(provenances) == 2
        assert summary["records_built"] == 2
        assert summary["skipped_no_finding_id"] == 0

    def test_skips_issue_without_finding_id(self) -> None:
        # Un-stamped issue: no finding_id
        raw = ValidationIssue(
            rule_id="IFC-003",
            severity=Severity.WARNING,
            message="Not stamped",
        )
        request = _make_request()

        records, provenances, summary = build_evidence_records(
            [raw], request
        )

        assert len(records) == 0
        assert summary["skipped_no_finding_id"] == 1

    def test_provenance_id_stable_across_two_calls(self) -> None:
        """Same inputs must yield the same provenance_id (determinism gate)."""
        issue = _make_stamped_issue("CLASH-001")
        request = _make_request()

        records_a, _, _ = build_evidence_records([issue], request)
        records_b, _, _ = build_evidence_records([issue], request)

        assert records_a[0].provenance_id == records_b[0].provenance_id

    def test_ai_origin_gets_ai_advisory_method(self) -> None:
        issue = _make_stamped_issue("ADV-001", origin="advisory")
        request = _make_request()

        records, _, _ = build_evidence_records([issue], request)

        assert records[0].extraction_method == ExtractionMethod.AI_ADVISORY
        assert records[0].is_ai_advisory is True

    def test_deterministic_origin_gets_parser_method(self) -> None:
        issue = _make_stamped_issue("IDS-001", origin="deterministic")
        request = _make_request()

        records, _, _ = build_evidence_records([issue], request)

        assert records[0].extraction_method in (
            ExtractionMethod.DETERMINISTIC_PARSER,
            ExtractionMethod.IDS_VALIDATOR,
            ExtractionMethod.DETERMINISTIC_GEOMETRY,
        )
        assert records[0].is_ai_advisory is False

    def test_package_id_derived_from_manifest_when_tenant_present(self) -> None:
        issue = _make_stamped_issue("IFC-010")
        request = _make_request(tenant_id="tenant-x", project_id="proj-y", revision="R3")

        records, _, summary = build_evidence_records([issue], request)

        assert len(summary["package_id"]) == 40  # sha256[:40]
        assert records[0].package_id == summary["package_id"]

    def test_package_id_fallback_when_no_tenant(self) -> None:
        issue = _make_stamped_issue("IFC-011")
        request = _make_request(tenant_id="", project_id="")

        records, _, summary = build_evidence_records([issue], request)

        # Falls back to sha256(request_id)
        assert len(summary["package_id"]) == 40

    def test_finding_provenance_is_reproducible(self) -> None:
        issue = _make_stamped_issue("KR-001")
        request = _make_request()

        _, provenances, _ = build_evidence_records([issue], request)

        prov = provenances[0]
        assert prov.is_reproducible
        assert prov.finding_id == issue.finding_id
        assert prov.rule_id == "KR-001"
        assert prov.tenant_id == "tenant-a"
        assert prov.project_id == "proj-1"

    def test_summary_has_expected_keys(self) -> None:
        issue = _make_stamped_issue("IFC-100")
        request = _make_request()

        _, _, summary = build_evidence_records([issue], request)

        required_keys = {
            "tool",
            "status",
            "package_id",
            "engine_version",
            "configuration_hash",
            "norm_pack_id",
            "norm_pack_hash",
            "issues_total",
            "records_built",
            "skipped_no_finding_id",
            "verdict_impact",
        }
        assert required_keys.issubset(summary.keys())
        assert summary["verdict_impact"] == "none"

    def test_summary_status_ok_on_clean_run(self) -> None:
        issue = _make_stamped_issue("IFC-200")
        request = _make_request()

        _, _, summary = build_evidence_records([issue], request)

        assert summary["status"] == "ok"
        assert summary["errors"] == []

    def test_mixed_stamped_and_unstamped_issues(self) -> None:
        stamped = _make_stamped_issue("IFC-300")
        raw = ValidationIssue(
            rule_id="RAW-001",
            severity=Severity.INFO,
            message="Raw, no provenance stamp",
        )
        request = _make_request()

        records, _, summary = build_evidence_records([stamped, raw], request)

        assert len(records) == 1
        assert summary["records_built"] == 1
        assert summary["skipped_no_finding_id"] == 1
        assert summary["issues_total"] == 2

    def test_evidence_record_provenance_id_format(self) -> None:
        """provenance_id must be a 24-char hex string."""
        issue = _make_stamped_issue("IFC-400")
        request = _make_request()

        records, _, _ = build_evidence_records([issue], request)

        pid = records[0].provenance_id
        assert len(pid) == 24
        assert all(c in "0123456789abcdef" for c in pid)
