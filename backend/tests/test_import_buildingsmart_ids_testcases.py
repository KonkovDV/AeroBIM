"""IDS TestCases importer — local unmodified pairs + fail-closed gates."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.import_buildingsmart_ids_testcases import (
    CLAIM_BOUNDARY,
    discover_ids_ifc_pairs,
    run_import,
)


class ImportBuildingsmartIdsTests(unittest.TestCase):
    def test_discover_pass_fail_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pass-demo.ids").write_text("<ids/>", encoding="utf-8")
            (root / "pass-demo.ifc").write_text("ISO-10303-21;", encoding="utf-8")
            (root / "fail-demo.ids").write_text("<ids/>", encoding="utf-8")
            (root / "fail-demo.ifc").write_text("ISO-10303-21;", encoding="utf-8")
            (root / "notes.txt").write_text("x", encoding="utf-8")
            pairs = discover_ids_ifc_pairs(root)
            self.assertEqual(len(pairs), 2)
            outcomes = {p["expected_outcome"] for p in pairs}
            self.assertEqual(outcomes, {"pass", "fail"})

    def test_run_import_from_source_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Build a fake IDS repo layout
            ids_root = Path(tmp) / "IDS"
            testcases = (
                ids_root / "Documentation" / "ImplementersDocumentation" / "TestCases" / "attribute"
            )
            testcases.mkdir(parents=True)
            (testcases / "pass-attr.ids").write_text("<ids/>", encoding="utf-8")
            (testcases / "pass-attr.ifc").write_text("ISO-10303-21;", encoding="utf-8")
            (testcases / "fail-attr.ids").write_text("<ids/>", encoding="utf-8")
            (testcases / "fail-attr.ifc").write_text("ISO-10303-21;", encoding="utf-8")

            # Point importer at temp as if it were repo by monkeypatching repo_root
            import aerobim.tools.import_buildingsmart_ids_testcases as mod

            fake_repo = Path(tmp) / "aerobim-repo"
            (fake_repo / "audit").mkdir(parents=True)
            (fake_repo / "samples" / "benchmarks" / "open-corpora" / "profiles").mkdir(parents=True)
            (fake_repo / "audit" / "dataset_license_manifest.json").write_text(
                json.dumps({"assets": [{"id": "ids-test-suite", "license": "unclear"}]}),
                encoding="utf-8",
            )
            (fake_repo / "samples" / "benchmarks" / "open-corpora" / "manifest.json").write_text(
                json.dumps({"profiles": []}),
                encoding="utf-8",
            )

            original = mod.repo_root
            mod.repo_root = lambda: fake_repo  # type: ignore[assignment]
            try:
                report = run_import(
                    source_dir=ids_root,
                    commit="deadbeef",
                    allow_floating_tip=False,
                    max_cases=None,
                )
            finally:
                mod.repo_root = original  # type: ignore[assignment]

            self.assertEqual(report["honest_case_count"], 2)
            self.assertIn("CC-BY-ND", report["license"])
            self.assertIn("NOT product accuracy", report["claim_boundary"])
            profile = fake_repo / "samples/benchmarks/open-corpora/profiles/regression-bsi.json"
            self.assertTrue(profile.is_file())
            payload = json.loads(profile.read_text(encoding="utf-8"))
            self.assertEqual(payload["honest_case_count"], 2)
            self.assertEqual(payload["claim_boundary"], CLAIM_BOUNDARY)
            notice = fake_repo / "samples/ids/buildingsmart-testcases/NOTICE"
            self.assertTrue(notice.is_file())

    def test_refuse_download_without_commit(self) -> None:
        with self.assertRaises(RuntimeError):
            run_import(
                source_dir=None,
                commit=None,
                allow_floating_tip=False,
                max_cases=None,
            )


if __name__ == "__main__":
    unittest.main()
