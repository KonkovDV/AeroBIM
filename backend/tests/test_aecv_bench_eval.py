"""AECV-Bench offline scoring helpers."""

from __future__ import annotations

import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class AecvBenchEvalTests(unittest.TestCase):
    def test_score_counts_exact_and_mape(self) -> None:
        from aerobim.tools.run_aecv_bench_eval import score_counts

        rows = score_counts(
            {"Door": 10, "Window": 8, "Space": 12, "Bedroom": 2, "Toilet": 2},
            {"Door": 10, "Window": 11, "Space": 12, "Bedroom": 2, "Toilet": 2},
        )
        by = {r.field: r for r in rows}
        self.assertTrue(by["Door"].exact_match)
        self.assertFalse(by["Window"].exact_match)
        self.assertAlmostEqual(by["Window"].abs_pct_error or 0.0, abs(8 - 11) / 11)

    def test_offline_dataset_when_present(self) -> None:
        from aerobim.tools.run_aecv_bench_eval import (
            evaluate_offline_counting,
            repo_root,
        )

        root = repo_root() / ".local" / "AECV-Bench"
        if not (root / "data").is_dir():
            self.skipTest("AECV-Bench checkout missing")
        payload = evaluate_offline_counting(root, limit=3)
        self.assertEqual(payload["plans_scored"], 3)
        self.assertGreater(len(payload["models"]), 3)
        sample = next(iter(payload["models"].values()))
        self.assertIn("macro_exact_match_rate", sample)

    def test_aggregate_includes_bias_and_zero_refusal(self) -> None:
        from aerobim.tools.run_aecv_bench_eval import FieldScore, _aggregate

        rows = [
            FieldScore("Window", 5, 8, False, abs(5 - 8) / 8),
            FieldScore("Window", 7, 10, False, abs(7 - 10) / 10),
            FieldScore("Bedroom", 0, 2, False, 1.0),
            FieldScore("Bedroom", 2, 2, True, 0.0),
        ]
        summary = _aggregate(rows)
        self.assertAlmostEqual(summary["per_field"]["Window"]["mean_bias"], -3.0)
        self.assertEqual(
            summary["per_field"]["Bedroom"]["zero_pred_when_expected_positive_n"], 1
        )
        self.assertIn("mape", summary["per_field"]["Window"])
        self.assertIsNotNone(summary.get("macro_mape"))

    def test_executive_summary_compares_to_published(self) -> None:
        from aerobim.tools.run_aecv_bench_eval import build_executive_summary

        exe = build_executive_summary(
            live={
                "provider": "yandex-ai-studio",
                "model": "gpt://x/qwen",
                "plans_attempted": 2,
                "errors": 0,
                "summary": {
                    "macro_exact_match_rate": 0.4,
                    "macro_mape": 0.3,
                    "per_field": {
                        "Door": {
                            "exact_match_rate": 0.2,
                            "mape": 0.3,
                            "mean_bias": -0.5,
                            "zero_pred_when_expected_positive_n": 0,
                            "zero_pred_when_expected_positive_rate": 0.0,
                        },
                        "Window": {
                            "exact_match_rate": 0.1,
                            "mape": 0.4,
                            "mean_bias": -2.5,
                            "zero_pred_when_expected_positive_n": 0,
                            "zero_pred_when_expected_positive_rate": 0.0,
                        },
                        "Space": {
                            "exact_match_rate": 0.1,
                            "mape": 0.3,
                            "mean_bias": 0.2,
                            "zero_pred_when_expected_positive_n": 0,
                            "zero_pred_when_expected_positive_rate": 0.0,
                        },
                        "Bedroom": {
                            "exact_match_rate": 0.8,
                            "mape": 0.1,
                            "mean_bias": 0.0,
                            "zero_pred_when_expected_positive_n": 1,
                            "zero_pred_when_expected_positive_rate": 0.2,
                        },
                        "Toilet": {
                            "exact_match_rate": 0.8,
                            "mape": 0.1,
                            "mean_bias": 0.0,
                            "zero_pred_when_expected_positive_n": 0,
                            "zero_pred_when_expected_positive_rate": 0.0,
                        },
                    },
                },
                "plans": [],
            },
            offline={
                "plans_scored": 120,
                "models": {
                    "gemini_x": {
                        "macro_exact_match_rate": 0.52,
                        "macro_mape": 0.25,
                        "per_field": {
                            "Door": {"exact_match_rate": 0.4},
                            "Window": {"exact_match_rate": 0.3},
                            "Bedroom": {"exact_match_rate": 0.8},
                        },
                    }
                },
            },
        )
        self.assertEqual(exe["claim_level"], "open_bench_only")
        self.assertAlmostEqual(
            exe["published_baseline_comparison"]["live_vs_best_published"][
                "delta_live_minus_best"
            ],
            0.4 - 0.52,
        )
        self.assertEqual(
            exe["failure_mode_contrast"]["Window"]["mean_bias"], -2.5
        )

    def test_image_mime_sniffs_webp_despite_jpg_extension(self) -> None:
        from aerobim.tools.run_aecv_bench_eval import _image_mime

        webp = b"RIFF\x20\x00\x00\x00WEBPVP8 " + b"\x00" * 16
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plan.jpg"
            path.write_bytes(webp)
            self.assertEqual(_image_mime(path), "image/webp")
            jpeg = Path(tmp) / "real.jpg"
            jpeg.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 8)
            self.assertEqual(_image_mime(jpeg), "image/jpeg")

    def test_yandex_vision_body_uses_chat_template_kwargs_not_toplevel(self) -> None:
        """Vendor rejects top-level enable_thinking (HTTP 400)."""
        from aerobim.tools.run_aecv_bench_eval import _call_openai_vision_counts

        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        captured: dict = {}

        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(
                    {
                        "choices": [
                            {
                                "message": {
                                    "content": json.dumps(
                                        {
                                            "Door": 1,
                                            "Window": 1,
                                            "Space": 1,
                                            "Bedroom": 0,
                                            "Toilet": 0,
                                        }
                                    )
                                }
                            }
                        ]
                    }
                ).encode()

        def fake_urlopen(req, timeout=0):  # noqa: ARG001
            captured["body"] = json.loads(req.data.decode())
            return _Resp()

        with tempfile.TemporaryDirectory() as tmp:
            img = Path(tmp) / "plan.png"
            img.write_bytes(png)
            with patch(
                "aerobim.tools.run_aecv_bench_eval.urllib.request.urlopen",
                fake_urlopen,
            ):
                _call_openai_vision_counts(
                    image_path=img,
                    model="gpt://folder/qwen3.6-35b-a3b",
                    api_key="test-key",
                    base_url="https://llm.api.cloud.yandex.net/v1",
                    timeout_s=5.0,
                    folder_id="folder",
                    auth_scheme="Api-Key",
                )
        body = captured["body"]
        self.assertEqual(
            body.get("chat_template_kwargs"), {"enable_thinking": False}
        )
        self.assertNotIn("enable_thinking", body)
        self.assertNotIn("extra_body", body)


if __name__ == "__main__":
    unittest.main()
