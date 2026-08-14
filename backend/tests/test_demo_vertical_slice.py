from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.run_demo_vertical_slice import (
    DemoSliceError,
    main,
    run_demo_vertical_slice,
)


class DemoVerticalSliceTests(unittest.TestCase):
    def test_end_to_end_writes_html_json_bcf_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = run_demo_vertical_slice(output_dir=out)
            self.assertGreaterEqual(summary["drawing_annotation_count"], 1)
            self.assertGreaterEqual(summary["finding_count"], 1)
            self.assertIn("fixture_only", summary["claim_boundary"])
            self.assertTrue((out / "report.html").is_file())
            self.assertTrue((out / "report.json").is_file())
            self.assertTrue((out / "findings.bcfzip").is_file())
            overlay = out / "overlay-problem-zone.png"
            self.assertTrue(overlay.is_file())
            self.assertEqual(overlay.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            html = (out / "report.html").read_text(encoding="utf-8")
            self.assertIn("finding_id=", html.lower())
            self.assertIn("evidence_refs=", html.lower())
            self.assertIn("kt2-overlay", html)
            self.assertIn("overlay-problem-zone.png", html)
            self.assertIn("Not CV", html)
            report = json.loads((out / "report.json").read_text(encoding="utf-8"))
            self.assertFalse(report["summary"]["passed"])

    def test_missing_manifest_is_loud(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope.json"
            with self.assertRaises(DemoSliceError):
                run_demo_vertical_slice(manifest=missing, output_dir=Path(tmp) / "out")
            self.assertEqual(main(["--manifest", str(missing), "--output", str(Path(tmp) / "out")]), 1)


if __name__ == "__main__":
    unittest.main()
