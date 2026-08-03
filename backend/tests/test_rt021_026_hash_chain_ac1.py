"""Package source hash chain + Gwet AC1 wave tests (RT-021 / RT-026)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.eval_statistics import agreement_artifact, gwet_ac1
from aerobim.domain.package_source_integrity import (
    build_package_source_hash_chain,
    compare_hash_chains,
)
from aerobim.tools.measure_adjudicator_agreement import measure_adjudication_csv


class GwetAc1Tests(unittest.TestCase):
    def test_perfect_agreement_is_one(self) -> None:
        self.assertEqual(gwet_ac1(["TP", "FP", "FN"], ["TP", "FP", "FN"]), 1.0)

    def test_hand_computed_two_category(self) -> None:
        # n=5; agree on 4 → po=0.8
        # cats {1,2}; counts_a: 1→3,2→2; counts_b: 1→4,2→1
        # π1=(3+4)/10=0.7; π2=(2+1)/10=0.3
        # pe=(1/1)*(0.7*0.3+0.3*0.7)=0.42
        # AC1=(0.8-0.42)/(1-0.42)=0.38/0.58
        value = gwet_ac1(["1", "1", "2", "2", "1"], ["1", "1", "2", "1", "1"])
        self.assertAlmostEqual(value, 0.38 / 0.58, places=9)

    def test_agreement_artifact_includes_ac1(self) -> None:
        units = [
            {"a": "TP", "b": "TP"},
            {"a": "FP", "b": "FP"},
            {"a": "FN", "b": "FN"},
        ]
        payload = agreement_artifact(units)
        self.assertIn("gwet_ac1", payload)
        self.assertTrue(payload["pass_ac1_0_60"])
        self.assertEqual(payload["schema_version"], "1.1.0")


class PackageSourceHashChainTests(unittest.TestCase):
    def test_emit_and_diff_detects_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "pkg" / "drawing.pdf"
            src.parent.mkdir(parents=True)
            src.write_bytes(b"%PDF-1.4 original bytes")
            chain = build_package_source_hash_chain(
                root=root,
                paths=[src],
                package_id="demo",
            )
            self.assertEqual(chain["status"], "ok")
            self.assertEqual(chain["entry_count"], 1)
            self.assertTrue(chain["chain_sha256"])

            src.write_bytes(b"%PDF-1.4 REWRITTEN")
            later = build_package_source_hash_chain(root=root, paths=[src])
            diff = compare_hash_chains(chain, later)
            self.assertFalse(diff["match"])
            self.assertTrue(any(item.startswith("changed:") for item in diff["mismatches"]))

    def test_escape_outside_root_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            outside = Path(tmp) / "outside.bin"
            outside.write_bytes(b"x")
            chain = build_package_source_hash_chain(root=root, paths=[outside])
            self.assertEqual(chain["status"], "incomplete")
            self.assertTrue(chain["escaped_paths"])


class MeasureCsvAc1Tests(unittest.TestCase):
    def test_template_csv_reports_ac1(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        csv_path = (
            repo / "samples" / "benchmarks" / "detection-precision" / "adjudication-template.csv"
        )
        payload = measure_adjudication_csv(csv_path)
        self.assertEqual(payload["schema_version"], "1.2.0")
        self.assertIn("gwet_ac1", payload)
        self.assertIn("pass_ac1_0_60", payload)


class PreregistrationTemplateTests(unittest.TestCase):
    def test_template_json_loads(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        path = repo / "samples" / "benchmarks" / "rt001-preregistration-template.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["artifact_type"], "rt001_preregistration")
        self.assertEqual(data["metrics"]["imbalance_robust"], "gwet_ac1")


if __name__ == "__main__":
    unittest.main()
