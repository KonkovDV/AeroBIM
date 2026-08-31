"""Check-coverage map: per-source honesty — 'no findings' is NOT 'not checked' (P0).

After Red Team: CHECKED_OK requires EXPLICIT per-source scope + all family capabilities
OK (H1); findings with unknown/None source_id surface in an (unattributed) row (H2);
worst-state aggregation over sibling capabilities (M1); unknown origin counts as
deterministic, never dropped (M2). Map is verdict-neutral.
"""

from __future__ import annotations

import json
import unittest

from aerobim.domain.check_coverage import (
    CheckCoverageMap,
    CoverageStatus,
    build_check_coverage,
)
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    ReportCapabilities,
    Severity,
    ValidationIssue,
)

_IFC = FindingCategory.IFC_VALIDATION
_IDS = FindingCategory.IDS_VALIDATION


def _issue(
    source_id: str | None, category: FindingCategory, *, origin: str | None = "deterministic"
) -> ValidationIssue:
    return ValidationIssue(
        rule_id="R",
        severity=Severity.ERROR,
        message="m",
        category=category,
        source_id=source_id,
        origin=origin,  # type: ignore[arg-type]
    )


def _ids_caps(state: CapabilityState, reason: str | None = None) -> ReportCapabilities:
    return ReportCapabilities(ids=CapabilityStatus(state, reason))


