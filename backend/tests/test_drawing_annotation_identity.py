"""Stable drawing-annotation IDs (drawing-annotation-id-v2)."""

from __future__ import annotations

import math
import os
import subprocess
import sys
import unittest
from pathlib import Path

from aerobim.infrastructure.adapters.drawing_annotation_identity import (
    canonical_coord,
    drawing_annotation_digest,
    drawing_annotation_id,
)

_SRC = Path(__file__).resolve().parents[1] / "src"
_ID_KWARGS = {
    "sheet_id": "A-101",
    "page_number": 1,
    "target_ref": "WALL-01",
    "measure_name": "thickness",
    "observed_value": "250",
    "unit": "mm",
    "x": 10.0,
    "y": 20.0,
    "width": 100.0,
    "height": 40.0,
}


def _id(**overrides: object) -> str:
    payload = dict(_ID_KWARGS)
    payload.update(overrides)
    return drawing_annotation_id(**payload)  # type: ignore[arg-type]


def _digest(**overrides: object) -> str:
    payload = dict(_ID_KWARGS)
    payload.update(overrides)
    return drawing_annotation_digest(**payload)  # type: ignore[arg-type]


class DrawingAnnotationIdentityTests(unittest.TestCase):
    def test_annotation_id_is_stable_across_hash_seeds(self) -> None:
        code = (
            "from aerobim.infrastructure.adapters.drawing_annotation_identity import "
            "drawing_annotation_id\n"
            "print(drawing_annotation_id("
            'sheet_id="A-101",page_number=1,target_ref="WALL-01",'
            'measure_name="thickness",observed_value="250",unit="mm",'
            "x=10.0,y=20.0,width=100.0,height=40.0))\n"
        )
        ids: list[str] = []
        for seed in ("1", "2", "3"):
            env = os.environ.copy()
            env["PYTHONHASHSEED"] = seed
            existing = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = str(_SRC) if not existing else str(_SRC) + os.pathsep + existing
            completed = subprocess.run(
                [sys.executable, "-c", code],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            ids.append(completed.stdout.strip())
        self.assertEqual(len(ids), 3)
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(ids[1], ids[2])
        self.assertTrue(ids[0].startswith("VIS-001-"))
        self.assertEqual(_id(), ids[0])

    def test_id_changes_when_source_page_changes(self) -> None:
        self.assertNotEqual(_id(page_number=1), _id(page_number=2))

    def test_id_changes_when_rule_relevant_value_changes(self) -> None:
        self.assertNotEqual(_id(observed_value="250"), _id(observed_value="251"))

    def test_decimal_comma_and_dot_share_identity(self) -> None:
        self.assertEqual(_digest(observed_value="150,0"), _digest(observed_value="150.0"))

    def test_cyrillic_and_latin_square_metres_stay_distinct(self) -> None:
        self.assertNotEqual(_digest(unit="м²"), _digest(unit="m²"))
        self.assertNotEqual(_digest(unit="м2"), _digest(unit="м²"))

    def test_nan_inf_coords_are_json_safe_and_stable(self) -> None:
        self.assertEqual(canonical_coord(math.nan), 0.0)
        self.assertEqual(canonical_coord(math.inf), 0.0)
        self.assertEqual(_id(x=math.nan), _id(x=0.0))
        self.assertEqual(_id(x=math.inf), _id(x=0.0))

    def test_three_decimal_coords_do_not_merge_adjacent_stamps(self) -> None:
        self.assertNotEqual(_digest(x=10.000), _digest(x=10.002))

    def test_builtin_hash_is_not_used_for_ids(self) -> None:
        import inspect

        from aerobim.infrastructure.adapters import raster_drawing_analyzer as mod

        source = inspect.getsource(mod)
        self.assertNotIn("hash((", source)
        self.assertIn("drawing_annotation_id", source)


if __name__ == "__main__":
    unittest.main()
