"""A title-block caption pairs only with the single cell beneath it."""

from __future__ import annotations

import unittest

from aerobim.domain.models import DrawingAnnotation, Severity
from aerobim.domain.stamp_caption_above import (
    STAMP_CAPTION_SOURCE,
    STAMP_FIELD_DISAGREE,
    PlacedLine,
    disagreeing_package_stamp_fields,
    pair_captions_above_values,
    writes_summary_passed,
)


def _line(text: str, *, x: float, y: float, width: float = 24.0, height: float = 8.0) -> PlacedLine:
    return PlacedLine(text=text, x=x, y=y, width=width, height=height)


class StampCaptionAboveTests(unittest.TestCase):
    def test_sheet_caption_takes_the_cell_beneath_it(self) -> None:
        pairs = pair_captions_above_values(
            (_line("Лист", x=10, y=10), _line("41", x=12, y=20, width=16))
        )
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0].code, "sheet")
        self.assertEqual(pairs[0].value, "41")
        self.assertFalse(writes_summary_passed())

    def test_a_neighbour_beside_the_caption_is_not_the_value(self) -> None:
        pairs = pair_captions_above_values(
            (_line("Стадия", x=10, y=10, width=30), _line("Р", x=80, y=10, width=12))
        )
        self.assertEqual(pairs, ())

    def test_two_cells_under_one_caption_are_not_guessed(self) -> None:
        pairs = pair_captions_above_values(
            (
                _line("Шифр", x=10, y=10, width=40),
                _line("А-101", x=10, y=20, width=30),
                _line("А-102", x=10, y=22, width=30),
            )
        )
        self.assertEqual(pairs, ())

    def test_two_captions_over_one_cell_are_not_guessed(self) -> None:
        pairs = pair_captions_above_values(
            (
                _line("Лист", x=10, y=4, width=20),
                _line("Стадия", x=10, y=12, width=20),
                _line("41", x=10, y=24, width=16),
            )
        )
        self.assertEqual(pairs, ())


def _stamp(code: str, value: str, sheet: str) -> DrawingAnnotation:
    return DrawingAnnotation(
        annotation_id=f"{sheet}-{code}",
        sheet_id=sheet,
        target_ref=f"STAMP-{code.upper()}",
        measure_name=code,
        observed_value=value,
        unit=None,
        source=STAMP_CAPTION_SOURCE,
    )


class PackageStampFieldTests(unittest.TestCase):
    def test_two_ciphers_are_a_warning(self) -> None:
        issues = disagreeing_package_stamp_fields(
            (_stamp("cipher", "АР-1", "A-101"), _stamp("cipher", "АР-2", "A-102"))
        )
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, STAMP_FIELD_DISAGREE)
        self.assertIs(issues[0].severity, Severity.WARNING)
        self.assertGreaterEqual(len(issues[0].evidence_refs), 2)
        self.assertFalse(writes_summary_passed())

    def test_same_cipher_and_different_sheet_numbers_are_quiet(self) -> None:
        issues = disagreeing_package_stamp_fields(
            (
                _stamp("cipher", "ар-1", "A-101"),
                _stamp("cipher", "АР-1", "A-102"),
                _stamp("sheet", "1", "A-101"),
                _stamp("sheet", "2", "A-102"),
            )
        )
        self.assertEqual(issues, [])

    def test_a_measure_line_is_not_a_stamp_caption(self) -> None:
        pairs = pair_captions_above_values(
            (_line("WALL-01 thickness 250 mm", x=10, y=10, width=140),)
        )
        self.assertEqual(pairs, ())


if __name__ == "__main__":
    unittest.main()
