from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.models import ConflictKind, FindingCategory, Severity
from aerobim.infrastructure.adapters.json_section_diff_analyzer import JsonSectionDiffAnalyzer

REPO_ROOT = Path(__file__).resolve().parents[2]
SECTIONS = REPO_ROOT / "samples" / "sections"
PD_SECTION = SECTIONS / "ar-pd-synthetic.json"
RD_SECTION = SECTIONS / "ar-rd-synthetic.json"
KZH_PD_SECTION = SECTIONS / "kzh-pd-synthetic.json"
KZH_RD_SECTION = SECTIONS / "kzh-rd-synthetic.json"
SECTION_SCHEMA = SECTIONS / "section-pair.schema.json"


class JsonSectionDiffAnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = JsonSectionDiffAnalyzer(severity=Severity.WARNING)

    def test_detects_expected_synthetic_ar_findings_with_si_equivalence(self) -> None:
        issues = self.analyzer.compare(PD_SECTION, RD_SECTION)

        self.assertEqual(len(issues), 3)
        self.assertTrue(all(issue.category is FindingCategory.CROSS_DOCUMENT for issue in issues))
        targets = {issue.target_ref for issue in issues}
        self.assertEqual(
            targets,
            {"APT-01", "DOOR-TYPE-D1", "FACADE-TYPE-F1"},
        )
        rule_ids = {issue.rule_id for issue in issues}
        self.assertNotIn("SECTION-PAIR-AR-BUILDING-HEIGHT", rule_ids)
        self.assertNotIn("SECTION-PAIR-AR-WALL-EXTERNAL-THICKNESS", rule_ids)
        self.assertNotIn("SECTION-PAIR-AR-RAILING-HEIGHT", rule_ids)

    def test_preserves_problem_zone_and_pair_provenance(self) -> None:
        issues = self.analyzer.compare(PD_SECTION, RD_SECTION)
        area_issue = next(issue for issue in issues if issue.target_ref == "APT-01")

        self.assertEqual(area_issue.conflict_kind, ConflictKind.HARD_CONFLICT)
        self.assertEqual(area_issue.problem_zone.sheet_id, "RD-AR-102")
        self.assertIn("SYNTHETIC-AR-PD-001@P0", area_issue.source_id or "")
        self.assertEqual(area_issue.evidence_modality, "section-pairing")
        self.assertEqual(area_issue.confidence, 1.0)

    def test_basis_revision_mismatch_is_explicit(self) -> None:
        payload = json.loads(RD_SECTION.read_text(encoding="utf-8"))
        payload["basis"]["revision"] = "P-STALE"
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "rd.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            issues = self.analyzer.compare(PD_SECTION, path)

        issue = next(item for item in issues if item.rule_id.endswith("BASIS-REVISION"))
        self.assertEqual(issue.conflict_kind, ConflictKind.VERSION_MISMATCH)

    def test_project_mismatch_is_rejected_instead_of_cross_pairing(self) -> None:
        payload = json.loads(RD_SECTION.read_text(encoding="utf-8"))
        payload["project_id"] = "OTHER-PROJECT"
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "rd.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "project_id mismatch"):
                self.analyzer.compare(PD_SECTION, path)

    def test_incompatible_units_are_classified_without_fuzzy_matching(self) -> None:
        payload = json.loads(RD_SECTION.read_text(encoding="utf-8"))
        height = next(item for item in payload["values"] if item["key"] == "building.height")
        height["unit"] = "m2"
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "rd.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            issues = self.analyzer.compare(PD_SECTION, path)

        issue = next(item for item in issues if item.rule_id.endswith("BUILDING-HEIGHT"))
        self.assertEqual(issue.conflict_kind, ConflictKind.UNIT_MISMATCH)

    def test_analyze_reports_canonical_discipline_and_key_coverage(self) -> None:
        report = self.analyzer.analyze(PD_SECTION, RD_SECTION)

        self.assertEqual(report.discipline.code, "AR")
        self.assertTrue(report.discipline.recognized)
        self.assertEqual(report.pd_key_count, 7)
        self.assertEqual(report.recognized_key_count, 7)
        self.assertEqual(report.unrecognized_keys, ())
        self.assertIn("canonical-key coverage=7/7", report.capability_reason("pd.json", "rd.json"))

    def test_kzh_pair_uses_cross_language_canonical_matching(self) -> None:
        report = self.analyzer.analyze(KZH_PD_SECTION, KZH_RD_SECTION)

        # RU alias 'защитный.слой' (RD) folds onto EN canonical 'rebar.cover' (PD)
        # and the SI-equivalent 25 mm vs 0.025 m must NOT be a false positive.
        self.assertEqual(len(report.issues), 3)
        self.assertEqual(
            {issue.target_ref for issue in report.issues},
            {"CONCRETE-01", "SLAB-01", "FOUND-01"},
        )
        self.assertEqual(report.discipline.code, "KZH")
        self.assertTrue(report.discipline.recognized)
        self.assertEqual(report.recognized_key_count, report.pd_key_count)

    def test_cyrillic_section_code_yields_stable_latin_rule_ids(self) -> None:
        issues = self.analyzer.compare(KZH_PD_SECTION, KZH_RD_SECTION)
        rule_ids = {issue.rule_id for issue in issues}
        self.assertIn("SECTION-PAIR-KZH-CONCRETE-CLASS", rule_ids)
        self.assertIn("SECTION-PAIR-KZH-FOUNDATION-DEPTH", rule_ids)
        # Every rule id must be ASCII / slug-safe for BCF and URLs.
        for rule_id in rule_ids:
            self.assertTrue(rule_id.isascii(), rule_id)

    def test_ru_en_discipline_labels_do_not_trigger_false_metadata_mismatch(self) -> None:
        payload = json.loads(RD_SECTION.read_text(encoding="utf-8"))
        payload["discipline"] = "АР"  # Cyrillic vs PD's Latin "AR"
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "rd.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            issues = self.analyzer.compare(PD_SECTION, path)

        self.assertFalse(
            any(issue.rule_id.endswith("-DISCIPLINE") for issue in issues),
            "AR vs АР must fold to one canonical discipline, not a mismatch",
        )

    def test_ambiguous_canonical_keys_fail_closed(self) -> None:
        payload = json.loads(PD_SECTION.read_text(encoding="utf-8"))
        # 'площадь.квартиры' and 'apartment.area.total' both canonicalize to the
        # same key within one document -> deterministic refusal, not silent drop.
        payload["values"].append(
            {
                "key": "площадь.квартиры",
                "value": 80,
                "unit": "m2",
                "target_ref": "APT-02",
                "source_ref": "PD-AR duplicate",
            }
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "pd.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "canonical key"):
                self.analyzer.compare(path, RD_SECTION)


class SectionFixtureSchemaTests(unittest.TestCase):
    """The shipped fixtures must validate against the published section schema."""

    def test_all_section_fixtures_conform_to_schema(self) -> None:
        import jsonschema

        schema = json.loads(SECTION_SCHEMA.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        for fixture in (PD_SECTION, RD_SECTION, KZH_PD_SECTION, KZH_RD_SECTION):
            with self.subTest(fixture=fixture.name):
                payload = json.loads(fixture.read_text(encoding="utf-8"))
                errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
                self.assertEqual(errors, [], f"{fixture.name}: {[e.message for e in errors]}")


if __name__ == "__main__":
    unittest.main()
