"""Region-restricted smoke — offline orchestration + cache-replay + NOT_RUN tests.

Only the model call is faked; the layout plan, real PyMuPDF crop, grounding and
cache are exercised for real. No network.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.domain.models import DrawingRegionRef, DrawingSource
from aerobim.infrastructure.adapters.caching_vlm_reader import (
    CachingVlmReader,
    FilesystemVlmResponseStore,
)
from aerobim.infrastructure.adapters.vlm_advisory_client import VlmReadResult
from aerobim.infrastructure.adapters.pymupdf_region_cropper import PyMuPDFRegionCropper
from aerobim.infrastructure.adapters.region_restricted_vlm_pipeline import (
    RegionRestrictedVlmPipeline,
)
from aerobim.tools.vlm_region_smoke import build_region_smoke_report, main

_OBS = {
    "readable": True,
    "observations": [
        {
            "kind": "designation",
            "raw_value": "Ст-1",
            "bbox_rel": [0.1, 0.1, 0.4, 0.3],
            "confidence": 0.9,
        }
    ],
}


def _make_pdf(path: Path) -> None:
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page(width=600, height=400)
    page.insert_text((60, 60), "AR-01 Ст-1")
    doc.save(str(path))
    doc.close()


def _source(tmp: str) -> DrawingSource:
    path = Path(tmp) / "sheet.pdf"
    _make_pdf(path)
    return DrawingSource(path=path, sheet_id="AR-01")


class _FakeDetector:
    def detect(self, path: Path, *, sheet_id: str | None = None) -> list[DrawingRegionRef]:
        return [
            DrawingRegionRef(
                sheet_id="AR-01",
                bbox_xyxy=(0.05, 0.05, 0.40, 0.30),
                confidence=0.9,
                modality="detector",
                layout_role="content",
                coordinate_system="normalized-0-1",
            )
        ]


class _CountingReader:
    def __init__(self) -> None:
        self.calls = 0

    def read_region(
        self, image_bytes: bytes, *, media_type: str, sheet_id: str, region_id: str, prompt: str
    ) -> VlmReadResult:
        self.calls += 1
        return VlmReadResult(content=_OBS, usage={}, determinism_basis="live")


class _FixedCropper:
    def crop(self, source: DrawingSource, *, bbox_xyxy: tuple[float, float, float, float]):
        return (b"\x89PNG-fixed-region-bytes", "image/png")


def _pipeline(reader: object, cropper: object) -> RegionRestrictedVlmPipeline:
    return RegionRestrictedVlmPipeline(
        region_detector=_FakeDetector(),
        reader=reader,  # type: ignore[arg-type]
        cropper=cropper,  # type: ignore[arg-type]
        ready=True,
    )


class RegionSmokeReportTests(unittest.TestCase):
    def test_report_ok_with_real_crop(self) -> None:
        # Real PyMuPDF crop of a generated PDF; only the model is faked.
        reader = _CountingReader()
        with tempfile.TemporaryDirectory() as tmp:
            report = build_region_smoke_report(
                _pipeline(reader, PyMuPDFRegionCropper(dpi=72, coordinate_system="normalized-0-1")),
                _source(tmp),
            )
        self.assertEqual(report["status"], "roundtrip_ok")
        self.assertEqual(reader.calls, 1)
        self.assertEqual(report["regions_detected"], 1)
        self.assertEqual(report["regions_planned"], 1)
        self.assertEqual(report["regions_read"], 1)
        self.assertEqual(report["regions_truncated"], 0)
        self.assertTrue(report["region_plan_sha256"])
        self.assertEqual(report["reads"][0]["observations"], 1)
        self.assertEqual(report["reads"][0]["determinism_basis"], "live")
        self.assertTrue(report["reads"][0]["crop_sha256"])  # real crop hashed
        self.assertIn("NOT a quality PASS", report["claim_boundary"])

    def test_cache_replay_second_run_avoids_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp) / "cache"
            source = _source(tmp)
            inner1 = _CountingReader()
            caching1 = CachingVlmReader(
                inner1, FilesystemVlmResponseStore(cache_dir), model="kimi-k3"
            )
            first = build_region_smoke_report(_pipeline(caching1, _FixedCropper()), source)
            self.assertEqual(inner1.calls, 1)
            self.assertEqual(first["reads"][0]["determinism_basis"], "live")

            inner2 = _CountingReader()
            caching2 = CachingVlmReader(
                inner2, FilesystemVlmResponseStore(cache_dir), model="kimi-k3"
            )
            second = build_region_smoke_report(_pipeline(caching2, _FixedCropper()), source)
            self.assertEqual(inner2.calls, 0)  # replayed from cache
            self.assertEqual(second["reads"][0]["determinism_basis"], "vlm_cache_replay")

    def test_main_not_run_without_credentials(self) -> None:
        with patch.dict(os.environ, {"AEROBIM_VLM_API_BASE_URL": "", "AEROBIM_VLM_API_KEY": ""}):
            exit_code = main(["--image", "nonexistent.png"])
        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
