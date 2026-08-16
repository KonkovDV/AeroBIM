"""Degraded-scan generator for VLM protocol T4 (self-side plan P4).

Determinism is the contract: same source + seed → byte-identical variants
(sha256 in the provenance manifest). Claim boundary: synthetic robustness
probes only; never customer scans (RT-001).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pytest

from aerobim.tools.generate_degraded_scans import generate_degraded_scans

pymupdf = pytest.importorskip("pymupdf")


def _make_sheet(path: Path) -> None:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "WALL-01 thickness 250 mm")
    page.insert_text((72, 110), "AXIS A-1 / REI 120")
    document.save(path)
    document.close()


class GenerateDegradedScansTests(unittest.TestCase):
    def test_manifest_lists_all_variant_families_with_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sheet.pdf"
            _make_sheet(source)
            output = Path(tmp) / "out"
            manifest = generate_degraded_scans(source, output)

        self.assertEqual(manifest["artifact_type"], "degraded_scan_set")
        self.assertTrue(manifest["source"]["sha256"])
        names = {item["variant"] for item in manifest["variants"]}
        self.assertIn("baseline_200dpi", names)
        # Default families: 3 lowres + 2 rotate + 2 noise + baseline = 8.
        self.assertEqual(len(names), 8)
        self.assertTrue(any(name.startswith("lowres_") for name in names))
        self.assertTrue(any(name.startswith("rotate_") for name in names))
        self.assertTrue(any(name.startswith("noise_") for name in names))
        self.assertIn("RT-001", manifest["claim_boundary"])

    def test_variants_written_and_hashes_match_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sheet.pdf"
            _make_sheet(source)
            output = Path(tmp) / "out"
            manifest = generate_degraded_scans(source, output)
            import hashlib

            for item in manifest["variants"]:
                payload = (output / item["file"]).read_bytes()
                self.assertEqual(
                    hashlib.sha256(payload).hexdigest(), item["sha256"], msg=item["variant"]
                )
            written = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(written["variants"], manifest["variants"])

    def test_same_seed_is_byte_deterministic_and_seed_changes_noise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sheet.pdf"
            _make_sheet(source)
            first = generate_degraded_scans(source, Path(tmp) / "a", seed=7)
            second = generate_degraded_scans(source, Path(tmp) / "b", seed=7)
            third = generate_degraded_scans(source, Path(tmp) / "c", seed=8)

        hashes = [
            {item["variant"]: item["sha256"] for item in run["variants"]}
            for run in (first, second, third)
        ]
        self.assertEqual(hashes[0], hashes[1])  # same seed -> byte-identical
        noise_variants = [name for name in hashes[0] if name.startswith("noise_")]
        self.assertTrue(noise_variants)
        for name in noise_variants:
            self.assertNotEqual(hashes[0][name], hashes[2][name], msg=name)
        # Non-noise families are seed-independent (pure render).
        for name in hashes[0]:
            if not name.startswith("noise_"):
                self.assertEqual(hashes[0][name], hashes[2][name], msg=name)

    def test_degradation_actually_reduces_information(self) -> None:
        """Sanity: lowres_72dpi image must be materially smaller than the
        200 dpi baseline (resolution loss is real, not a rename)."""
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sheet.pdf"
            _make_sheet(source)
            output = Path(tmp) / "out"
            generate_degraded_scans(source, output)
            baseline = (output / "baseline_200dpi.png").stat().st_size
            lowres = (output / "lowres_72dpi.png").stat().st_size
        self.assertLess(lowres, baseline)

    def test_invalid_inputs_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sheet.pdf"
            _make_sheet(source)
            output = Path(tmp) / "out"
            with self.assertRaises(FileNotFoundError):
                generate_degraded_scans(Path(tmp) / "missing.pdf", output)
            with self.assertRaises(ValueError):
                generate_degraded_scans(source, output, dpi_variants=(300,))
            with self.assertRaises(ValueError):
                generate_degraded_scans(source, output, angles=(45.0,))
            with self.assertRaises(ValueError):
                generate_degraded_scans(source, output, noise_percents=(50.0,))
            with self.assertRaises(ValueError):
                generate_degraded_scans(source, output, page_number=5)


if __name__ == "__main__":
    unittest.main()
