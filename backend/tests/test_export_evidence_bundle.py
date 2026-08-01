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
                "report.html",
                "logs_snippet.txt",
                "README.md",
            ):
                self.assertTrue((output_dir / name).is_file(), msg=name)

            self.assertTrue(str(manifest.get("code_version", "")).startswith("aerobim-backend@"))
            self.assertIn("report.html", manifest.get("artifacts") or {})
            self.assertIn("runtime_settings", manifest)
            self.assertIn("output_file_sha256", manifest)
            self.assertTrue(manifest["output_file_sha256"].get("report.json"))
            self.assertTrue((output_dir / "report.html").read_text(encoding="utf-8"))
            self.assertIn(
                "summary_passed=", (output_dir / "logs_snippet.txt").read_text(encoding="utf-8")
            )
            readme = (output_dir / "README.md").read_text(encoding="utf-8")
            self.assertIn("Forbidden:", readme)
            self.assertNotIn("production-ready", readme.lower())
            self.assertNotIn("customer accuracy achieved", readme.lower())

            coverage = json.loads(
                (output_dir / "capability_coverage.json").read_text(encoding="utf-8")
            )
            self.assertTrue(coverage.get("present"))
            self.assertIsInstance(coverage.get("fields"), dict)
            self.assertIn("ids", coverage["fields"])

            report = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
            self.assertIn("summary", report)
            self.assertEqual(bool(report["summary"]["passed"]), bool(manifest["summary_passed"]))

            # P2 (Checkpoint #2): time-to-first-finding is an auto field with
            # explicit batch semantics — equals analyze_elapsed_ms when the
            # run has findings, null otherwise; never a streaming claim.
            timings = json.loads((output_dir / "timings.json").read_text(encoding="utf-8"))
            self.assertIn("time_to_first_finding_ms", timings)
            self.assertIn(
                "not a streaming-latency claim", timings["time_to_first_finding_semantics"]
            )
            if report["summary"]["issue_count"] > 0:
                self.assertEqual(timings["time_to_first_finding_ms"], timings["analyze_elapsed_ms"])
            else:
                self.assertIsNone(timings["time_to_first_finding_ms"])

    def test_export_wall_guid_demo_includes_annotation_ifc_links(self) -> None:
        from aerobim.tools.export_evidence_bundle import export_evidence_bundle

        repo_root = Path(__file__).resolve().parents[2]
        pack_path = repo_root / "samples" / "benchmarks" / "project-package-wall-guid-demo.json"
        if not pack_path.is_file():
            self.skipTest("wall-guid demo pack missing")
        try:
            import ifcopenshell  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("ifcopenshell not installed")

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory) / "bundle"
            storage_dir = Path(temporary_directory) / "storage"
            manifest = export_evidence_bundle(
                pack_path=pack_path,
                output_dir=output_dir,
                storage_dir=storage_dir,
            )
            report = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
            links = report.get("annotation_ifc_links") or []
            self.assertIsInstance(links, list)
            self.assertGreaterEqual(len(links), 1)
            confirmed = [link for link in links if link.get("ifc_guid")]
            self.assertTrue(confirmed, msg="expected at least one confirmed annotation_ifc_link")
            self.assertIn("reproducibility_hash", manifest)
            self.assertTrue(manifest["reproducibility_hash"])


if __name__ == "__main__":
    unittest.main()
