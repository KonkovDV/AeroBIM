"""Mentor VLM demo — dry crop honesty + Yandex credential guard (offline)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pdf_fixtures import write_text_pdf

from aerobim.domain.models import DrawingSource
from aerobim.infrastructure.adapters.heuristic_layout_region_detector import (
    HeuristicLayoutRegionDetector,
)
from aerobim.tools.run_mentor_vlm_demo import (
    _redact_model_uri,
    _resolve_credentials,
    _save_planned_crops,
    main,
)


def _make_pdf(path: Path) -> None:
    write_text_pdf(path, "WALL-01 thickness 150 mm")


class MentorVlmDemoTests(unittest.TestCase):
    def test_redact_model_uri(self) -> None:
        self.assertEqual(
            _redact_model_uri("gpt://b1gsecret/qwen3.6-35b-a3b"),
            "gpt://<folder>/qwen3.6-35b-a3b",
        )

    def test_yandex_refuses_kimi_default(self) -> None:
        os_environ = __import__("os").environ
        controlled = {k: v for k, v in os_environ.items() if not k.startswith("AEROBIM_")}
        controlled.update(
            {
                "AEROBIM_LLM_BASE_URL": "https://llm.api.cloud.yandex.net/v1",
                "AEROBIM_LLM_API_KEY": "k",
                "AEROBIM_LLM_PROVIDER": "yandex-ai-studio",
            }
        )
        with patch.dict("os.environ", controlled, clear=True):
            creds = _resolve_credentials()
        self.assertIsNotNone(creds.get("error"))
        self.assertIn("Yandex", creds["error"] or "")

    def test_planned_crops_are_cloud_safe_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "sheet.pdf"
            _make_pdf(pdf)
            out = Path(tmp) / "out"
            out.mkdir()
            source = DrawingSource(path=pdf, sheet_id="T1")
            crops = _save_planned_crops(
                source=source, out_dir=out, detector=HeuristicLayoutRegionDetector()
            )
            self.assertTrue(crops)
            roles = {c["layout_role"] for c in crops}
            self.assertEqual(roles, {"content"})
            self.assertTrue(all(c.get("egress_crop") for c in crops))
            # PII clip moves left edge off 0.0 for content prior
            self.assertGreaterEqual(crops[0]["bbox_xyxy"][0], 0.1)

    def test_dry_crop_only_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "sheet.pdf"
            _make_pdf(pdf)
            out = Path(tmp) / "artifacts"
            code = main(["--pdf", str(pdf), "--output", str(out), "--dry-crop-only"])
            self.assertEqual(code, 0)
            report = json.loads((out / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "dry_crop_only")
            self.assertTrue(report["crops"])
            self.assertTrue((out / "crops").is_dir())


if __name__ == "__main__":
    unittest.main()
