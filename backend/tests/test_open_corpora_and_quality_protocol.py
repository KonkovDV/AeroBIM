"""WP-06 / WP-07 foundation tests — synthetic counts and pin verification."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.compute_quality_protocol_stats import (
    INTERIM_CONFIRMED_FINDING_RATE_TARGET,
    build_quality_protocol_stats,
    compute_precision_recall_wilson,
    plan_sample_size,
)
from aerobim.tools.compute_quality_protocol_stats import (
    main as quality_main,
)
from aerobim.tools.run_open_corpora_profiles import (
    CLAIM_BOUNDARY,
    all_pins_ok,
    default_profiles_dir,
    repo_root,
    run_all_profiles,
    run_smoke,
    verify_regression_pins,
)

PROFILES = default_profiles_dir()


class QualityProtocolStatsTests(unittest.TestCase):
    def test_wilson_precision_recall_synthetic_counts(self) -> None:
        # Textbook Wilson (5/10) ≈ (0.2366, 0.7634) reused for precision TP=5 FP=5.
        report = compute_precision_recall_wilson(
            true_positives=5,
            false_positives=5,
            false_negatives=2,
            confidence=0.95,
        )
        precision = report["precision"]
        recall = report["recall"]
        assert isinstance(precision, dict)
        assert isinstance(recall, dict)
        self.assertTrue(precision["defined"])
        self.assertTrue(recall["defined"])
        self.assertAlmostEqual(float(precision["point"]), 0.5)
        self.assertAlmostEqual(float(precision["lower"]), 0.2366, places=3)
        self.assertAlmostEqual(float(precision["upper"]), 0.7634, places=3)
        self.assertAlmostEqual(float(recall["point"]), 5 / 7, places=6)
        self.assertEqual(report["interim_confirmed_finding_rate_target"], 0.60)
        self.assertFalse(report["demonstrates_interim_target"])
        self.assertFalse(report["demonstrates_interim_target_publishable"])

    def test_undefined_precision_when_no_detections(self) -> None:
        report = compute_precision_recall_wilson(
            true_positives=0,
            false_positives=0,
            false_negatives=3,
        )
        self.assertFalse(report["precision"]["defined"])
        self.assertTrue(report["recall"]["defined"])

    def test_sample_size_planner_matches_wilson_halfwidth(self) -> None:
        plan = plan_sample_size(expected_p=0.75, margin=0.08, confidence=0.95)
        self.assertTrue(90 <= int(plan["required_n"]) <= 130)
        preview = plan["preview_at_expected_p"]
        assert isinstance(preview, dict)
        self.assertLessEqual(float(preview["half_width"]), 0.08)

    def test_build_artifact_combines_counts_and_plan(self) -> None:
        artifact = build_quality_protocol_stats(
            true_positives=83,
            false_positives=28,
            false_negatives=10,
            expected_p=0.75,
            margin=0.08,
            confidence=0.95,
        )
        self.assertEqual(artifact["artifact_type"], "quality_protocol_stats")
        self.assertIn("RT-001", artifact["claim_boundary"])
        self.assertEqual(
            artifact["interim_confirmed_finding_rate_target"],
            INTERIM_CONFIRMED_FINDING_RATE_TARGET,
        )
        self.assertIn("evaluate_ranking_quality", artifact["ranking_quality_reference"]["tool"])
        wilson = artifact["wilson_precision_recall"]
        self.assertTrue(wilson["precision"]["defined"])
        # 83/(83+28)=0.7477… lower Wilson should clear 0.60 at this n.
        self.assertTrue(wilson["demonstrates_interim_target"])
        self.assertEqual(
            artifact["sample_size_plan"]["required_n"],
            plan_sample_size(expected_p=0.75, margin=0.08)["required_n"],
        )

    def test_cli_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "stats.json"
            code = quality_main(
                [
                    "--tp",
                    "10",
                    "--fp",
                    "2",
                    "--fn",
                    "1",
                    "--expected-p",
                    "0.7",
                    "--margin",
                    "0.1",
                    "--output",
                    str(out),
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["artifact_type"], "quality_protocol_stats")


class OpenCorporaProfilesTests(unittest.TestCase):
    def test_regression_profile_documents_honest_count(self) -> None:
        profile = json.loads((PROFILES / "regression.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["honest_case_count"], len(profile["cases"]))
        self.assertLess(profile["honest_case_count"], 250)
        self.assertIn("not", profile["target_case_count_note"].lower())
        self.assertIn("product accuracy", profile["claim_boundary"].lower())

    def test_smoke_verifies_pins(self) -> None:
        artifact = run_smoke(repo=repo_root(), profiles_dir=PROFILES)
        self.assertTrue(artifact["pins_ok"])
        self.assertEqual(artifact["honest_regression_case_count"], 7)
        self.assertIn("NOT product accuracy", artifact["claim_boundary"])

    def test_regression_pins_match_files(self) -> None:
        profile = json.loads((PROFILES / "regression.json").read_text(encoding="utf-8"))
        pins = verify_regression_pins(profile, repo=repo_root())
        self.assertTrue(all_pins_ok(pins))

    def test_run_all_profiles_smoke_writes_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "artifacts"
            artifact = run_all_profiles(
                repo=repo_root(),
                profiles_dir=PROFILES,
                output_dir=out_dir,
                mode="smoke",
            )
            self.assertEqual(artifact["mode"], "smoke")
            self.assertTrue(artifact["pins_ok"])
            self.assertTrue((out_dir / "open-corpora-smoke.json").is_file())
            self.assertIn("output_sha256", artifact)
            self.assertEqual(CLAIM_BOUNDARY, artifact["claim_boundary"])

    def test_manifest_lists_three_profiles(self) -> None:
        manifest = json.loads(
            (repo_root() / "samples/benchmarks/open-corpora/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        kinds = {row["kind"] for row in manifest["profiles"]}
        self.assertEqual(kinds, {"regression", "pilot_approx", "load"})
        self.assertIn("NOT product accuracy", manifest["claim_boundary"])


if __name__ == "__main__":
    unittest.main()
