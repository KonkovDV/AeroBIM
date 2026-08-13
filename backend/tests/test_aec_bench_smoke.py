"""AEC-Bench gold inventory + null-always-clean baseline."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.tools.run_aec_bench_smoke import classify_gold_task, inventory_gold, repo_root


class AecBenchGoldTests(unittest.TestCase):
    def test_classify_broken_clean_and_submittal(self) -> None:
        self.assertEqual(classify_gold_task({"variant": "broken", "defects": [{}]}), "has_issue")
        self.assertEqual(classify_gold_task({"variant": "clean", "defects": []}), "clean")
        self.assertEqual(classify_gold_task({"variant": "navigation"}), "qa")
        self.assertEqual(
            classify_gold_task({"expected_determination": "rejected", "variant": "broken"}),
            "has_issue",
        )
        self.assertEqual(
            classify_gold_task({"expected_determination": "approved"}),
            "clean",
        )

    def test_inventory_on_tiny_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = root / "tasks" / "intrasheet" / "note-callout-accuracy" / "demo"
            task.mkdir(parents=True)
            (task / "gt.json").write_text(
                '{"variant": "broken", "defects": [{"defect_id": "x"}]}',
                encoding="utf-8",
            )
            payload = inventory_gold(root)
        self.assertEqual(payload["gt_files"], 1)
        self.assertEqual(payload["null_always_clean"]["false_positive"], 1)
        self.assertEqual(payload["null_always_clean"]["true_negative"], 0)
        self.assertEqual(payload["null_always_clean"]["false_pass_rate_on_labeled"], 1.0)

    def test_live_checkout_when_present(self) -> None:
        root = repo_root() / ".local" / "aec-bench"
        if not (root / "tasks").is_dir():
            self.skipTest("AEC-Bench checkout not present under .local/aec-bench")
        payload = inventory_gold(root)
        self.assertEqual(payload["gt_files"], 196)
        self.assertEqual(payload["status"], "RUN")
        labeled = payload["null_always_clean"]["labeled_compliance_tasks"]
        self.assertGreaterEqual(labeled, 180)
        self.assertGreater(
            payload["null_always_clean"]["false_positive"],
            payload["null_always_clean"]["true_negative"],
        )
        self.assertEqual(
            labeled,
            payload["null_always_clean"]["false_positive"]
            + payload["null_always_clean"]["true_negative"],
        )


if __name__ == "__main__":
    unittest.main()
