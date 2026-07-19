"""Evidence bundle CLI: fixture pack → reproducible artifact set."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class ExportEvidenceBundleTests(unittest.TestCase):
    def test_export_techlab_demo_bundle_writes_required_artifacts(self) -> None:
        from aerobim.tools.export_evidence_bundle import export_evidence_bundle

        repo_root = Path(__file__).resolve().parents[2]
        pack_path = repo_root / "samples" / "benchmarks" / "project-package-techlab-demo.json"
        if not pack_path.is_file():
            self.skipTest("techlab-demo pack missing")

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory) / "bundle"
            storage_dir = Path(temporary_directory) / "storage"
            manifest = export_evidence_bundle(
                pack_path=pack_path,
                output_dir=output_dir,
                storage_dir=storage_dir,
            )

            self.assertEqual(manifest["artifact_type"], "aerobim_evidence_bundle")
            self.assertEqual(manifest["pack_id"], "project-package-techlab-demo")
            self.assertIn("summary_passed", manifest)
            self.assertIn("derived_outcome", manifest)
            self.assertIn(manifest["derived_outcome"], {"PASS", "BLOCKED", "FAILED"})
            self.assertTrue(manifest["source_files"])
            self.assertTrue(any(item.get("sha256") for item in manifest["source_files"]))

            for name in (
                "manifest.json",
                "report.json",
                "findings.json",
                "capability_coverage.json",
                "timings.json",
                "README.md",
            ):
                self.assertTrue((output_dir / name).is_file(), msg=name)

            coverage = json.loads(
                (output_dir / "capability_coverage.json").read_text(encoding="utf-8")
            )
            self.assertTrue(coverage.get("present"))
            self.assertIsInstance(coverage.get("fields"), dict)
            self.assertIn("ids", coverage["fields"])

            report = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
            self.assertIn("summary", report)
            self.assertEqual(bool(report["summary"]["passed"]), bool(manifest["summary_passed"]))


if __name__ == "__main__":
    unittest.main()
