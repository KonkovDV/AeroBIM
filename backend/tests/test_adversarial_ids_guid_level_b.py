"""P-012 Level B (wave 3): adversarial IDS inputs + duplicate-GUID boundary.

Probe-verified 2026-07-31 against the clean rei60+IDS baseline:
- malformed / wrong-namespace / empty IDS  -> ids capability FAILED, passed=False
  (fail-closed: a broken rule source can never green-pass);
- duplicate GlobalId (both walls pset-compliant) -> AEROBIM-GUID-DUPLICATE
  WARNING (verdict-neutral: passed stays True). Closed consciously 2026-07-31;
  the former known-undetected anchor was updated together with the catalog.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import CapabilityState, RequirementSource, ValidationRequest
from aerobim.infrastructure.di.bootstrap import bootstrap_container

REPO_ROOT = Path(__file__).resolve().parents[2]
IFC_BASE = REPO_ROOT / "samples" / "ifc" / "wall-fire-rating-rei60.ifc"
IDS_PATH = REPO_ROOT / "samples" / "ids" / "wall-fire-rating.ids"
_WALL_LINE = "#6=IFCWALL('38FRviGan7WhU9JrK165gm',$,'Fixture Wall',$,$,$,$,$,$);"


class AdversarialIdsAndGuidLevelBTests(unittest.TestCase):
    def _tmp(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return Path(temp_dir.name)

    def _run(self, ifc_path: Path, ids_path: Path):
        root = self._tmp()
        settings = Settings(
            application_name="aerobim-test",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=root / "var",
            debug=True,
        )
        settings.storage_dir.mkdir(parents=True, exist_ok=True)
        container = bootstrap_container(settings)
        use_case = container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE)
        return use_case.execute(
            ValidationRequest(
                request_id="level-b-w3",
                ifc_path=ifc_path,
                requirement_source=RequirementSource(text=""),
                ids_path=ids_path,
            )
        )

    def _assert_ids_fail_closed(self, ids_text: str, expected_rule: str) -> None:
        ids_path = self._tmp() / "adversarial.ids"
        ids_path.write_text(ids_text, encoding="utf-8")
        report = self._run(IFC_BASE, ids_path)
        self.assertFalse(report.summary.passed)
        assert report.capabilities is not None
        ids_cap = report.capabilities.ids
        assert ids_cap is not None
        self.assertIs(ids_cap.status, CapabilityState.FAILED)
        self.assertTrue(any(i.rule_id == expected_rule for i in report.issues))

    def test_lb008_malformed_ids_fails_closed(self) -> None:
        text = IDS_PATH.read_text(encoding="utf-8")
        self._assert_ids_fail_closed(text[: len(text) // 2], "AEROBIM-IDS-AUDIT")

    def test_lb009_wrong_namespace_ids_fails_closed(self) -> None:
        text = IDS_PATH.read_text(encoding="utf-8").replace(
            "http://standards.buildingsmart.org/IDS", "http://example.com/not-ids"
        )
        self._assert_ids_fail_closed(text, "AEROBIM-IDS-XSD-INVALID")

    def test_lb010_empty_ids_fails_closed(self) -> None:
        self._assert_ids_fail_closed("", "AEROBIM-IDS-AUDIT")

    def test_lb011_duplicate_guid_yields_warning_verdict_neutral(self) -> None:
        # LB-011 closed consciously: the schema pre-gate now emits a WARNING per
        # duplicated GlobalId. Verdict-neutral by design -- passed stays True.
        base = IFC_BASE.read_text(encoding="utf-8")
        assert _WALL_LINE in base
        mutated = base.replace(
            _WALL_LINE,
            _WALL_LINE
            + "\n#16=IFCWALL('38FRviGan7WhU9JrK165gm',$,'Duplicate GUID Wall',$,$,$,$,$,$);",
        ).replace("(#6),#7);", "(#6,#16),#7);")
        ifc_path = self._tmp() / "dup-guid.ifc"
        ifc_path.write_text(mutated, encoding="utf-8")
        report = self._run(ifc_path, IDS_PATH)
        duplicates = [i for i in report.issues if i.rule_id == "AEROBIM-GUID-DUPLICATE"]
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0].element_guid, "38FRviGan7WhU9JrK165gm")
        self.assertTrue(report.summary.passed)  # WARNING never flips the verdict

    def test_unique_guids_produce_no_duplicate_warning_control(self) -> None:
        report = self._run(IFC_BASE, IDS_PATH)
        self.assertFalse(any(i.rule_id == "AEROBIM-GUID-DUPLICATE" for i in report.issues))
        self.assertTrue(report.summary.passed)


if __name__ == "__main__":
    unittest.main()
