"""Golden report stability on fixture baseline pack."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.run_manifest import build_run_manifest, compute_report_reproducibility_hash
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.tools.benchmark_project_package import load_benchmark_pack, repo_root

# Pinned on project-package-baseline.json @ development profile (fixture only).
# 2026-08-11 (fourth conscious refresh): mep_system_clash / engine signature after
# MEP-CLASH-001 honesty probe wiring; hash is status+engine only (not reason text).
GOLDEN_BASELINE_REPRO_HASH = "62ade6f05ddad57a541200c513f2c454ab615fa83a5592110c4a9d83e0b68595"


class GoldenReportTests(unittest.TestCase):
    def test_baseline_pack_reproducibility_hash_is_stable(self) -> None:
        repo = repo_root()
        pack_path = repo / "samples" / "benchmarks" / "project-package-baseline.json"
        if not pack_path.exists():
            self.skipTest("baseline pack missing")
        pack = load_benchmark_pack(pack_path, repo_root_path=repo)

        with tempfile.TemporaryDirectory() as tmpdir:
            settings = Settings(
                application_name="golden-test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmpdir) / "var",
                debug=True,
            )
            settings.storage_dir.mkdir(parents=True, exist_ok=True)
            uc = bootstrap_container(settings).resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)

            first = uc.execute(replace(pack.request, request_id="golden-a"))
            second = uc.execute(replace(pack.request, request_id="golden-b"))

        hash_first = compute_report_reproducibility_hash(first)
        hash_second = compute_report_reproducibility_hash(second)
        self.assertEqual(hash_first, hash_second)
        self.assertEqual(hash_first, GOLDEN_BASELINE_REPRO_HASH)

        manifest = build_run_manifest(
            first,
            request_id="golden-a",
            pack_id=pack.pack_id,
        )
        self.assertEqual(manifest.reproducibility_hash, GOLDEN_BASELINE_REPRO_HASH)
        self.assertEqual(manifest.outcome, "blocked")
        self.assertFalse(manifest.passed)
        self.assertGreater(manifest.engine_finding_count, 0)


if __name__ == "__main__":
    unittest.main()
