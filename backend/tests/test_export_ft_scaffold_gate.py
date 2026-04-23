from __future__ import annotations

import unittest

from aerobim.tools.export_ft_scaffold_gate import build_ft_scaffold_gate_report


class ExportFtScaffoldGateTests(unittest.TestCase):
    def test_gate_passes_when_all_checks_are_green(self) -> None:
        report = build_ft_scaffold_gate_report(
            command_checks=[
                {
                    "command": "python llm/train/smoke_train.py",
                    "passed": True,
                    "exit_code": 0,
                    "duration_ms": 10,
                    "output_summary": "ok",
                }
            ],
            criteria=[
                {
                    "name": "train_smoke_entrypoint",
                    "passed": True,
                    "details": "ok",
                }
            ],
        )

        self.assertTrue(report["gate_passed"])

    def test_gate_fails_when_any_criterion_fails(self) -> None:
        report = build_ft_scaffold_gate_report(
            command_checks=[
                {
                    "command": "python llm/train/smoke_train.py",
                    "passed": True,
                    "exit_code": 0,
                    "duration_ms": 10,
                    "output_summary": "ok",
                }
            ],
            criteria=[
                {
                    "name": "train_smoke_entrypoint",
                    "passed": False,
                    "details": "missing",
                }
            ],
        )

        self.assertFalse(report["gate_passed"])


if __name__ == "__main__":
    unittest.main()
