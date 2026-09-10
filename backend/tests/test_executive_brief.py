"""Executive brief: two-layer export, negatives stay visible, not accuracy."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime
from pathlib import Path

from test_report_pdf_coverage import extract_pdf_text

from aerobim.core.di.container import Container
from aerobim.domain.executive_brief import executive_brief
from aerobim.domain.finding_provenance import ensure_finding_provenance
from aerobim.domain.models import (
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.presentation.http.context import ApiContext
from aerobim.presentation.http.report_html import render_report_html
from aerobim.presentation.http.report_pdf import render_report_pdf_bytes


def _pack() -> dict:
    return {
        "rule_id": "REQ-FIRE-001",
        "severity": "error",
        "message": "Property Pset_WallCommon.FireRating does not match the expected value",
        "category": "ids-validation",
        "finding_id": "fid-pack",
        "element_guid": "guid-wall",
        "target_ref": "Wall-01",
        "norm_clause": "5.4.3",
        "evidence_refs": ["guid-wall"],
        "remark": {
            "essence": "Стена не соответствует REI 60",
            "clause_cite": "СП 2.13130 п. 5.4.3",
            "clause_bound": True,
            "location_line": "этаж 3",
        },
    }


def _advisory() -> dict:
    return {
        "rule_id": "AEROBIM-SPACE-EFFICIENCY-CANDIDATE",
        "severity": "info",
        "message": "space candidate",
        "origin": "advisory",
        "finding_id": "fid-adv",
        "remark": {"essence": "Кандидат"},
    }


class ExecutiveBriefTests(unittest.TestCase):
    def test_advisory_is_not_a_pack_finding(self) -> None:
        brief = executive_brief(
            {
                "issues": [_pack(), _advisory()],
                "capabilities": {
                    "mep_system_clash": {"status": "not_verified"},
                    "dwg_dxf": {"status": "missing"},
                    "calculation_correctness": {"status": "not_implemented"},
                },
                "coverage": {
                    "tz_gaps": [{"label": "MEP", "status": "not_checked", "reason": "no IFC"}]
                },
            }
        )
        self.assertEqual(brief["pack_findings"], 1)
        self.assertEqual(brief["advisory_candidates"], 1)
        self.assertEqual(brief["machine_records"], 2)
        self.assertFalse(brief["is_accuracy"])
        self.assertFalse(brief["is_sla"])
        self.assertFalse(brief["hides_negative"])
        self.assertEqual(brief["review_mode"], "single_expert_pilot_review")
        self.assertEqual(brief["mep_system_clash"], "not_verified")
        self.assertEqual(brief["coverage_not_checked"], 1)
        self.assertIn("not_verified", {row["status"] for row in brief["negative_capabilities"]})

    def test_rejected_counts_separately(self) -> None:
        rejected = dict(_pack())
        rejected["finding_id"] = "fid-rej"
        rejected["review"] = {"state": "rejected"}
        brief = executive_brief({"issues": [_pack(), rejected]})
        self.assertEqual(brief["pack_findings"], 1)
        self.assertEqual(brief["rejected"], 1)
        self.assertEqual(brief["unresolved_review"], 1)

    def test_html_brief_shows_negatives(self) -> None:
        html = render_report_html(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 2,
                    "error_count": 1,
                    "warning_count": 0,
                    "requirement_count": 0,
                },
                "issues": [_pack(), _advisory()],
                "capabilities": {"mep_system_clash": {"status": "not_verified"}},
            },
        )
        self.assertIn("id='executive-brief'", html)
        brief = html[html.find("id='executive-brief'") : html.find('class="summary')]
        self.assertIn("not_verified", brief)
        self.assertIn("кандидаты", brief)
        self.assertIn("single_expert_pilot_review", brief)
        self.assertIn("hides_negative=false", brief)

    def test_pdf_brief_precedes_coverage(self) -> None:
        text = extract_pdf_text(
            render_report_pdf_bytes(
                "r-pdf",
                {
                    "summary": {
                        "passed": False,
                        "issue_count": 1,
                        "error_count": 1,
                        "warning_count": 0,
                    },
                    "issues": [_pack()],
                    "coverage": {},
                },
            )
        )
        self.assertLess(text.find("КРАТКАЯ ВЫЖИМКА"), text.find("CHECK COVERAGE MAP"))
        self.assertLess(text.find("CHECK COVERAGE MAP"), text.find("Замечания к комплекту"))

    def test_serialize_adds_brief_without_storing_on_issue(self) -> None:
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
            report_id="b" * 32,
            request_id="brief",
            ifc_path=Path("m.ifc"),
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=(),
            issues=(issue,),
            summary=ValidationSummary(0, 1, 1, 0, False),
        )
        ctx = object.__new__(ApiContext)
        ctx.container = Container()
        payload = ctx.serialize_public_report(report)
        self.assertIn("executive_brief", payload)
        self.assertFalse(payload["executive_brief"]["is_accuracy"])
        self.assertFalse(hasattr(report.issues[0], "executive_brief"))


if __name__ == "__main__":
    unittest.main()
