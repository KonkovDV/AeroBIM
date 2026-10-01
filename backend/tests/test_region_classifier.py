"""Region classifier: heuristic type labeling that never guesses (P1).

UNKNOWN on no match OR ambiguous tie; heuristic_confidence is not calibrated;
advisory + verdict-neutral.
"""

from __future__ import annotations

import json
import unittest

from aerobim.domain.region_classifier import (
    RegionType,
    classify_region,
)


def _t(text: str, **kwargs: object) -> RegionType:
    return classify_region(text, **kwargs).region_type  # type: ignore[arg-type]


class RegionClassifierTests(unittest.TestCase):
    def test_stamp(self) -> None:
        self.assertEqual(_t("Стадия П, Изм. Разраб."), RegionType.STAMP)

    def test_specification(self) -> None:
        self.assertEqual(_t("Спецификация\nПоз. Наименование Кол."), RegionType.SPECIFICATION)

    def test_explication(self) -> None:
        self.assertEqual(_t("Экспликация помещений"), RegionType.EXPLICATION)

    def test_section(self) -> None:
        self.assertEqual(_t("Разрез 1-1"), RegionType.SECTION)

    def test_node(self) -> None:
        self.assertEqual(_t("Узел А"), RegionType.NODE)

    def test_legend(self) -> None:
        self.assertEqual(_t("Условные обозначения"), RegionType.LEGEND)

    def test_plan(self) -> None:
        self.assertEqual(_t("План этажа на отметке 0.000"), RegionType.PLAN)

    def test_schedule(self) -> None:
        self.assertEqual(_t("Ведомость расхода стали"), RegionType.SCHEDULE)

    def test_table_structure_without_keyword(self) -> None:
        self.assertEqual(_t("прочий заголовок", has_table_structure=True), RegionType.TABLE)

    def test_dimension_chain_from_numeric_ratio(self) -> None:
        self.assertEqual(_t("100 200 300 1500", numeric_ratio=0.95), RegionType.DIMENSION_CHAIN)

    def test_no_signal_is_unknown(self) -> None:
        result = classify_region("некий свободный текст")
        self.assertEqual(result.region_type, RegionType.UNKNOWN)
        self.assertEqual(result.heuristic_confidence, 0.0)
        self.assertFalse(result.is_known())

    def test_ambiguous_tie_is_unknown_not_a_guess(self) -> None:
        result = classify_region("Разрез фасад")  # section vs facade, 1 hit each
        self.assertEqual(result.region_type, RegionType.UNKNOWN)
        # tied candidates are recorded for the expert (never silently picked)
        self.assertTrue(any("section" in term for term in result.matched_terms))
        self.assertTrue(any("facade" in term for term in result.matched_terms))

    def test_confidence_is_bounded_and_not_calibrated(self) -> None:
        result = classify_region("Спецификация\nПоз. Наименование Кол. Марка")
        self.assertTrue(0.0 < result.heuristic_confidence <= 1.0)
        self.assertTrue(result.is_known())
        self.assertIn("NOT a calibrated", result.to_dict()["note"])

    def test_to_dict_json_safe_and_verdict_neutral(self) -> None:
        record = classify_region("Узел А").to_dict()
        json.dumps(record)
        self.assertNotIn('"passed"', json.dumps(record))
        self.assertEqual(record["region_type"], "node")

    def test_substring_collisions_do_not_produce_labels(self) -> None:
        # Red Team MEDIUM: short stems must not bleed into common words.
        self.assertEqual(_t("Перегородки из гипсокартона"), RegionType.UNKNOWN)
        self.assertEqual(_t("Сталь листовая ГОСТ 19903"), RegionType.UNKNOWN)
        self.assertEqual(_t("Планировка участка"), RegionType.UNKNOWN)

    def test_both_structure_hints_is_ambiguous_unknown(self) -> None:
        # Red Team MEDIUM #1: table + numeric hints together -> tie -> UNKNOWN, not TABLE.
        result = classify_region("", has_table_structure=True, numeric_ratio=0.95)
        self.assertEqual(result.region_type, RegionType.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
