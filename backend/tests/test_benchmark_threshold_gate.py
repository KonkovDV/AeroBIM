from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class BenchmarkThresholdGateTests(unittest.TestCase):
    def _write_fixture(self, root: Path, rel_path: str, payload: object) -> Path:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def test_run_threshold_gate_passes_when_metrics_within_limits(self) -> None:
        from aerobim.tools.benchmark_threshold_gate import run_threshold_gate

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact_dir = root / "artifacts"
            profile_path = root / "thresholds.json"

            self._write_fixture(
                root,
                "artifacts/project-package-baseline.json",
                {
                    "pack_id": "project-package-baseline",
                    "summary": {
                        "avg_ms": 1200.0,
                        "reports_per_second": 0.833,
                    },
                },
            )
            self._write_fixture(
                root,
                "thresholds.json",
                {
                    "packs": {
                        "project-package-baseline": {
                            "max_avg_ms": 2000.0,
                            "min_reports_per_second": 0.4,
                        }
                    }
                },
            )

            result = run_threshold_gate(artifact_dir=artifact_dir, profile_path=profile_path, mode="advisory")

            self.assertTrue(result["gate_passed"])
            checks = result["checks"]
            self.assertEqual(len(checks), 1)
            self.assertEqual(checks[0]["status"], "pass")

    def test_run_threshold_gate_reports_violation(self) -> None:
        from aerobim.tools.benchmark_threshold_gate import run_threshold_gate

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact_dir = root / "artifacts"
            profile_path = root / "thresholds.json"

            self._write_fixture(
                root,
                "artifacts/project-package-baseline.json",
                {
                    "pack_id": "project-package-baseline",
                    "summary": {
                        "avg_ms": 5000.0,
                        "reports_per_second": 0.2,
                    },
                },
            )
            self._write_fixture(
                root,
                "thresholds.json",
                {
                    "packs": {
                        "project-package-baseline": {
                            "max_avg_ms": 2000.0,
                            "min_reports_per_second": 0.4,
                        }
                    }
                },
            )

            advisory = run_threshold_gate(artifact_dir=artifact_dir, profile_path=profile_path, mode="advisory")
            enforced = run_threshold_gate(artifact_dir=artifact_dir, profile_path=profile_path, mode="enforced")

            self.assertTrue(advisory["has_failure"])
            self.assertTrue(advisory["gate_passed"])
            self.assertFalse(enforced["gate_passed"])
            checks = enforced["checks"]
            self.assertEqual(checks[0]["status"], "failed")
            self.assertGreaterEqual(len(checks[0]["violations"]), 1)

    def test_run_threshold_gate_marks_missing_pack_as_failure(self) -> None:
        from aerobim.tools.benchmark_threshold_gate import run_threshold_gate

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact_dir = root / "artifacts"
            profile_path = root / "thresholds.json"

            artifact_dir.mkdir(parents=True, exist_ok=True)
            self._write_fixture(
                root,
                "thresholds.json",
                {
                    "packs": {
                        "project-package-baseline": {
                            "max_avg_ms": 2000.0,
                            "min_reports_per_second": 0.4,
                        }
                    }
                },
            )

            result = run_threshold_gate(artifact_dir=artifact_dir, profile_path=profile_path, mode="enforced")

            self.assertFalse(result["gate_passed"])
            checks = result["checks"]
            self.assertEqual(checks[0]["status"], "missing")


if __name__ == "__main__":
    unittest.main()