"""WP-R2: HTML export groups by layer, prints Russian essence, keeps the machine log."""

from __future__ import annotations

import unittest

from aerobim.presentation.http.report_html import (
    collapse_hitl_with_multiplicity,
    issue_display_text,
    render_report_html,
)


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
        "project_name": "Wave R",
        "discipline": "AR",
        "created_at": "2026-09-09T00:00:00+00:00",
    }


def _pack(**overrides: object) -> dict:
    item: dict[str, object] = {
        "rule_id": "REQ-FIRE-001",
        "severity": "error",
        "message": "Property Pset_WallCommon.FireRating does not match the expected value",
        "category": "ids-validation",
        "priority": 40,
        "finding_id": "fid-pack",
        "source_id": "ids",
        "origin": "deterministic",
        "element_guid": "guid-wall",
        "target_ref": "Wall-01",
        "norm_clause": "5.4.3",
        "evidence_refs": ["guid-wall"],
        "remark": {
            "essence": "Стена не соответствует REI 60",
            "title": "Замечание по модели: Стена не соответствует REI 60 [приоритет 40]",
            "clause_cite": "СП 2.13130 п. 5.4.3",
            "clause_bound": True,
            "location_line": "этаж 3; ось А",
        },
    }
    item.update(overrides)
    return item


def _advisory() -> dict:
    return {
        "rule_id": "AEROBIM-SPACE-EFFICIENCY-CANDIDATE",
        "severity": "info",
        "message": "space candidate",
        "category": "ifc-validation",
        "priority": 5,
        "finding_id": "fid-adv",
        "source_id": "advisory",
        "origin": "advisory",
        "remark": {"essence": "Кандидат по неэффективному пространству", "title": "x"},
    }


def _hitl(sheet: str, finding_id: str) -> dict:
    return {
        "rule_id": "AEROBIM-DRAWING-REGION-HITL",
        "severity": "warning",
        "message": "region needs expert",
        "category": "drawing-validation",
        "priority": 20,
        "finding_id": finding_id,
        "source_id": "drawing",
        "origin": "deterministic",
        "problem_zone": {"sheet_id": sheet},
    }


class ReportHtmlLayerTests(unittest.TestCase):
    def test_pack_findings_exclude_advisory_and_service(self) -> None:
        html = render_report_html("r" * 32, _payload([_pack(), _advisory(), _hitl("A-101", "h1")]))
        pack = html[html.find("id='layer-pack_finding'") : html.find("id='layer-coverage_note'")]
        self.assertIn("Стена не соответствует REI 60", pack)
        self.assertNotIn("AEROBIM-SPACE-EFFICIENCY-CANDIDATE", pack)
        self.assertNotIn("AEROBIM-DRAWING-REGION-HITL", pack)
        self.assertIn("id='layer-advisory_candidate'", html)
        self.assertIn("id='layer-service_record'", html)

    def test_advisory_rendered_in_named_tz_subsections(self) -> None:
        html = render_report_html("r" * 32, _payload([_advisory()]))
        advisory = html[html.find("id='layer-advisory_candidate'") :]
        self.assertIn("Неэффективное использование пространства", advisory)
        self.assertIn("Кандидат по неэффективному пространству", advisory)

    def test_duplicate_hitl_collapse_with_multiplicity(self) -> None:
        issues = [_hitl("A-101", "h1"), _hitl("A-101", "h2"), _hitl("A-101", "h3")]
        html = render_report_html("r" * 32, _payload(issues))
        service = html[html.find("id='layer-service_record'") : html.find("id='finding-gates'")]
        self.assertEqual(service.count("AEROBIM-DRAWING-REGION-HITL"), 1)
        self.assertIn("×3", service)
        self.assertEqual(
            html.count("finding_id=h1") + html.count("finding_id=h2") + html.count("finding_id=h3"),
            4,
        )
        collapsed = collapse_hitl_with_multiplicity(issues)
        self.assertEqual(len(collapsed), 1)
        self.assertEqual(collapsed[0][1], 3)

    def test_row_count_conserved_across_layers_and_appendix(self) -> None:
        issues = [_pack(), _advisory(), _hitl("A-101", "h1"), _hitl("A-101", "h2")]
        html = render_report_html("r" * 32, _payload(issues))
        self.assertIn("всего машинных записей: 4", html)
        self.assertIn("Приложение: полный машинный лог", html)
        self.assertIn("AEROBIM-SPACE-EFFICIENCY-CANDIDATE", html)
        self.assertGreaterEqual(html.count("AEROBIM-DRAWING-REGION-HITL"), 2)

    def test_display_text_prefers_russian_essence(self) -> None:
        self.assertEqual(issue_display_text(_pack()), "Стена не соответствует REI 60")
        html = render_report_html("r" * 32, _payload([_pack()]))
        self.assertIn("Суть замечания", html)
        self.assertIn("Стена не соответствует REI 60", html)

    def test_machine_message_present_in_audit_line(self) -> None:
        html = render_report_html("r" * 32, _payload([_pack()]))
        self.assertIn("machine=Property Pset_WallCommon.FireRating", html)

    def test_header_breakdown_lists_every_layer(self) -> None:
        html = render_report_html("r" * 32, _payload([_pack(), _advisory(), _hitl("A-101", "h1")]))
        header = html[html.find("id='layer-breakdown'") : html.find("id='layer-pack_finding'")]
        self.assertIn("замечаний к комплекту", header)
        self.assertIn("проверок без объектов", header)
        self.assertIn("служебных записей", html)
        self.assertIn("кандидатов", html)
        self.assertIn("всего машинных записей: 3", html)

    def test_html_contains_executive_brief(self) -> None:
        html = render_report_html("r" * 32, _payload([_pack(), _advisory()]))
        self.assertIn("id='executive-brief'", html)
        self.assertIn("hides_negative=false", html)
        self.assertLess(html.find("id='executive-brief'"), html.find("summary.passed"))

    def test_summary_block_unchanged(self) -> None:
        html = render_report_html("r" * 32, _payload([_pack()]))
        self.assertIn("summary.passed=false", html)
        self.assertIn("1 issue(s):", html)
        self.assertIn("FAILED", html)

    def test_default_lang_is_ru(self) -> None:
        html = render_report_html("r" * 32, _payload([_pack()]))
        self.assertIn('<html lang="ru">', html)
        html_en = render_report_html("r" * 32, _payload([_pack()]), locale="en")
        self.assertIn('<html lang="en">', html_en)
        self.assertIn("Pack findings", html_en)


if __name__ == "__main__":
    unittest.main()
