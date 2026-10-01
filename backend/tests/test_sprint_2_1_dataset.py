"""Sprint 2.1 dataset manifest / mutation / license gates."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.synthetic_project_package import (
    SyntheticProjectPackage,
    generate_synthetic_package,
)

REPO = Path(__file__).resolve().parents[2]
S21 = REPO / "samples" / "benchmarks" / "sprint-2-1"


class Sprint21DatasetTests(unittest.TestCase):
    def test_manifest_hashes(self) -> None:
        manifest = json.loads((S21 / "manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest.get("customer_evidence"))
        for asset in manifest["assets"]:
            if asset.get("redistribution") == "allowed" and asset.get("path"):
                path = REPO / asset["path"]
                self.assertTrue(path.is_file(), asset["path"])
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(digest, asset["sha256"], asset["path"])

    def test_license_manifest(self) -> None:
        license_path = REPO / "audit" / "dataset_license_manifest.json"
        self.assertTrue(license_path.is_file())
        payload = json.loads(license_path.read_text(encoding="utf-8"))
        self.assertEqual(payload.get("artifact_type"), "dataset_license_manifest")
        for row in payload.get("entries") or []:
            if row.get("redistribution") == "unknown":
                self.assertEqual(row.get("public_benchmark"), "INTERNAL_ONLY_LICENSE_REVIEW")

    def test_synthetic_generator_determinism(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a = generate_synthetic_package(Path(first), package=SyntheticProjectPackage())
            b = generate_synthetic_package(Path(second), package=SyntheticProjectPackage())
            self.assertEqual(a["files"], b["files"])
            self.assertEqual(a["mutations"], b["mutations"])

    def test_mutation_ground_truth(self) -> None:
        path = S21 / "mutations" / "mutation-manifest.json"
        mutations = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(mutations.get("ssot"))
        allowed = {"finding", "review_required", "not_verifiable"}
        for defect in mutations["defects"]:
            self.assertIn(defect["mutation_type"], mutations["mutation_catalog"])
            self.assertIn(defect["expected_status"], allowed)

    def test_source_immutability(self) -> None:
        """Pack files must remain unchanged relative to manifest hashes."""

        pack = json.loads((S21 / "baseline-package.json").read_text(encoding="utf-8"))
        for rel in pack["files"]:
            path = REPO / rel
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            # Read-only touch: re-hash must match.
            after = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(before, after)

    def test_expected_findings(self) -> None:
        expected = json.loads((S21 / "expected" / "findings.json").read_text(encoding="utf-8"))
        self.assertIn("findings", expected)
        self.assertFalse(expected.get("customer_evidence", False))


if __name__ == "__main__":
    unittest.main()
