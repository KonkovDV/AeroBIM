"""Reviewer surfacing of clash triage in HTML export (Wave G, Jul 2026).

Anchor: clash relevance triage (Wave B — Ailem 2026 AutoCon; Koo 2026 ASCE).
Claim boundary: presentation only — band chips never change severity or
``summary.passed``.
"""

from __future__ import annotations

import unittest

from aerobim.presentation.http.report_html import render_report_html


def _payload(issues: list[dict]) -> dict:
    return {
        "summary": {
            "passed": False,
            "issue_count": len(issues),
            "error_count": 0,
            "warning_count": len(issues),
            "requirement_count": 0,
        },
        "issues": issues,
        "project_name": "Wave G",
        "discipline": "MEP",
        "created_at": "2026-07-25T00:00:00+00:00",
    }


def _spatial_issue(band: str, rank: int, priority: int) -> dict:
    return {
        "rule_id": "SPATIAL-HARD-CLASH",
        "severity": "warning",
        "message": f"clash {rank}",
        "category": "spatial",
        "priority": priority,
        "finding_id": f"clash-hard-a{rank}-b{rank}",
        "source_id": "clash",
        "origin": "deterministic",
        "evidence_refs": [
            f"a{rank}",
            f"b{rank}",
            f"triage:band={band}",
            f"triage:rank={rank}",
        ],
    }


class ReportHtmlTriageTests(unittest.TestCase):
    def test_spatial_section_labeled_and_band_chip_rendered(self) -> None:
        html = render_report_html("r" * 32, _payload([_spatial_issue("critical", 1, 40)]))
        self.assertIn("Spatial / Clash Coordination (1)", html)
        self.assertIn("<span class='band band-critical'>critical</span>", html)

    def test_issues_ordered_by_priority_within_section(self) -> None:
        html = render_report_html(
            "r" * 32,
            _payload(
                [
                    _spatial_issue("negligible", 2, 20),
                    _spatial_issue("critical", 1, 40),
                ]
            ),
        )
        self.assertLess(html.index("band-critical"), html.index("band-negligible"))

    def test_unknown_band_value_is_not_rendered_as_chip(self) -> None:
        issue = _spatial_issue("critical", 1, 40)
        issue["evidence_refs"] = ["triage:band=<script>alert(1)</script>"]
        html = render_report_html("r" * 32, _payload([issue]))
        self.assertNotIn("band-<script>", html)
        self.assertNotIn("<script>alert(1)</script>", html)

    def test_non_spatial_issue_without_band_unchanged(self) -> None:
        issue = {
            "rule_id": "IDS-001",
            "severity": "error",
            "message": "missing property",
            "category": "ids-validation",
            "priority": 40,
            "finding_id": "f1",
            "source_id": "ids",
            "evidence_refs": ["guid-1"],
        }
        html = render_report_html("r" * 32, _payload([issue]))
        self.assertNotIn("class='band", html)


if __name__ == "__main__":
    unittest.main()
