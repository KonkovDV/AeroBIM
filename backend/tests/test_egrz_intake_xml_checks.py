"""Honesty lock: MinStroy XML intake is not RT-001 CLOSED."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.domain.egrz_intake_xml_checks import (
    RULE_MISSING,
    RULE_PARSER,
    RULE_ROOT,
    RULE_STALE,
    RULE_WELLFORMED,
    RULE_XSD,
    collect_egrz_xml_validate_issues,
    egrz_intake_catalog_snapshot,
    minstroy_xml_schema_catalog,
    schema_by_kind,
    strip_documentation_xml_ids,
)
from aerobim.domain.npa_legal_force import (
    EGRZ_INTAKE_LEGAL,
    FORCE_AGENCY_ORDER,
    FORCE_NOT_NPA,
    overlay_egrz_intake,
)
from aerobim.domain.tz_proxy_constructs import egrz_intake_xml_proxy

REPO = Path(__file__).resolve().parents[2]
XSD_DIR = REPO / "samples" / "xsd" / "minstroy"
FIXTURES = XSD_DIR / "fixtures"


class CatalogHonestyTests(unittest.TestCase):
    def test_catalog_uses_ecpe_in_force_versions(self) -> None:
        by_kind = {row["kind"]: row for row in minstroy_xml_schema_catalog()}
        self.assertEqual(by_kind["explanatory_note"]["listed_version"], "01.07")
        self.assertEqual(by_kind["explanatory_note"]["ecpe_in_force_version"], "01.07")
        self.assertFalse(by_kind["explanatory_note"]["stale_vs_ecpe"])
        self.assertFalse(by_kind["explanatory_note"]["loadable_xmlschema11"])
        self.assertTrue(by_kind["explanatory_note"]["loadable_xmlschema11_after_doc_id_sanitize"])
        self.assertIn("dev_", str(by_kind["explanatory_note"]["zip_member"]))
        self.assertEqual(by_kind["design_assignment"]["listed_version"], "01.01")
        self.assertEqual(by_kind["design_assignment"]["ecpe_in_force_version"], "01.01")
        self.assertFalse(by_kind["design_assignment"]["stale_vs_ecpe"])
        self.assertFalse(by_kind["conclusion"]["stale_vs_ecpe"])
        self.assertTrue(by_kind["conclusion"]["loadable_xmlschema11"])
        self.assertTrue((REPO / schema_by_kind("conclusion")["rel"]).is_file())
        self.assertTrue((REPO / schema_by_kind("explanatory_note")["rel"]).is_file())
        self.assertTrue((REPO / schema_by_kind("design_assignment")["rel"]).is_file())
        self.assertTrue(by_kind["survey_assignment"]["loadable_xmlschema11"])
        self.assertTrue(by_kind["survey_report"]["loadable_xmlschema11"])
        self.assertEqual(by_kind["survey_assignment"]["root_localname"], "EngineeringSurveysTask")
        self.assertEqual(by_kind["survey_report"]["root_localname"], "GeologicalReport")
        self.assertTrue((REPO / schema_by_kind("survey_assignment")["rel"]).is_file())
        self.assertTrue((REPO / schema_by_kind("survey_report")["rel"]).is_file())

    def test_source_md_refuses_rt001_closed_and_names_dev_folder(self) -> None:
        text = (XSD_DIR / "SOURCE.md").read_text(encoding="utf-8")
        self.assertIn("Does **not** close RT-001", text)
        self.assertIn("01.07", text)
        self.assertIn("01.01", text)
        self.assertIn("dev_", text)
        self.assertIn("duplicate", text.casefold())
        self.assertIn("EngineeringSurveysTask", text)
        self.assertIn("GeologicalReport", text)
        self.assertIn("Construction-stage catalog gap", text)

    def test_vendored_xsd_sha256_pins(self) -> None:
        import hashlib

        pins = {
            "conclusion-01-03.xsd": (
                "46387fa5b4d41f7fad64ff67e8d9aa0b48c6d59864b2eca2acc4c9822aba90ec"
            ),
            "explanatorynote-01-07.xsd": (
                "742dc8ec7f2df425b27fd59d419f3d01e4f25f53025475f9e71f7f4f45459df4"
            ),
            "DesignAssignment-01-01.xsd": (
                "38ff89664f1c8c3bd8fef9366d1ee747aa3313ada6c32dc026d5658d3c040be5"
            ),
            "explanatorynote-01-05.xsd": (
                "6002c961b155322b52ec64462eadb2c58049a0ad7f4411372b4e1f4b432f5f58"
            ),
            "explanatorynote-01-06.xsd": (
                "e3fbc7b338d2b5a7d88855d41904cea5077e681b804489c017f3017823a12569"
            ),
            "DesignAssignment-01-00.xsd": (
                "f566de807cc3f74b807f0498dfd9e31948d14bc7c4146a4b9c1df1f8e2964b23"
            ),
            "EngineeringSurveysTask-01-00.xsd": (
                "7da19458da8d4201f7b42d3ecc858e18f191c6112f2fed0dcf90a2eb22b3b112"
            ),
            "GeologicalReport-01-00.xsd": (
                "b6d55df9621c34ada95420347397b32e8d926e80218736c3ee75dad6c8618b9e"
            ),
        }
        for name, digest in pins.items():
            raw = (XSD_DIR / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest, name)
        snap = egrz_intake_catalog_snapshot()
        self.assertFalse(snap["closes_rt001"])
        self.assertTrue(snap["no_pass_fixture"])
        self.assertEqual(
            snap["loadable_kinds"],
            ["conclusion", "survey_assignment", "survey_report"],
        )
        self.assertEqual(
            snap["sanitize_loadable_kinds"],
            [
                "conclusion",
                "explanatory_note",
                "design_assignment",
                "survey_assignment",
                "survey_report",
            ],
        )
        self.assertEqual(snap["stale_kinds"], [])

    def test_overlay_refuses_rt_close(self) -> None:
        with self.assertRaises(ValueError):
            overlay_egrz_intake({"closes_rt001": True})
        self.assertEqual(EGRZ_INTAKE_LEGAL["product_function"], "egrz_intake_precheck")
        self.assertEqual(
            EGRZ_INTAKE_LEGAL["legal_force_of_cited_npa"],
            FORCE_AGENCY_ORDER,
        )
        self.assertEqual(EGRZ_INTAKE_LEGAL["xsd_files_legal_force"], FORCE_NOT_NPA)
        self.assertFalse(EGRZ_INTAKE_LEGAL["substitutes_egrz_remark_corpus"])

    def test_proxy_stays_intake_not_expertise(self) -> None:
        proxy = egrz_intake_xml_proxy()
        self.assertEqual(proxy["claim_level"], "egrz_intake_precheck")
        self.assertFalse(proxy["closes_rt001"])
        self.assertFalse(proxy["substitutes_grk_art_49_expertise"])
        self.assertFalse(proxy["substitutes_ukep_check"])
        self.assertEqual(proxy["stale_kinds"], [])


class FailFixtureTests(unittest.TestCase):
    def test_missing_instance_fail_closed(self) -> None:
        issues = collect_egrz_xml_validate_issues(
            kind="conclusion",
            xml_path=None,
            xsd_path=XSD_DIR / "conclusion-01-03.xsd",
        )
        self.assertEqual([issue.rule_id for issue in issues], [RULE_MISSING])

    def test_not_wellformed_fail_closed(self) -> None:
        issues = collect_egrz_xml_validate_issues(
            kind="conclusion",
            xml_path=FIXTURES / "not-wellformed.xml",
            xsd_path=XSD_DIR / "conclusion-01-03.xsd",
        )
        self.assertEqual([issue.rule_id for issue in issues], [RULE_WELLFORMED])

    def test_wrong_root_fail_closed_without_loading_xsd(self) -> None:
        issues = collect_egrz_xml_validate_issues(
            kind="conclusion",
            xml_path=FIXTURES / "not-conclusion.xml",
            xsd_path=XSD_DIR / "conclusion-01-03.xsd",
        )
        self.assertEqual([issue.rule_id for issue in issues], [RULE_ROOT])

    def test_empty_pz_fails_listed_xsd_after_xml_id_sanitize(self) -> None:
        issues = collect_egrz_xml_validate_issues(
            kind="explanatory_note",
            xml_path=FIXTURES / "empty-explanatory-note.xml",
            xsd_path=XSD_DIR / "explanatorynote-01-07.xsd",
        )
        ids = [issue.rule_id for issue in issues]
        self.assertEqual(ids, [RULE_XSD])
        self.assertNotIn(RULE_STALE, ids)
        self.assertNotIn(RULE_PARSER, ids)
        issues = collect_egrz_xml_validate_issues(
            kind="explanatory_note",
            xml_path=FIXTURES / "not-conclusion.xml",
            xsd_path=XSD_DIR / "explanatorynote-01-07.xsd",
        )
        ids = [issue.rule_id for issue in issues]
        self.assertEqual(ids, [RULE_ROOT])
        self.assertNotIn(RULE_XSD, ids)

    def test_empty_assignment_fails_listed_xsd_after_xml_id_sanitize(self) -> None:
        issues = collect_egrz_xml_validate_issues(
            kind="design_assignment",
            xml_path=FIXTURES / "empty-design-assignment.xml",
            xsd_path=XSD_DIR / "DesignAssignment-01-01.xsd",
        )
        ids = [issue.rule_id for issue in issues]
        self.assertEqual(ids, [RULE_XSD])
        self.assertNotIn(RULE_STALE, ids)
        self.assertNotIn(RULE_PARSER, ids)
        issues = collect_egrz_xml_validate_issues(
            kind="design_assignment",
            xml_path=FIXTURES / "empty-conclusion.xml",
            xsd_path=XSD_DIR / "DesignAssignment-01-01.xsd",
        )
        ids = [issue.rule_id for issue in issues]
        self.assertEqual(ids, [RULE_ROOT])
        self.assertNotIn(RULE_XSD, ids)

    def test_empty_conclusion_fails_xsd11(self) -> None:
        issues = collect_egrz_xml_validate_issues(
            kind="conclusion",
            xml_path=FIXTURES / "empty-conclusion.xml",
            xsd_path=XSD_DIR / "conclusion-01-03.xsd",
        )
        self.assertTrue(issues)
        self.assertEqual(issues[0].rule_id, RULE_XSD)
        self.assertFalse(any(issue.rule_id == RULE_STALE for issue in issues))

    def test_empty_survey_assignment_fails_xsd(self) -> None:
        issues = collect_egrz_xml_validate_issues(
            kind="survey_assignment",
            xml_path=FIXTURES / "empty-survey-assignment.xml",
            xsd_path=XSD_DIR / "EngineeringSurveysTask-01-00.xsd",
        )
        ids = [issue.rule_id for issue in issues]
        self.assertEqual(ids, [RULE_XSD])
        self.assertNotIn(RULE_PARSER, ids)
        issues = collect_egrz_xml_validate_issues(
            kind="survey_assignment",
            xml_path=FIXTURES / "empty-conclusion.xml",
            xsd_path=XSD_DIR / "EngineeringSurveysTask-01-00.xsd",
        )
        self.assertEqual([issue.rule_id for issue in issues], [RULE_ROOT])

    def test_empty_survey_report_fails_xsd(self) -> None:
        issues = collect_egrz_xml_validate_issues(
            kind="survey_report",
            xml_path=FIXTURES / "empty-survey-report.xml",
            xsd_path=XSD_DIR / "GeologicalReport-01-00.xsd",
        )
        ids = [issue.rule_id for issue in issues]
        self.assertEqual(ids, [RULE_XSD])
        self.assertNotIn(RULE_PARSER, ids)
        issues = collect_egrz_xml_validate_issues(
            kind="survey_report",
            xml_path=FIXTURES / "empty-conclusion.xml",
            xsd_path=XSD_DIR / "GeologicalReport-01-00.xsd",
        )
        self.assertEqual([issue.rule_id for issue in issues], [RULE_ROOT])

    def test_xml_id_strip_makes_pz_text_loadable(self) -> None:
        raw = (XSD_DIR / "explanatorynote-01-07.xsd").read_text(encoding="utf-8")
        self.assertIn('xml:id="Name"', raw)
        sanitized = strip_documentation_xml_ids(raw)
        self.assertNotIn("xml:id=", sanitized)


if __name__ == "__main__":
    unittest.main()
