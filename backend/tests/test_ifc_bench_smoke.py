"""IFC-Bench smoke: countable probes + claim_level honesty."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class IfcBenchSmokeTests(unittest.TestCase):
    def test_parse_expected_number(self) -> None:
        from aerobim.tools.run_ifc_bench_smoke import _parse_expected_number

        self.assertEqual(_parse_expected_number("There are four bathrooms."), 4.0)
        self.assertEqual(_parse_expected_number("There are 10 interior doors."), 10.0)
        self.assertEqual(_parse_expected_number("There are 4 bedrooms in the building."), 4.0)
        self.assertEqual(
            _parse_expected_number("The width of the door with uuid X is 1.25 m."),
            1.25,
        )
        self.assertEqual(
            _parse_expected_number(
                "The window with GUID 0otfaO0qPDAhynjJ6DmgH8 has a height of 1.735 m "
                "and a width of 1.0 m."
            ),
            1.735,
        )
        self.assertEqual(
            _parse_expected_number(
                "The width of the door with uuid 1hOSvn6df7F8_7GcBWlRGQ is 1.25 m."
            ),
            1.25,
        )
        self.assertEqual(
            _parse_expected_number(
                "The floor-to-floor height between the ground floor and the first floor is 3.1 m."
            ),
            3.1,
        )
        self.assertEqual(
            _parse_expected_number("Based on the data, two thermostats are installed."),
            2.0,
        )
        self.assertEqual(
            _parse_expected_number(
                "The model specifies 14 light fixtures: 8 pendant and 6 sconce lights."
            ),
            14.0,
        )
        self.assertEqual(
            _parse_expected_number(
                "Air Terminals by Building Storey:\n   - E00_OKRD: 35 terminals (23.6%)\n\n"
                "   Total Air Terminals: 148"
            ),
            148.0,
        )
        self.assertEqual(
            _parse_expected_number(
                "Heating System Components:\n   - Pipe Segments (914)\n\n"
                "   Total Heating Components: 1795"
            ),
            1795.0,
        )
        self.assertEqual(
            _parse_expected_number("Column Types:\n- M_W-Wide Flange-Column:W250X67: 80 columns"),
            80.0,
        )
        self.assertEqual(
            _parse_expected_number("Total Railings: 10\nRailing Types:\n- Railing: 10"),
            10.0,
        )
        self.assertEqual(
            _parse_expected_number(
                "Heating Systems: 42 systems\n\nSystem Categories:\n- Transport Systems: 38 systems"
            ),
            42.0,
        )
        self.assertIsNone(
            _parse_expected_number("I cannot calculate the number of window on the north facade.")
        )

    def test_evaluate_requires_dataset(self) -> None:
        from aerobim.tools.run_ifc_bench_smoke import evaluate_dataset

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                evaluate_dataset(Path(tmp))

    def test_path_escape_rejected(self) -> None:
        from aerobim.tools.run_ifc_bench_smoke import evaluate_dataset

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            qdir = root / "questions"
            qdir.mkdir()
            # Traversal in project component; question still matches duplex probe map
            # only if project==duplex — so inject unsafe component while keeping probe id
            # via a forged project that still triggers the probe key after map lookup:
            # force probe by using project=duplex and ifc_model with separator.
            (qdir / "ifc-bench-v1.csv").write_text(
                "id,question,answer,ifc_model,project,category\n"
                "1,How many bedrooms are there?,There are 4 bedrooms.,arc,../outside,count\n",
                encoding="utf-8",
            )
            (root / "projects").mkdir(parents=True)
            payload = evaluate_dataset(root, version="v1")
            errors = [r for r in payload["results"] if r["status"] == "error"]
            self.assertTrue(errors)
            self.assertTrue(any("unsafe" in (e.get("detail") or "") for e in errors))

    def test_live_dataset_smoke_when_present(self) -> None:
        from aerobim.tools.run_ifc_bench_smoke import evaluate_dataset, repo_root

        root = repo_root() / ".local" / "ifc-bench"
        if not (root / "questions" / "ifc-bench-v1.csv").is_file():
            self.skipTest("IFC-Bench checkout not present under .local/ifc-bench")
        payload = evaluate_dataset(root, version="v1")
        self.assertEqual(payload["claim_level"], "open_bench_only")
        self.assertFalse(payload["closes_rt001"])
        self.assertGreaterEqual(payload["summary"]["scored"], 5)
        self.assertEqual(payload["summary"]["mismatched"], 0)
        self.assertEqual(payload["summary"]["exact_match_rate_on_scored"], 1.0)
        # Round-trip JSON for evidence shape.
        raw = json.dumps(payload)
        self.assertIn("open_bench_only", raw)

    def test_live_v2_dataset_smoke_when_present(self) -> None:
        from aerobim.tools.run_ifc_bench_smoke import evaluate_dataset, repo_root

        root = repo_root() / ".local" / "ifc-bench-v2"
        if not (root / "questions" / "ifc-bench-v2.csv").is_file():
            self.skipTest("IFC-Bench v2 checkout not present under .local/ifc-bench-v2")
        payload = evaluate_dataset(root, version="v2")
        self.assertEqual(payload["claim_level"], "open_bench_only")
        self.assertFalse(payload["closes_rt001"])
        self.assertEqual(payload["benchmark"]["question_count"], 1026)
        self.assertTrue(payload["benchmark"]["questions_sha256_matches_pin"])
        self.assertGreaterEqual(payload["summary"]["scored"], 27)
        self.assertEqual(payload["summary"]["mismatched"], 0)
        self.assertLess(payload["summary"]["scored"], payload["summary"]["total_questions"])
        self.assertEqual(payload["eval_split"]["published_test_rows"], 514)
        self.assertEqual(
            payload["eval_split"]["scored_in_test"] + payload["eval_split"]["scored_in_train"],
            payload["summary"]["scored"],
        )
        breakdown = payload["summary"]["skip_breakdown"]
        self.assertGreaterEqual(breakdown["gpl_project_excluded"], 1)
        self.assertIn("first_number_on_unmapped", breakdown)
        self.assertLess(
            breakdown["how_many_unmapped_non_gpl"] + payload["summary"]["scored"],
            payload["summary"]["total_questions"],
        )
        raw = json.dumps(payload)
        self.assertIn("scored=", raw)

    def test_skip_breakdown_gpl_and_incomplete(self) -> None:
        from aerobim.tools.run_ifc_bench_smoke import evaluate_dataset

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            qdir = root / "questions"
            qdir.mkdir()
            (qdir / "ifc-bench-v2.csv").write_text(
                "id,question,ground_truth,ifc_model,project,category\n"
                "1,What railings are installed?,Total Railings: 6,arc,hitos,count\n"
                "2,How many widgets?,I cannot calculate the number.,arc,duplex,count\n"
                "3,Describe the atrium.,The atrium is glazed.,arc,duplex,nl\n",
                encoding="utf-8",
            )
            (root / "projects").mkdir(parents=True)
            payload = evaluate_dataset(root, version="v2")
        by_id = {row["question_id"]: row for row in payload["results"]}
        # skipped rows are omitted from results; use skip_breakdown
        breakdown = payload["summary"]["skip_breakdown"]
        self.assertEqual(payload["summary"]["total_questions"], 3)
        self.assertEqual(payload["summary"]["scored"], 0)
        self.assertEqual(breakdown["gpl_project_excluded"], 1)
        self.assertEqual(breakdown["incomplete_info"], 1)
        self.assertEqual(breakdown["non_numeric_gt"], 1)
        self.assertEqual(by_id, {})

    def test_docs_evidence_uses_repo_relative_dataset_root(self) -> None:
        from aerobim.tools.run_ifc_bench_smoke import _sanitize_docs_evidence, repo_root

        payload = {
            "benchmark": {"dataset_root": str(repo_root() / ".local" / "ifc-bench-v2")},
            "output_path": str(
                repo_root() / "artifacts" / "open-bench" / "ifc-bench-v2-smoke.json"
            ),
            "output_sha256": "abc",
        }
        docs = _sanitize_docs_evidence(payload)
        self.assertEqual(docs["benchmark"]["dataset_root"], ".local/ifc-bench-v2")
        self.assertNotIn("output_path", docs)
        self.assertEqual(docs["output_sha256"], "abc")


if __name__ == "__main__":
    unittest.main()
