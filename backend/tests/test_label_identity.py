"""Sheet-mark identity: lookalikes and short system-mark lists."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.domain.label_identity import (
    expand_system_marks,
    labels_equivalent,
    mark_sets_overlap,
)


class LabelIdentityTests(unittest.TestCase):
    def test_steel_grade_lookalikes_match_and_case_stays(self) -> None:
        self.assertTrue(labels_equivalent("С345", "C345"))
        self.assertFalse(labels_equivalent("С345", "c345"))
        self.assertFalse(labels_equivalent("REI60", "rei60"))
        self.assertFalse(labels_equivalent("III", "Ш"))

    def test_mark_list_and_short_range_expand(self) -> None:
        self.assertEqual(expand_system_marks("В2.7,8,9"), ("В2.7", "В2.8", "В2.9"))
        self.assertEqual(expand_system_marks("B2.7, 8, 9"), ("В2.7", "В2.8", "В2.9"))
        self.assertEqual(expand_system_marks("В2.4-В2.6"), ("В2.4", "В2.5", "В2.6"))
        self.assertEqual(expand_system_marks("В2.4-6"), ("В2.4", "В2.5", "В2.6"))

    def test_grille_size_and_prose_are_not_mark_lists(self) -> None:
        self.assertEqual(expand_system_marks("П300*300"), ())
        self.assertEqual(expand_system_marks("стена В2.1"), ())
        self.assertEqual(expand_system_marks("В"), ())
        self.assertFalse(mark_sets_overlap("В2.7,8,9", "В2.1"))
        self.assertTrue(mark_sets_overlap("В2.7,8,9", "В2.8"))
