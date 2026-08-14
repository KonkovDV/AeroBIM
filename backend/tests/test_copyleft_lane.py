"""Public MIT tree stays copyleft-free; Samolet-local demo may read gitignored GPLv3 IFC."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.domain.copyleft_lane import (
    GPLV3_IFC_BENCH_PROJECTS,
    local_samolet_demo_copyleft_inputs_permitted,
)
from aerobim.tools.fetch_ifc_bench_v2 import copy_local
from aerobim.tools.fetch_ifc_bench_v2 import main as fetch_main
from aerobim.tools.run_federated_mep_inventory import CANDIDATES, gplv3_local_candidates

REPO_ROOT = Path(__file__).resolve().parents[2]


class CopyleftLanePolicyTests(unittest.TestCase):
    def test_default_and_ci_refuse_copyleft_inputs(self) -> None:
        self.assertFalse(local_samolet_demo_copyleft_inputs_permitted(opted_in=False, ci=False))
        self.assertFalse(local_samolet_demo_copyleft_inputs_permitted(opted_in=True, ci=True))
        self.assertTrue(local_samolet_demo_copyleft_inputs_permitted(opted_in=True, ci=False))

    def test_gplv3_project_dirs_are_not_under_samples(self) -> None:
        samples = REPO_ROOT / "samples"
        for name in GPLV3_IFC_BENCH_PROJECTS:
            hits = [path for path in samples.rglob("*") if path.is_dir() and path.name == name]
            self.assertFalse(
                hits,
                f"GPLv3 IFC-Bench project {name!r} must stay out of samples/: {hits[:5]}",
            )

    def test_ci_workflow_does_not_opt_into_copyleft_lane(self) -> None:
        ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertNotIn("--include-gplv3", ci)
        self.assertNotIn("--samolet-demo-copyleft", ci)


class FetchCopyleftLaneTests(unittest.TestCase):
    def test_copy_can_include_gpl_when_lane_is_on(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            (src / "projects" / "duplex").mkdir(parents=True)
            (src / "projects" / "hitos").mkdir(parents=True)
            (src / "projects" / "duplex" / "arc.ifc").write_text("ok", encoding="utf-8")
            (src / "projects" / "hitos" / "arc.ifc").write_text("gpl", encoding="utf-8")
            skipped = copy_local(src, dest, excludes={"hitos"})
            included = copy_local(src, dest, excludes={"hitos"}, include_gpl=True)
        skipped_paths = {item["path"] for item in skipped}
        included_paths = {item["path"] for item in included}
        self.assertNotIn("projects/hitos/arc.ifc", skipped_paths)
        self.assertIn("projects/hitos/arc.ifc", included_paths)

    def test_fetch_refuses_gpl_without_samolet_lane(self) -> None:
        self.assertEqual(fetch_main(["--include-gplv3"]), 2)

    def test_fetch_refuses_gpl_on_ci_even_with_lane(self) -> None:
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "CI": "true"}):
            self.assertEqual(
                fetch_main(["--include-gplv3", "--samolet-demo-copyleft"]),
                2,
            )


class FederatedInventoryCopyleftLaneTests(unittest.TestCase):
    def test_default_candidates_do_not_include_gplv3_labels(self) -> None:
        labels = {label for _rel, label in CANDIDATES}
        gpl_labels = [label for label in labels if str(label).startswith("ifc_bench_gplv3_")]
        self.assertEqual(gpl_labels, [])

    def test_gpl_candidates_only_come_from_local_checkout(self) -> None:
        for rel, label in gplv3_local_candidates(REPO_ROOT):
            self.assertTrue(rel.startswith(".local/ifc-bench-v2/projects/"))
            self.assertTrue(label.startswith("ifc_bench_gplv3_"))
            self.assertFalse(rel.startswith("samples/"))


if __name__ == "__main__":
    unittest.main()
