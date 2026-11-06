"""A title-block caption pairs only with the single cell beneath it."""

from __future__ import annotations

import unittest

from aerobim.domain.stamp_caption_above import (
    PlacedLine,
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

    def test_a_measure_line_is_not_a_stamp_caption(self) -> None:
        pairs = pair_captions_above_values(
            (_line("WALL-01 thickness 250 mm", x=10, y=10, width=140),)
        )
        self.assertEqual(pairs, ())


if __name__ == "__main__":
    unittest.main()
