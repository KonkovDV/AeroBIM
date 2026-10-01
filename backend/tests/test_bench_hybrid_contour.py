"""Hybrid AI P3 bench: deterministic contour invariants on synthetic cases (no external output).

Прогоняет стенд ``bench_hybrid_contour`` на зафиксированном синтетическом наборе и
проверяет инварианты (без сети/модели): внешний выход только для PUBLIC; нет утечки
сырых значений; локальное восстановление совпадает и не работает для чужого tenant;
результат verdict-neutral. Задержку не проверяем (зависит от окружения).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.tools.bench_hybrid_contour import load_cases, run_bench

_CASES = (
    Path(__file__).resolve().parents[2]
    / "samples"
    / "benchmarks"
    / "hybrid-contour"
    / "cases-synthetic.json"
)


class BenchHybridContourTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = run_bench(load_cases(_CASES))
        self.summary = self.report["summary"]

    def test_external_egress_only_for_public(self) -> None:
        self.assertTrue(self.summary["external_only_for_public"])

    def test_no_cross_tenant_restore_leak(self) -> None:
        self.assertEqual(self.summary["cross_tenant_restore_leaks"], 0)

    def test_no_raw_value_leaks(self) -> None:
        self.assertEqual(self.summary["raw_value_leaks"], 0)

    def test_restore_fidelity_is_perfect(self) -> None:
        self.assertEqual(self.summary["restore_fidelity"], 1.0)
        self.assertGreater(self.summary["restore_total"], 0)  # actually exercised tokens

    def test_flow_is_verdict_neutral(self) -> None:
        self.assertTrue(self.summary["verdict_impact_all_none"])

    def test_case_mix_is_non_vacuous(self) -> None:
        self.assertEqual(self.summary["external_cases"], 1)
        statuses = {row["route_status"] for row in self.report["rows"]}
        self.assertIn("blocked", statuses)
        self.assertIn("human_review", statuses)


if __name__ == "__main__":
    unittest.main()
