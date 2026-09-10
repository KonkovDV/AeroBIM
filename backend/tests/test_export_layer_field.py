"""WP-R4: ``layer`` is a serialization derivative; stored integrity is unchanged."""

from __future__ import annotations

import copy
import unittest
from datetime import UTC, datetime
from pathlib import Path

from aerobim.core.di.container import Container
from aerobim.domain.finding_provenance import ensure_finding_provenance
from aerobim.domain.models import (
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.presentation.http.context import ApiContext


class ExportLayerFieldTests(unittest.TestCase):
    def test_every_issue_has_layer(self) -> None:
        issue = ensure_finding_provenance(
            ValidationIssue(
                rule_id="REQ-FIRE-001",
                severity=Severity.ERROR,
                message="Property Pset_WallCommon.FireRating does not match the expected value",
                category=FindingCategory.IDS_VALIDATION,
                element_guid="guid-1",
                target_ref="Wall-01",
            )
        )
        report = ValidationReport(
            report_id="a" * 32,
            request_id="layer",
            ifc_path=Path("m.ifc"),
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=(),
            issues=(issue,),
            summary=ValidationSummary(0, 1, 1, 0, False),
        )
        ctx = object.__new__(ApiContext)
        ctx.container = Container()
        payload = ctx.serialize_public_report(report)
        self.assertTrue(all("layer" in item for item in payload["issues"]))
        self.assertEqual(payload["issues"][0]["layer"], "pack_finding")

    def test_finding_volume_block_is_not_accuracy(self) -> None:
        issue = ensure_finding_provenance(
            ValidationIssue(
                rule_id="AEROBIM-CLASH-CAPABILITY",
                severity=Severity.INFO,
                message="cap",
                category=FindingCategory.IFC_VALIDATION,
            )
        )
        report = ValidationReport(
            report_id="b" * 32,
            request_id="vol",
            ifc_path=Path("m.ifc"),
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=(),
            issues=(issue,),
            summary=ValidationSummary(0, 1, 0, 0, True),
        )
        ctx = object.__new__(ApiContext)
        ctx.container = Container()
        payload = ctx.serialize_public_report(report)
        volume = payload["finding_volume"]
        self.assertFalse(volume["is_accuracy"])
        self.assertEqual(volume["publishable_finding_count"], 0)
        self.assertIn("claim_boundary", volume)
        self.assertFalse(payload["remark_completeness"]["is_accuracy"])

    def test_stored_report_integrity_hash_unchanged(self) -> None:
        issue = ensure_finding_provenance(
            ValidationIssue(
                rule_id="REQ-FIRE-001",
                severity=Severity.ERROR,
                message="mismatch",
                category=FindingCategory.IDS_VALIDATION,
                element_guid="guid-1",
            )
        )
        report = ValidationReport(
            report_id="c" * 32,
            request_id="hash",
            ifc_path=Path("m.ifc"),
            created_at="2026-09-09T00:00:00+00:00",
            requirements=(),
            issues=(issue,),
            summary=ValidationSummary(0, 1, 1, 0, False),
        )
        before = copy.deepcopy(report.issues)
        ctx = object.__new__(ApiContext)
        ctx.container = Container()
        ctx.serialize_public_report(report)
        self.assertEqual(report.issues, before)
        self.assertFalse(hasattr(report.issues[0], "layer"))


if __name__ == "__main__":
    unittest.main()
