"""P0 remediation tests: require_clash, ACL, revision ambiguity, provenance."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.architecture import DocumentIdentity
from aerobim.domain.errors import ClashCapabilityError
from aerobim.domain.finding_provenance import assert_finding_persistable, ensure_finding_provenance
from aerobim.domain.ingestion import detect_revision_merge_conflicts, revisions_conflict
from aerobim.domain.models import (
    ConflictKind,
    FindingCategory,
    GeneratedRemark,
    RequirementSource,
    Severity,
    SourceKind,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.domain.object_acl import AuthPrincipal, principal_may_access_report
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore


def _minimal_uc(*, require_clash: bool, clash_detector) -> AnalyzeProjectPackageUseCase:
    empty = MagicMock()
    empty.extract.return_value = []
    empty.synthesize.return_value = []
    empty.analyze.return_value = []
    empty.validate.return_value = []
    empty.generate.side_effect = lambda issue: GeneratedRemark(
        title=issue.rule_id, body=issue.message
    )
    store = MagicMock()
    store.save.side_effect = lambda report: report.report_id
    store.get.side_effect = lambda report_id: None
    return AnalyzeProjectPackageUseCase(
        requirement_extractor=empty,
        narrative_rule_synthesizer=empty,
        drawing_analyzer=empty,
        ifc_validator=empty,
        remark_generator=empty,
        audit_report_store=store,
        clash_detector=clash_detector,
        require_clash=require_clash,
    )


class RequireClashFailClosedTests(unittest.TestCase):
    def test_require_clash_maps_skipped_to_failed(self) -> None:
        clash = MagicMock()
        clash.detect.side_effect = ClashCapabilityError("skipped", "ifcclash missing")
        uc = _minimal_uc(require_clash=True, clash_detector=clash)
        _results, capability, issues = uc._run_clash_detection(Path("sample.ifc"))
        self.assertEqual(capability.status.value, "failed")
        self.assertEqual(issues[0].severity, Severity.ERROR)

    def test_optional_clash_skipped_remains_skipped(self) -> None:
        clash = MagicMock()
        clash.detect.side_effect = ClashCapabilityError("skipped", "ifcclash missing")
        uc = _minimal_uc(require_clash=False, clash_detector=clash)
        _results, capability, issues = uc._run_clash_detection(Path("sample.ifc"))
        self.assertEqual(capability.status.value, "skipped")
        self.assertEqual(issues[0].severity, Severity.WARNING)


class ObjectAclTests(unittest.TestCase):
    def test_cross_tenant_denied_when_enforced(self) -> None:
        report = ValidationReport(
            report_id="a" * 32,
            request_id="r",
            ifc_path=Path("x.ifc"),
            created_at="2026-07-17T00:00:00+00:00",
            requirements=(),
            issues=(),
            summary=ValidationSummary(0, 0, 0, 0, True),
            tenant_id="tenant-a",
        )
        self.assertTrue(
            principal_may_access_report(
                enforce_object_acl=True,
                principal=AuthPrincipal(tenant_id="tenant-a"),
                report=report,
            )
        )
        self.assertFalse(
            principal_may_access_report(
                enforce_object_acl=True,
                principal=AuthPrincipal(tenant_id="tenant-b"),
                report=report,
            )
        )


class RevisionAmbiguityTests(unittest.TestCase):
    def test_one_sided_revision_is_conflict(self) -> None:
        left = DocumentIdentity(source_id="AR-1", doc_type="drawing", revision="R1")
        right = DocumentIdentity(source_id="AR-1", doc_type="drawing", revision=None)
        self.assertTrue(revisions_conflict(left, right))
        issues = detect_revision_merge_conflicts(
            [
                RequirementSource(
                    text="a",
                    source_kind=SourceKind.STRUCTURED_TEXT,
                    source_id="AR-1",
                    doc_type="drawing",
                    revision="R1",
                ),
                RequirementSource(
                    text="b",
                    source_kind=SourceKind.TECHNICAL_SPECIFICATION,
                    source_id="AR-1",
                    doc_type="drawing",
                    revision=None,
                ),
            ]
        )
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].conflict_kind, ConflictKind.AMBIGUOUS_MAPPING)


class FindingProvenancePersistTests(unittest.TestCase):
    def test_ensure_and_assert_provenance(self) -> None:
        issue = ValidationIssue(
            rule_id="R1",
            severity=Severity.ERROR,
            message="x",
            category=FindingCategory.IFC_VALIDATION,
        )
        stamped = ensure_finding_provenance(issue, revision="R1")
        assert_finding_persistable(stamped)
        self.assertTrue(stamped.finding_id)
        self.assertTrue(stamped.evidence_refs)

    def test_store_rejects_empty_rule_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemAuditStore(Path(tmp))
            bad = ValidationIssue(
                rule_id="",
                severity=Severity.ERROR,
                message="x",
                finding_id="f1",
                source_id="s1",
                evidence_refs=("s1",),
            )
            report = ValidationReport(
                report_id="c" * 32,
                request_id="r",
                ifc_path=Path(tmp) / "x.ifc",
                created_at="2026-07-17T00:00:00+00:00",
                requirements=(),
                issues=(bad,),
                summary=ValidationSummary(0, 1, 1, 0, False),
            )
            with self.assertRaises(ValueError):
                store.save(report)


if __name__ == "__main__":
    unittest.main()