class CheckCoverageTests(unittest.TestCase):
    def test_deterministic_finding_is_checked_findings(self) -> None:
        cov = build_check_coverage(source_ids=["a"], issues=[_issue("a", _IFC)])
        self.assertEqual(cov.rows[0].status_for(_IFC), CoverageStatus.CHECKED_FINDINGS)

    def test_advisory_only_requires_expert(self) -> None:
        cov = build_check_coverage(source_ids=["a"], issues=[_issue("a", _IFC, origin="advisory")])
        self.assertEqual(cov.rows[0].status_for(_IFC), CoverageStatus.REQUIRES_EXPERT)

    def test_checked_ok_requires_capability_ok_and_scope(self) -> None:
        cov = build_check_coverage(
            source_ids=["a"],
            issues=[],
            capabilities=_ids_caps(CapabilityState.OK),
            scope={_IDS: {"a"}},
        )
        self.assertEqual(cov.rows[0].status_for(_IDS), CoverageStatus.CHECKED_OK)

    def test_h1_capability_ok_but_source_not_in_scope_is_not_checked(self) -> None:
        cov = build_check_coverage(
            source_ids=["a"],
            issues=[],
            capabilities=_ids_caps(CapabilityState.OK),
            scope={_IDS: set()},  # source 'a' not in scope
        )
        self.assertEqual(cov.rows[0].status_for(_IDS), CoverageStatus.NOT_CHECKED)

    def test_h1_capability_ok_without_scope_is_not_checked(self) -> None:
        # No scope supplied -> a global OK must NOT become a silent per-source CHECKED_OK.
        cov = build_check_coverage(
            source_ids=["a"], issues=[], capabilities=_ids_caps(CapabilityState.OK)
        )
        self.assertEqual(cov.rows[0].status_for(_IDS), CoverageStatus.NOT_CHECKED)

    def test_anti_silent_pass_not_run_is_not_checked(self) -> None:
        cov = build_check_coverage(
            source_ids=["a"], issues=[], scope={_IDS: {"a"}}
        )  # default ids = SKIPPED
        self.assertEqual(cov.rows[0].status_for(_IDS), CoverageStatus.NOT_CHECKED)

    def test_failed_capability_is_insufficient_data(self) -> None:
        cov = build_check_coverage(
            source_ids=["a"],
            issues=[],
            capabilities=_ids_caps(CapabilityState.FAILED, "boom"),
            scope={_IDS: {"a"}},
        )
        self.assertEqual(cov.rows[0].status_for(_IDS), CoverageStatus.INSUFFICIENT_DATA)

    def test_m1_sibling_capability_not_ok_blocks_checked_ok(self) -> None:
        # IFC family = (ifc_validation, ifc_schema). ifc_validation OK but ifc_schema
        # SKIPPED (default) -> NOT_CHECKED, not a false CHECKED_OK.
        caps = ReportCapabilities(ifc_validation=CapabilityStatus(CapabilityState.OK))
        cov = build_check_coverage(
            source_ids=["a"], issues=[], capabilities=caps, scope={_IFC: {"a"}}
        )
        self.assertEqual(cov.rows[0].status_for(_IFC), CoverageStatus.NOT_CHECKED)

    def test_m1_sibling_failed_is_insufficient_data(self) -> None:
        caps = ReportCapabilities(
            ifc_validation=CapabilityStatus(CapabilityState.OK),
            ifc_schema=CapabilityStatus(CapabilityState.FAILED, "schema boom"),
        )
        cov = build_check_coverage(
            source_ids=["a"], issues=[], capabilities=caps, scope={_IFC: {"a"}}
        )
        self.assertEqual(cov.rows[0].status_for(_IFC), CoverageStatus.INSUFFICIENT_DATA)

    def test_m1_all_family_capabilities_ok_in_scope_is_checked_ok(self) -> None:
        caps = ReportCapabilities(
            ifc_validation=CapabilityStatus(CapabilityState.OK),
            ifc_schema=CapabilityStatus(CapabilityState.OK),
        )
        cov = build_check_coverage(
            source_ids=["a"], issues=[], capabilities=caps, scope={_IFC: {"a"}}
        )
        self.assertEqual(cov.rows[0].status_for(_IFC), CoverageStatus.CHECKED_OK)

    def test_m2_unknown_origin_counts_as_deterministic_not_dropped(self) -> None:
        cov = build_check_coverage(
            source_ids=["a"],
            issues=[_issue("a", _IFC, origin="hybrid")],
            capabilities=ReportCapabilities(
                ifc_validation=CapabilityStatus(CapabilityState.OK),
                ifc_schema=CapabilityStatus(CapabilityState.OK),
            ),
            scope={_IFC: {"a"}},
        )
        # Must NOT fall through to CHECKED_OK — the finding is not dropped.
        self.assertEqual(cov.rows[0].status_for(_IFC), CoverageStatus.CHECKED_FINDINGS)

    def test_h2_unattributed_finding_surfaces_in_its_own_row(self) -> None:
        cov = build_check_coverage(
            source_ids=["a"], issues=[_issue("clash", FindingCategory.SPATIAL)]
        )
        row = next(r for r in cov.rows if r.source_id == "(unattributed)")
        self.assertEqual(row.status_for(FindingCategory.SPATIAL), CoverageStatus.CHECKED_FINDINGS)

    def test_h2_none_source_finding_surfaces_as_unattributed(self) -> None:
        cov = build_check_coverage(
            source_ids=["a"], issues=[_issue(None, FindingCategory.CROSS_DOCUMENT)]
        )
        row = next(r for r in cov.rows if r.source_id == "(unattributed)")
        self.assertEqual(
            row.status_for(FindingCategory.CROSS_DOCUMENT), CoverageStatus.CHECKED_FINDINGS
        )

    def test_verdict_neutral_no_verdict_fields(self) -> None:
        cov = build_check_coverage(source_ids=["a"], issues=[])
        self.assertIsInstance(cov, CheckCoverageMap)
        self.assertFalse(hasattr(cov, "passed"))
        record = cov.to_dict()
        self.assertNotIn("passed", record)
        self.assertNotIn("summary_passed", record)

    def test_to_dict_json_safe_and_dedupes_sources(self) -> None:
        cov = build_check_coverage(source_ids=["a", "a", "b", ""], issues=[_issue("a", _IFC)])
        record = cov.to_dict()
        json.dumps(record)
        source_ids = [s["source_id"] for s in record["sources"]]
        self.assertEqual(source_ids, ["a", "b"])  # deduped + empty dropped, no unattributed

    def test_to_dict_includes_operator_aliases(self) -> None:
        cov = build_check_coverage(
            source_ids=["a"],
            issues=[],
            capabilities=ReportCapabilities(
                ifc_validation=CapabilityStatus(CapabilityState.OK),
                ifc_schema=CapabilityStatus(CapabilityState.OK),
            ),
            scope={_IFC: {"a"}},
        )
        record = cov.to_dict()
        self.assertEqual(record["schema_version"], "1.2.0")
        self.assertIn("operator_legend", record)
        self.assertIn("no_findings", record["operator_legend"])
        self.assertIn("tz_gaps", record)
        self.assertEqual(len(record["tz_gaps"]), 6)
        space = next(row for row in record["tz_gaps"] if row["gap_id"] == "space_efficiency")
        self.assertEqual(space["kt3_scope"], "advisory_unsigned")
        self.assertIn("not delivered", space["jury_speech"])
        row = record["sources"][0]
        self.assertIn("operator_status", row)
        self.assertEqual(row["operator_status"]["ifc-validation"], "no_findings")
        self.assertIn("no_findings", record["operator_summary"])
