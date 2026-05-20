from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class PilotPerformanceGuardrailTests(unittest.TestCase):
    """Advisory latency guardrail for the Moscow pilot pack on developer hardware."""

    def test_pilot_moscow_pack_completes_within_advisory_budget(self) -> None:
        from aerobim.tools.benchmark_project_package import benchmark_project_package

        repo_root = Path(__file__).resolve().parents[2]
        pack_path = repo_root / "samples" / "benchmarks" / "project-package-pilot-moscow-v1.json"
        if not pack_path.exists():
            self.skipTest("Pilot Moscow manifest missing")

        with tempfile.TemporaryDirectory() as tmp:
            payload = benchmark_project_package(
                pack_path=pack_path,
                iterations=1,
                warmup_iterations=0,
                storage_dir=Path(tmp),
            )

        summary = payload.get("summary", {})
        avg_ms = float(summary.get("avg_ms", 0.0))
        # Advisory ceiling for CI/dev laptops — not a production SLA.
        self.assertGreater(avg_ms, 0.0)
        self.assertLess(avg_ms, 120_000.0, f"pilot pack avg_ms {avg_ms} exceeded advisory 120s budget")


if __name__ == "__main__":
    unittest.main()
