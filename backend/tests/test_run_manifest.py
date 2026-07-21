"""Run manifest and reproducibility hash tests."""

from __future__ import annotations

import unittest

from aerobim.domain.models import Severity, ValidationIssue
from aerobim.domain.package_outcome import PackageOutcome
from aerobim.domain.run_manifest import (
    build_run_manifest,
    compute_reproducibility_hash,
    engine_signature,
)


class _Summary:
    def __init__(self, *, passed: bool, outcome: PackageOutcome) -> None:
        self.passed = passed
        self.outcome = outcome


class _CapsField:
    def __init__(self, status) -> None:  # noqa: ANN001
        self.status = status


class _Caps:
    def __init__(self) -> None:
        from aerobim.domain.models import CapabilityState

        self.clash = _CapsField(CapabilityState.OK)
        self.ids = _CapsField(CapabilityState.OK)
        self.ifc_validation = _CapsField(CapabilityState.OK)
        self.mep_system_clash = _CapsField(CapabilityState.NOT_VERIFIED)


class _Report:
    def __init__(self, issues) -> None:  # noqa: ANN001
        self.summary = _Summary(passed=False, outcome=PackageOutcome.BLOCKED)
        self.issues = issues
        self.capabilities = _Caps()


class RunManifestTests(unittest.TestCase):
    def test_engine_signature_excludes_advisory_agent(self) -> None:
        from aerobim.domain.models import FindingCategory

        report = _Report(
            [
                ValidationIssue(
                    rule_id="RULE-1",
                    severity=Severity.ERROR,
                    category=FindingCategory.IFC_VALIDATION,
                    message="bad",
                ),
                ValidationIssue(
                    rule_id="AGENT-HINT",
                    severity=Severity.INFO,
                    category=FindingCategory.DRAWING_VALIDATION,
                    message="hint",
                    source_id="compliance-agent",
                ),
            ]
        )
        sig = engine_signature(report)
        self.assertEqual(len(sig), 1)
        self.assertEqual(sig[0][0], "RULE-1")

    def test_reproducibility_hash_stable_for_same_inputs(self) -> None:
        engine = (("RULE-1", "error", "ifc-property", "", "bad"),)
        caps = {"mep_system_clash": "not_verified"}
        first = compute_reproducibility_hash(
            passed=False,
            outcome=PackageOutcome.BLOCKED,
            engine=engine,
            capabilities=caps,
            package_sha256="abc",
        )
        second = compute_reproducibility_hash(
            passed=False,
            outcome="blocked",
            engine=engine,
            capabilities=caps,
            package_sha256="abc",
        )
        self.assertEqual(first, second)

    def test_build_run_manifest_includes_stage_budget(self) -> None:
        from aerobim.domain.models import FindingCategory

        report = _Report(
            [
                ValidationIssue(
                    rule_id="RULE-1",
                    severity=Severity.WARNING,
                    category=FindingCategory.IFC_VALIDATION,
                    message="warn",
                )
            ]
        )
        manifest = build_run_manifest(report, request_id="req-1", pack_id="pack-1")
        self.assertEqual(manifest.schema_version, "1.0.0")
        self.assertEqual(manifest.request_id, "req-1")
        self.assertEqual(manifest.stage_budget["total_minutes"], 30.0)
        self.assertIn("ingestion", manifest.contours[0])


if __name__ == "__main__":
    unittest.main()
