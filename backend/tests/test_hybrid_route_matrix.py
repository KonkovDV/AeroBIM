"""Hybrid AI P2: full route matrix — 100% нет неразрешённого внешнего выхода (Задача 10 #1).

Прогоняет всю матрицу (вид × цель × задача) через classify -> decide_route ->
ModelRouter и проверяет инвариант безопасности: внешний выход (external egress)
возможен ТОЛЬКО для PUBLIC-маршрута (класс PUBLIC + цель PUBLIC + public_masked +
public-tier); чувствительные классы и неизвестный заказчик наружу не выходят никогда.
Плюс воспроизводимость: матрица совпадает с зафиксированным evidence-артефактом.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.tools.export_hybrid_route_matrix import build_route_matrix

_ARTIFACT = (
    Path(__file__).resolve().parents[2]
    / "audit"
    / "evidence"
    / "hybrid-route-matrix-2026-07-29.json"
)
_SENSITIVE = {"confidential", "restricted", "secret"}


class HybridRouteMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.matrix = build_route_matrix()

    def test_external_egress_only_for_public_route(self) -> None:
        for row in self.matrix["rows"]:
            if row["external"]:
                self.assertEqual(row["classification"], "public", row)
                self.assertEqual(row["target"], "public", row)
                self.assertEqual(row["route_status"], "public_masked", row)
                self.assertEqual(row["model_tier"], "public", row)

    def test_sensitive_classes_never_egress(self) -> None:
        for row in self.matrix["rows"]:
            if row["classification"] in _SENSITIVE:
                self.assertFalse(row["external"], row)

    def test_unknown_tenant_never_egress(self) -> None:
        for row in self.matrix["unknown_tenant"]:
            self.assertEqual(row["route_status"], "blocked", row)
            self.assertFalse(row["external"], row)

    def test_summary_invariants(self) -> None:
        summary = self.matrix["summary"]
        self.assertTrue(summary["external_only_for_public_route"])
        self.assertEqual(summary["unknown_tenant_external_cells"], 0)
        self.assertGreater(summary["total_cells"], 0)

    def test_matrix_is_reproducible_vs_committed_artifact(self) -> None:
        self.assertTrue(_ARTIFACT.exists(), "route-matrix evidence artifact is missing")
        committed = json.loads(_ARTIFACT.read_text(encoding="utf-8"))
        # Regenerate on intentional change: python -m aerobim.tools.export_hybrid_route_matrix
        self.assertEqual(self.matrix, committed)


if __name__ == "__main__":
    unittest.main()
