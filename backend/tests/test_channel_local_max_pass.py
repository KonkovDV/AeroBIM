
"""Maximum licensed Samolet-copy pass stays coverage_map_only."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.channel_local_max_pass import channel_local_max_pass_snapshot
from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.tools.pack_probe import probe_pack
from aerobim.tools.run_channel_max_pass import main as max_pass_main
from aerobim.tools.run_finding_volume import main as finding_volume_main
from aerobim.tools.scan_declared_calc_tokens import scan_declared_calc_tokens


class ChannelLocalMaxPassTests(unittest.TestCase):
    def test_snapshot_stays_no_go_and_uncertain(self) -> None:
        snap = channel_local_max_pass_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertEqual(snap["claim_level"], "coverage_map_only")
        self.assertEqual(snap["publishable_finding_count"], 0)
        self.assertFalse(snap["pack_processed"])
        self.assertFalse(snap["finding_volume_is_accuracy"])
        self.assertFalse(snap["raises_spf_default"])
        self.assertEqual(snap["customer_confirmed_patterns"], 0)
        self.assertEqual(snap["spf_analyze_cap_mib"], 256)
        self.assertEqual(len(snap["techlab_seven"]), 7)
        self.assertTrue(all(row["criterion"] == "Uncertain" for row in snap["techlab_seven"]))
        self.assertEqual(snap["owner_blocked_count"], 8)
        self.assertFalse(snap["names_in_git"])
        self.assertFalse(snap["hashes_in_git"])
        self.assertFalse(snap["uncompressed_gib_in_git"])
        self.assertEqual(snap["pack_family"]["docx_with_class_phrase"], 6)
        self.assertGreaterEqual(snap["pack_triage_kill_count"], 16)
        blob = json.dumps(snap, ensure_ascii=False)
        self.assertIn("объём находок на канале получен", blob)
        self.assertIn("Not Meets/Does-not", blob)
        self.assertNotIn("ГиБ", blob)
        self.assertNotIn("GiB", blob)

    def test_catalog_observations_stay_unconfirmed(self) -> None:
        path = (
            Path(__file__).resolve().parents[2]
            / "samples"
            / "benchmarks"
            / "samolet-typical-errors-catalog.json"
        )
        catalog = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(catalog["schema_version"], "1.4.1")
        self.assertEqual(catalog["customer_confirmed_patterns"], 0)
        notes = catalog["channel_carrier_observations"]["notes"]
        self.assertEqual(len(notes), 7)
        self.assertEqual(catalog["channel_carrier_observations"]["customer_confirmed_patterns"], 0)
        self.assertTrue(catalog["channel_carrier_observations"]["not_customer_defects"])

    def test_findings_lite_dir_cli(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            lite_dir = Path(tmp) / "runs" / "ifc-1"
            lite_dir.mkdir(parents=True)
            (lite_dir / "findings-lite.json").write_text(
                json.dumps(
                    [
                        {
                            "rule_id": "REQ-FIRE-001",
                            "target_ref": "ALL",
                            "message": "Property does not match the expected value",
                            "severity": "error",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            out = Path(tmp) / "volume.json"
            self.assertEqual(
                finding_volume_main(
                    ["--findings-lite-dir", str(Path(tmp) / "runs"), "--output", str(out)]
                ),
                0,
            )
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["total"], 1)
            self.assertEqual(payload["publishable_finding_count"], 0)
            self.assertEqual(payload["by_volume_class"]["unrestricted_eq_sample"], 1)
            self.assertEqual(
                finding_volume_main(
                    [
                        "--findings-lite-dir",
                        str(Path(tmp) / "runs"),
                        "--output",
                        str(repo / "docs" / "evidence" / "finding-volume.json"),
                    ]
                ),
                2,
            )

    def test_token_scan_counts_without_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            root.mkdir()
            (root / "note.xlsx").write_bytes(b"PK\x03\x04 concrete class B25 and B35")
            (root / "skip.dwg").write_bytes(b"AC1032")
            payload = scan_declared_calc_tokens(root)
        self.assertEqual(payload["scanned_files"], 1)
        self.assertGreaterEqual(payload["hits"]["B25"], 1)
        self.assertGreaterEqual(payload["hits"]["B35"], 1)
        self.assertFalse(payload["is_solver"])
        self.assertNotIn("note.xlsx", json.dumps(payload))

    def test_probe_skip_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            root.mkdir()
            (root / "a.ifc").write_text("ISO-10303-21;\nHEADER;\nENDSEC;", encoding="utf-8")
            rows, aggregate = probe_pack(root, compute_hash=False)
        self.assertEqual(rows[0]["sha256"], "")
        self.assertFalse(aggregate["hashes_computed"])
        self.assertFalse(aggregate["pd_filename_inventory"]["statutory_pp87"])

    def test_max_pass_cli_refuses_docs_and_writes_local(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "pack"
            pack.mkdir()
            (pack / "a.pdf").write_bytes(b"%PDF-1.4 /Font B25")
            self.assertEqual(
                max_pass_main(
                    [
                        "--pack",
                        str(pack),
                        "--out",
                        str(repo / "docs" / "evidence"),
                    ]
                ),
                2,
            )
            out = Path(tmp) / "out"
            self.assertEqual(
                max_pass_main(["--pack", str(pack), "--out", str(out), "--skip-hash"]),
                0,
            )
            combined = json.loads((out / "combined-aggregate.json").read_text(encoding="utf-8"))
            self.assertEqual(combined["checkpoint"], CHECKPOINT)
            self.assertFalse(combined["pack_processed"])
            self.assertEqual(combined["pack_file_count"], 1)
            self.assertFalse((out / "pack-local.json").exists())


if __name__ == "__main__":
    unittest.main()
