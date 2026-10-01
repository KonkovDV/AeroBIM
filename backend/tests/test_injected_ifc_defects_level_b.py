"""P-012 Level B (wave 2): programmatic IFC mutations with deterministic outcomes.

Probe-verified 2026-07-31 on wall-fire-rating-rei60.ifc + wall-fire-rating.ids
(clean baseline: passed=True, 0 issues):
- LB-005 missing pset relation  -> IDS error (detected);
- LB-006 wrong FireRating value -> IDS error (detected);
- LB-007 class swap IFCWALL->IFCCOLUMN -> IDS spec is SKIPPED (zero applicable
  elements). Fail-closed contour (29fd0d5) treats SKIPPED as FAILED
  (AEROBIM-IDS-SKIPPED). Compensating entity-presence requirement still
  emits "No elements found for entity IFCWALL".
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.ids_schema_gate import RULE_SKIPPED
from aerobim.domain.models import RequirementSource, ValidationRequest
from aerobim.infrastructure.di.bootstrap import bootstrap_container

REPO_ROOT = Path(__file__).resolve().parents[2]
IFC_BASE = REPO_ROOT / "samples" / "ifc" / "wall-fire-rating-rei60.ifc"
IDS_PATH = REPO_ROOT / "samples" / "ids" / "wall-fire-rating.ids"
ENTITY_PRESENCE_REQ = "SAM-001|IFCWALL|Pset_WallCommon|FireRating|eq|REI60"


def _mutate(base_text: str, defect_id: str) -> str:
    if defect_id == "LB-005":
        return "\n".join(line for line in base_text.splitlines() if not line.startswith("#8="))
    if defect_id == "LB-006":
        return base_text.replace("IFCLABEL('REI60')", "IFCLABEL('REI45')")
    if defect_id == "LB-007":
        return base_text.replace("IFCWALL(", "IFCCOLUMN(")
    raise AssertionError(defect_id)


class InjectedIfcDefectsLevelBTests(unittest.TestCase):
    def _run(self, ifc_path: Path, *, requirement_text: str = ""):
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
        container = bootstrap_container(settings)
        use_case = container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE)
        return use_case.execute(
            ValidationRequest(
                request_id="level-b-ifc",
                ifc_path=ifc_path,
                requirement_source=RequirementSource(text=requirement_text),
                ids_path=IDS_PATH,
            )
        )

    def _mutated_path(self, defect_id: str) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / f"{defect_id}.ifc"
        path.write_text(_mutate(IFC_BASE.read_text(encoding="utf-8"), defect_id), encoding="utf-8")
        return path

    def test_baseline_fixture_is_clean_control(self) -> None:
        report = self._run(IFC_BASE)
        self.assertTrue(report.summary.passed)
        self.assertEqual(report.summary.issue_count, 0)

    def test_lb005_missing_pset_relation_is_detected(self) -> None:
        report = self._run(self._mutated_path("LB-005"))
        self.assertFalse(report.summary.passed)
        self.assertTrue(any(i.rule_id == "IDS-Wall Fire Rating" for i in report.issues))

    def test_lb006_wrong_property_value_is_detected(self) -> None:
        report = self._run(self._mutated_path("LB-006"))
        self.assertFalse(report.summary.passed)
        self.assertTrue(any(i.rule_id == "IDS-Wall Fire Rating" for i in report.issues))

    def test_lb007_class_swap_fails_closed_on_skipped_ids_spec(self) -> None:
        # Honesty anchor (updated 2026-08-14): IfcTester SKIPPED the Wall Fire
        # Rating spec because no IfcWall remains. Fail-closed wiring must not
        # read that as PASS. Historical 2026-07-31 CLAIMS_LOCK still records
        # the pre-gate vacuous pass; this test is the live contour.
        report = self._run(self._mutated_path("LB-007"))
        self.assertFalse(report.summary.passed)
        self.assertTrue(any(i.rule_id == RULE_SKIPPED for i in report.issues))

    def test_lb007_compensating_entity_presence_requirement_fails_closed(self) -> None:
        report = self._run(self._mutated_path("LB-007"), requirement_text=ENTITY_PRESENCE_REQ)
        self.assertFalse(report.summary.passed)
        self.assertTrue(
            any("No elements found for entity IFCWALL" in (i.message or "") for i in report.issues)
        )


if __name__ == "__main__":
    unittest.main()
