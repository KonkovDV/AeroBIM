from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.domain.models import DrawingSource
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer


class StructuredDrawingAnalyzerTests(unittest.TestCase):
    def test_analyze_parses_pipe_separated_annotations_with_problem_zone(self) -> None:
        analyzer = StructuredDrawingAnalyzer()

        annotations = analyzer.analyze(
            DrawingSource(
                text="ANN-001|A-101|WALL-01|thickness|150|mm|1|10|20|100|50"
            )
        )

        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].target_ref, "WALL-01")
        self.assertEqual(annotations[0].measure_name, "thickness")
        self.assertEqual(annotations[0].observed_value, "150")
        self.assertIsNotNone(annotations[0].problem_zone)
        self.assertEqual(annotations[0].problem_zone.sheet_id, "A-101")


if __name__ == "__main__":
    unittest.main()