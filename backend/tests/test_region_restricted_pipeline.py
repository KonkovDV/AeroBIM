"""§3 layers 0-2 — region-restricted VLM orchestration tests (offline, fakes)."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.domain.models import DrawingRegionRef, DrawingSource
from aerobim.domain.region_read_plan import plan_region_reads
from aerobim.infrastructure.adapters.kimi_k3_advisory_client import (
    KimiAdvisoryError,
    KimiReadResult,
)
from aerobim.infrastructure.adapters.region_restricted_vlm_pipeline import (
    RegionRestrictedVlmPipeline,
)

_OBS = {
    "readable": True,
    "observations": [
        {
            "kind": "designation",
            "raw_value": "ст 1",
            "bbox_rel": [0.1, 0.1, 0.4, 0.3],
            "confidence": 0.9,
        }
    ],
}


def _regions(n: int) -> list[DrawingRegionRef]:
    return [
        DrawingRegionRef(
            sheet_id="AR-01",
            bbox_xyxy=(0.0, 0.0, 10.0 * (i + 1), 10.0),
            confidence=0.9,
            modality="detector",
        )
        for i in range(n)
    ]


class _FakeDetector:
    def __init__(self, n: int) -> None:
        self._n = n

    def detect(self, path: Path, *, sheet_id: str | None = None) -> list[DrawingRegionRef]:
        return _regions(self._n)


class _FakeCropper:
    def __init__(self) -> None:
        self.calls = 0

    def crop(self, source: DrawingSource, *, bbox_xyxy: tuple[float, float, float, float]):
        self.calls += 1
        return (b"\x89PNG crop", "image/png")


class _FakeReader:
    def __init__(self, content: dict | None = None, raise_exc: Exception | None = None) -> None:
        self.calls = 0
        self._content = content if content is not None else _OBS
        self._raise = raise_exc

    def read_region(
        self, image_bytes: bytes, *, media_type: str, sheet_id: str, region_id: str, prompt: str
    ) -> KimiReadResult:
        self.calls += 1
        if self._raise is not None:
            raise self._raise
        return KimiReadResult(content=self._content, usage={}, determinism_basis="test")


def _source() -> DrawingSource:
    return DrawingSource(path=Path("plan.png"), sheet_id="AR-01")


class RegionReadPlanTests(unittest.TestCase):
    def test_text_layer_skips_vlm(self) -> None:
        plan = plan_region_reads(text_layer_present=True, regions=_regions(3))
        self.assertTrue(plan.skip_vlm)
        self.assertEqual(plan.tasks, ())
        self.assertIn("Layer 0", plan.reason)

    def test_no_regions_skips(self) -> None:
        plan = plan_region_reads(text_layer_present=False, regions=[])
        self.assertTrue(plan.skip_vlm)

    def test_regions_become_tasks(self) -> None:
        plan = plan_region_reads(text_layer_present=False, regions=_regions(2))
        self.assertFalse(plan.skip_vlm)
        self.assertEqual(len(plan.tasks), 2)


class RegionRestrictedPipelineTests(unittest.TestCase):
    def _pipeline(self, *, reader, cropper, detector, ready=True, max_regions=24):  # noqa: ANN001
        return RegionRestrictedVlmPipeline(
            region_detector=detector,
            reader=reader,
            cropper=cropper,
            ready=ready,
            max_regions=max_regions,
        )

    def test_text_layer_present_does_not_call_vlm(self) -> None:
        reader = _FakeReader()
        pipe = self._pipeline(reader=reader, cropper=_FakeCropper(), detector=_FakeDetector(3))
        result = pipe.read_sheet(_source(), text_layer_present=True)
        self.assertTrue(result.skipped_vlm)
        self.assertEqual(reader.calls, 0)

    def test_no_cropper_forbids_whole_sheet_read(self) -> None:
        reader = _FakeReader()
        pipe = self._pipeline(reader=reader, cropper=None, detector=_FakeDetector(3))
        result = pipe.read_sheet(_source(), text_layer_present=False)
        self.assertTrue(result.skipped_vlm)
        self.assertEqual(reader.calls, 0)
        self.assertIn("whole-sheet read is forbidden", result.reason)

    def test_not_ready_skips(self) -> None:
        reader = _FakeReader()
        pipe = self._pipeline(
            reader=reader, cropper=_FakeCropper(), detector=_FakeDetector(3), ready=False
        )
        result = pipe.read_sheet(_source(), text_layer_present=False)
        self.assertTrue(result.skipped_vlm)
        self.assertEqual(reader.calls, 0)

    def test_one_call_per_region_always_degraded(self) -> None:
        reader = _FakeReader()
        cropper = _FakeCropper()
        pipe = self._pipeline(reader=reader, cropper=cropper, detector=_FakeDetector(2))
        result = pipe.read_sheet(_source(), text_layer_present=False)
        self.assertFalse(result.skipped_vlm)
        self.assertEqual(reader.calls, 2)
        self.assertEqual(cropper.calls, 2)
        self.assertEqual(len(result.reads), 2)
        self.assertTrue(result.degraded)
        self.assertTrue(all(r.degraded for r in result.reads))
        self.assertEqual(result.reads[0].observations[0].normalized_value, "СТ1")

    def test_max_regions_budget_caps_calls(self) -> None:
        reader = _FakeReader()
        pipe = self._pipeline(
            reader=reader, cropper=_FakeCropper(), detector=_FakeDetector(5), max_regions=1
        )
        result = pipe.read_sheet(_source(), text_layer_present=False)
        self.assertEqual(reader.calls, 1)
        self.assertEqual(len(result.reads), 1)

    def test_reader_error_degrades_that_region_not_the_sheet(self) -> None:
        reader = _FakeReader(raise_exc=KimiAdvisoryError("boom", reason_code="TRUNCATED"))
        pipe = self._pipeline(reader=reader, cropper=_FakeCropper(), detector=_FakeDetector(1))
        result = pipe.read_sheet(_source(), text_layer_present=False)
        self.assertFalse(result.skipped_vlm)
        self.assertEqual(len(result.reads), 1)
        self.assertTrue(result.reads[0].degraded)
        self.assertEqual(result.reads[0].observations, ())
        self.assertIn("TRUNCATED", result.reads[0].reason or "")

    def test_schema_deviation_degrades_region(self) -> None:
        reader = _FakeReader(content={"no_observations": True})
        pipe = self._pipeline(reader=reader, cropper=_FakeCropper(), detector=_FakeDetector(1))
        result = pipe.read_sheet(_source(), text_layer_present=False)
        self.assertEqual(result.reads[0].observations, ())
        self.assertIn("schema deviation", result.reads[0].reason or "")


if __name__ == "__main__":
    unittest.main()
