"""IDS buildingSMART TestCases importer — pins and fail-closed behavior."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEST = REPO / "samples" / "ids" / "buildingsmart-testcases"
PINS = DEST / "IMPORT_PINS.json"
PROFILE = REPO / "samples" / "benchmarks" / "open-corpora" / "profiles" / "regression-bsi.json"
MIN_TARGET = 250


class IdsImporterTests(unittest.TestCase):
    def test_importer_module_exposes_discover_helper(self) -> None:
        from aerobim.tools.import_buildingsmart_ids_testcases import discover_ids_ifc_pairs

        self.assertTrue(callable(discover_ids_ifc_pairs))

    def test_offline_run_import_requires_commit_or_source(self) -> None:
        from aerobim.tools.import_buildingsmart_ids_testcases import run_import

        with self.assertRaises(RuntimeError):
            run_import(source_dir=None, commit=None, allow_floating_tip=False, max_cases=None)

    def test_vendored_pins_meet_target_when_present(self) -> None:
        if not PINS.is_file():
            self.skipTest("IDS import not run — execute import_buildingsmart_ids_testcases")
        payload = json.loads(PINS.read_text(encoding="utf-8"))
        case_count = int(payload.get("case_count") or 0)
        self.assertGreaterEqual(case_count, MIN_TARGET)
        self.assertEqual(payload.get("license"), "CC-BY-ND-4.0")
        self.assertTrue((DEST / "NOTICE").is_file())

    def test_regression_bsi_profile_honest_count(self) -> None:
        if not PROFILE.is_file():
            self.skipTest("regression-bsi profile missing")
        profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        self.assertGreaterEqual(int(profile.get("honest_case_count") or 0), MIN_TARGET)
        if PINS.is_file():
            pins_payload = json.loads(PINS.read_text(encoding="utf-8"))
            self.assertEqual(profile["honest_case_count"], pins_payload["case_count"])


if __name__ == "__main__":
    unittest.main()
