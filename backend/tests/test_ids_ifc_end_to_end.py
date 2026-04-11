from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import FindingCategory, RequirementSource, ValidationRequest
from aerobim.infrastructure.di.bootstrap import bootstrap_container

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = REPO_ROOT / "samples"
IDS_FIXTURE = SAMPLES_DIR / "ids" / "wall-fire-rating.ids"
IFC_PASS_FIXTURE = SAMPLES_DIR / "ifc" / "wall-fire-rating-rei60.ifc"
IFC_FAIL_FIXTURE = SAMPLES_DIR / "ifc" / "wall-fire-rating-rei30.ifc"
IDS_MULTI_FIXTURE = SAMPLES_DIR / "ids" / "walls-multi-entity.ids"
IFC_MULTI_FIXTURE = SAMPLES_DIR / "ifc" / "walls-multi-entity.ifc"
IDS_QTO_FIXTURE = SAMPLES_DIR / "ids" / "wall-pset-qto.ids"
IFC_QTO_PASS_FIXTURE = SAMPLES_DIR / "ifc" / "wall-pset-qto-pass.ifc"
IFC_QTO_MISSING_FIXTURE = SAMPLES_DIR / "ifc" / "wall-pset-qto-missing-qto.ifc"


class RealIdsIfcEndToEndTests(unittest.TestCase):
    def _make_container(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        settings = Settings(
            application_name="aerobim-test",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path(temp_dir.name) / "var",
            debug=True,
        )
        settings.storage_dir.mkdir(parents=True, exist_ok=True)
        return bootstrap_container(settings)

    def test_ids_fixture_passes_for_matching_ifc(self) -> None:
        container = self._make_container()
        use_case = container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE)
        store = container.resolve(Tokens.AUDIT_REPORT_STORE)

        report = use_case.execute(
            ValidationRequest(
                request_id="req-ids-pass",
                ifc_path=IFC_PASS_FIXTURE,
                requirement_source=RequirementSource(text=""),
                ids_path=IDS_FIXTURE,
            )
        )

        self.assertEqual(report.summary.requirement_count, 0)
        self.assertEqual(report.summary.issue_count, 0)
        self.assertTrue(report.summary.passed)
        self.assertIsNotNone(store.get(report.report_id))

    def test_ids_fixture_fails_for_nonmatching_ifc(self) -> None:
        container = self._make_container()
        use_case = container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE)
        store = container.resolve(Tokens.AUDIT_REPORT_STORE)

        report = use_case.execute(
            ValidationRequest(
                request_id="req-ids-fail",
                ifc_path=IFC_FAIL_FIXTURE,
                requirement_source=RequirementSource(text=""),
                ids_path=IDS_FIXTURE,
            )
        )

        self.assertEqual(report.summary.requirement_count, 0)
        self.assertEqual(report.summary.issue_count, 1)
        self.assertEqual(len(report.issues), 1)
        self.assertFalse(report.summary.passed)
        self.assertEqual(report.issues[0].category, FindingCategory.IDS_VALIDATION)
        self.assertIn("REI30", report.issues[0].message)
        self.assertIsNotNone(report.issues[0].element_guid)

        stored = store.get(report.report_id)
        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(stored.summary.issue_count, 1)

    def test_multi_entity_ids_detects_two_failures(self) -> None:
        """3 walls: 1 passes, 1 wrong FireRating, 1 missing property → 2 IDS issues."""
        container = self._make_container()
        use_case = container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE)
        store = container.resolve(Tokens.AUDIT_REPORT_STORE)

        report = use_case.execute(
            ValidationRequest(
                request_id="req-ids-multi",
                ifc_path=IFC_MULTI_FIXTURE,
                requirement_source=RequirementSource(text=""),
                ids_path=IDS_MULTI_FIXTURE,
            )
        )

        self.assertFalse(report.summary.passed)
        ids_issues = [i for i in report.issues if i.category == FindingCategory.IDS_VALIDATION]
        self.assertEqual(len(ids_issues), 2, f"Expected 2 IDS failures; got {len(ids_issues)}")
        guids = {i.element_guid for i in ids_issues}
        self.assertEqual(len(guids), 2, "Each failing wall must have a distinct GUID")
        for issue in ids_issues:
            self.assertIsNotNone(issue.element_guid)

        stored = store.get(report.report_id)
        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(stored.summary.issue_count, 2)

    def test_ids_combined_with_structured_requirements(self) -> None:
        """IDS issues merge with requirement-based issues in a single report."""
        container = self._make_container()
        use_case = container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE)

        report = use_case.execute(
            ValidationRequest(
                request_id="req-ids-combined",
                ifc_path=IFC_FAIL_FIXTURE,
                requirement_source=RequirementSource(
                    text="SAM-001|IFCWALL|Pset_WallCommon|FireRating|eq|REI60",
                ),
                ids_path=IDS_FIXTURE,
            )
        )

        ids_issues = [i for i in report.issues if i.category == FindingCategory.IDS_VALIDATION]
        ifc_issues = [i for i in report.issues if i.category == FindingCategory.IFC_VALIDATION]
        self.assertGreaterEqual(len(ids_issues), 1)
        self.assertGreaterEqual(len(ifc_issues), 1)
        self.assertGreater(report.summary.issue_count, 1)

    def test_quantity_set_ids_passes_when_qto_present(self) -> None:
        """IDS with Pset + Qto specs passes when IFC has both sets."""
        container = self._make_container()
        use_case = container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE)

        report = use_case.execute(
            ValidationRequest(
                request_id="req-qto-pass",
                ifc_path=IFC_QTO_PASS_FIXTURE,
                requirement_source=RequirementSource(text=""),
                ids_path=IDS_QTO_FIXTURE,
            )
        )
        self.assertTrue(report.summary.passed)
        self.assertEqual(report.summary.issue_count, 0)

    def test_quantity_set_ids_fails_when_qto_missing(self) -> None:
        """IDS with Pset + Qto specs fails when IFC is missing the quantity set."""
        container = self._make_container()
        use_case = container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE)
        store = container.resolve(Tokens.AUDIT_REPORT_STORE)

        report = use_case.execute(
            ValidationRequest(
                request_id="req-qto-fail",
                ifc_path=IFC_QTO_MISSING_FIXTURE,
                requirement_source=RequirementSource(text=""),
                ids_path=IDS_QTO_FIXTURE,
            )
        )
        self.assertFalse(report.summary.passed)
        ids_issues = [i for i in report.issues if i.category == FindingCategory.IDS_VALIDATION]
        self.assertEqual(len(ids_issues), 1, "Only the Qto spec should fail")
        self.assertIn("Width", ids_issues[0].message)
        stored = store.get(report.report_id)
        self.assertIsNotNone(stored)


if __name__ == "__main__":
    unittest.main()