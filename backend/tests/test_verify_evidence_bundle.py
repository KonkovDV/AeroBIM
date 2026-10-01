"""Evidence bundle verifier: tamper-evidence + dual-truth checks (Wave I).

Anchors (Jul 2026): SLSA provenance — verifier recomputes digests, never
trusts declared hashes; RTATOM-G04 (dual-truth HTML) regression class.
Claim boundary: tamper-evidence only, no signature; fixture packs prove
Shared-gate honesty, not customer claims.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.verify_evidence_bundle import verify_evidence_bundle

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PACK = _REPO_ROOT / "samples" / "benchmarks" / "project-package-techlab-demo.json"


class EvidenceBundleVerifierTests(unittest.TestCase):
    _bundle_dir: Path
    _tmp: tempfile.TemporaryDirectory

    @classmethod
    def setUpClass(cls) -> None:
        if not _PACK.is_file():
            raise unittest.SkipTest("techlab-demo pack missing")
        from aerobim.tools.export_evidence_bundle import export_evidence_bundle

        cls._tmp = tempfile.TemporaryDirectory()
        root = Path(cls._tmp.name)
        cls._bundle_dir = root / "bundle"
        export_evidence_bundle(
            pack_path=_PACK,
            output_dir=cls._bundle_dir,
            storage_dir=root / "storage",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _copy_bundle(self, destination_root: Path) -> Path:
        target = destination_root / "bundle-copy"
        shutil.copytree(self._bundle_dir, target)
        return target

    def test_fresh_bundle_verifies(self) -> None:
        result = verify_evidence_bundle(self._bundle_dir)
        self.assertTrue(result["ok"], msg=result["errors"])
        self.assertEqual(result["verification"], "passed")
        self.assertGreater(result["hashes_checked"], 0)

    def test_fresh_bundle_files_are_lf_only(self) -> None:
        for path in self._bundle_dir.iterdir():
            if path.is_file():
                self.assertNotIn(b"\r\n", path.read_bytes(), msg=path.name)

    def test_tampered_findings_json_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = self._copy_bundle(Path(tmp))
            findings_path = bundle / "findings.json"
            findings = json.loads(findings_path.read_text(encoding="utf-8"))
            findings.append({"rule_id": "FORGED", "severity": "info", "message": "x"})
            findings_path.write_text(json.dumps(findings), encoding="utf-8")
            result = verify_evidence_bundle(bundle)
        self.assertFalse(result["ok"])
        self.assertTrue(any("findings.json" in error for error in result["errors"]))

    def test_flipped_pass_in_html_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = self._copy_bundle(Path(tmp))
            html_path = bundle / "report.html"
            text = html_path.read_text(encoding="utf-8")
            flipped = (
                text.replace("summary.passed=FAILED", "summary.passed=PASSED")
                if "summary.passed=FAILED" in text
                else text.replace("summary.passed=PASSED", "summary.passed=FAILED")
            )
            html_path.write_text(flipped, encoding="utf-8")
            result = verify_evidence_bundle(bundle)
        self.assertFalse(result["ok"])
        # Digest mismatch always fires; the dual-truth check names report.html too.
        self.assertTrue(any("report.html" in error for error in result["errors"]))

    def test_missing_declared_artifact_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = self._copy_bundle(Path(tmp))
            (bundle / "timings.json").unlink()
            result = verify_evidence_bundle(bundle)
        self.assertFalse(result["ok"])
        self.assertTrue(any("timings.json" in error for error in result["errors"]))

    def test_manifest_issue_count_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = self._copy_bundle(Path(tmp))
            manifest_path = bundle / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["issue_count"] = int(manifest.get("issue_count") or 0) + 5
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = verify_evidence_bundle(bundle)
        self.assertFalse(result["ok"])
        self.assertTrue(any("issue_count" in error for error in result["errors"]))

    def test_missing_manifest_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = verify_evidence_bundle(Path(tmp))
        self.assertFalse(result["ok"])
        self.assertIn("manifest.json missing", result["errors"])


if __name__ == "__main__":
    unittest.main()
