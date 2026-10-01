"""AEC-Bench gold inventory + null-always-clean baseline."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.tools.run_aec_bench_smoke import (
    _sanitize_docs_evidence,
    _secret_present,
    assert_prefetch_url,
    classify_gold_task,
    inventory_gold,
    prefetch_instance,
    repo_root,
)


class AecBenchGoldTests(unittest.TestCase):
    def test_secret_present_reads_process_env(self) -> None:
        with patch.dict("os.environ", {"AEROBIM_LLM_API_KEY": "x"}, clear=False):
            self.assertTrue(_secret_present("AEROBIM_LLM_API_KEY"))

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


class AecBenchPrefetchJailTests(unittest.TestCase):
    def test_prefetch_url_https_allowlist(self) -> None:
        allowed = "https://nomic-public-data.com/data/aec-bench-v1/sheet.pdf"
        self.assertEqual(assert_prefetch_url(allowed), allowed)
        with self.assertRaises(ValueError):
            assert_prefetch_url("file:///C:/Windows/win.ini")
        with self.assertRaises(ValueError):
            assert_prefetch_url("http://nomic-public-data.com/x.pdf")
        with self.assertRaises(ValueError):
            assert_prefetch_url("https://evil.example/x.pdf")
        with self.assertRaises(ValueError):
            assert_prefetch_url("https://nomic-public-data.com:8443/x.pdf")
        with self.assertRaises(ValueError):
            assert_prefetch_url("https://user:pass@nomic-public-data.com/x.pdf")

    def _write_manifest(self, root: Path, *, dest: str, url: str) -> None:
        env = root / "tasks" / "intrasheet" / "note-callout-accuracy" / "demo" / "environment"
        env.mkdir(parents=True)
        (env / "manifest.jsonl").write_text(
            json.dumps({"key": url, "dest": dest}) + "\n",
            encoding="utf-8",
        )

    def test_prefetch_rejects_dest_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_manifest(
                root,
                dest="../../../evil.pdf",
                url="https://nomic-public-data.com/data/aec-bench-v1/x.pdf",
            )
            with patch("aerobim.tools.run_aec_bench_smoke.safe_urlopen") as opener:
                result = prefetch_instance(
                    root,
                    scope="intrasheet",
                    family="note-callout-accuracy",
                    instance="demo",
                    timeout_s=1,
                    retries=1,
                )
            opener.assert_not_called()
            self.assertEqual(result["downloads"][0]["status"], "error")
            self.assertIn("path jail", result["downloads"][0]["detail"])
            self.assertFalse((root / "evil.pdf").is_file())

    def test_prefetch_rejects_file_url_without_fetch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_manifest(root, dest="ok.pdf", url="file:///etc/passwd")
            with patch("aerobim.tools.run_aec_bench_smoke.safe_urlopen") as opener:
                result = prefetch_instance(
                    root,
                    scope="intrasheet",
                    family="note-callout-accuracy",
                    instance="demo",
                    timeout_s=1,
                    retries=1,
                )
            opener.assert_not_called()
            self.assertEqual(result["downloads"][0]["status"], "error")
            self.assertIn("https", result["downloads"][0]["detail"])

    def test_prefetch_writes_allowlisted_body_inside_jail(self) -> None:
        class _Resp:
            def __init__(self) -> None:
                self._sent = False

            def read(self, _n: int = -1) -> bytes:
                if self._sent:
                    return b""
                self._sent = True
                return b"%PDF-1.4 fixture"

            def __enter__(self) -> _Resp:
                return self

            def __exit__(self, *_exc: object) -> bool:
                return False

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_manifest(
                root,
                dest="sheet.pdf",
                url="https://nomic-public-data.com/data/aec-bench-v1/sheet.pdf",
            )
            with patch(
                "aerobim.tools.run_aec_bench_smoke.safe_urlopen",
                return_value=_Resp(),
            ):
                result = prefetch_instance(
                    root,
                    scope="intrasheet",
                    family="note-callout-accuracy",
                    instance="demo",
                    timeout_s=1,
                    retries=1,
                )
            dest = (
                root
                / "tasks"
                / "intrasheet"
                / "note-callout-accuracy"
                / "demo"
                / "environment"
                / "sheet.pdf"
            )
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["downloads"][0]["status"], "downloaded")
            self.assertEqual(dest.read_bytes(), b"%PDF-1.4 fixture")

    def test_docs_evidence_drops_machine_fingerprint(self) -> None:
        report = {
            "benchmark": {"dataset_root": str(repo_root() / ".local" / "aec-bench")},
            "output_path": str(repo_root() / "artifacts" / "open-bench" / "aec-bench-smoke.json"),
            "agent_trial": {
                "reason": "Harbor. Yandex key present=true; do not paste.",
                "yandex_studio_key_present": True,
                "openai_key_present": True,
                "anthropic_key_present": False,
            },
        }
        docs = _sanitize_docs_evidence(report)
        self.assertEqual(docs["benchmark"]["dataset_root"], ".local/aec-bench")
        self.assertNotIn("output_path", docs)
        trial = docs["agent_trial"]
        self.assertNotIn("yandex_studio_key_present", trial)
        self.assertNotIn("openai_key_present", trial)
        self.assertNotIn("anthropic_key_present", trial)
        self.assertNotIn("Yandex key present=", trial["reason"])
        self.assertEqual(trial["credential_flags"], "omitted_from_docs_evidence")


if __name__ == "__main__":
    unittest.main()
