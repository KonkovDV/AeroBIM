"""RT-001 dual-rater protocol rehearsal: simulated passes, humans stay zero."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.rt001_dual_rater_simulation import (
    CSV_REL,
    EVIDENCE_MD_REL,
    MIN_UNITS,
    RATER_A,
    RATER_B,
    Rt001DualRaterSimulationError,
    assemble_rt001_dual_rater_simulation,
    csv_records,
    rehearsal_units,
    render_adjudication_csv,
    require_honest_rt001_dual_rater_simulation,
    verdict_a,
    verdict_b,
)
from aerobim.domain.rt_blocker_volumes import assemble_rt_blocker_volumes
from aerobim.tools.measure_adjudicator_agreement import measure_adjudication_csv

REPO_ROOT = Path(__file__).resolve().parents[2]


class Rt001DualRaterSimulationTests(unittest.TestCase):
    def test_same_pack_two_policies_humans_stay_zero(self) -> None:
        payload = assemble_rt001_dual_rater_simulation(REPO_ROOT)
        self.assertEqual(payload["checkpoint"], CHECKPOINT)
        self.assertFalse(payload["closes_rt001"])
        self.assertFalse(payload["precision_claim_publishable"])
        self.assertEqual(payload["corpus_kind"], "synthetic")
        self.assertEqual(payload["independent_human_raters"], 0)
        self.assertFalse(payload["llm_counts_as_rater"])
        self.assertEqual(payload["simulated_independent_passes"], 2)
        self.assertEqual(payload["b_protocol_rehearsal"], "CLOSED")
        self.assertEqual(payload["b_criterion_dual_rater"], "OPEN")
        self.assertGreaterEqual(payload["n"], MIN_UNITS)
        self.assertLessEqual(payload["n"], 30)
        self.assertGreaterEqual(float(payload["cohens_kappa"]), 0.60)
        self.assertLess(float(payload["cohens_kappa"]), 1.0)
        self.assertGreaterEqual(float(payload["krippendorff_alpha"]), 0.67)
        self.assertGreaterEqual(float(payload["gwet_ac1"]), 0.60)
        self.assertFalse(payload["rater_a"]["human"])
        self.assertFalse(payload["rater_b"]["human"])
        self.assertFalse(payload["rater_a"]["llm"])
        self.assertFalse(payload["rater_b"]["llm"])
        self.assertGreaterEqual(int(payload["disagreement_count"]), 1)
        units = rehearsal_units(REPO_ROOT)
        ids = [unit.finding_id for unit in units]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(any(verdict_a(unit) != verdict_b(unit) for unit in units))

    def test_csv_is_two_rows_per_unit_for_the_agreement_tool(self) -> None:
        units = rehearsal_units(REPO_ROOT)
        records = csv_records(units)
        self.assertEqual(len(records), 2 * len(units))
        raters = {row["adjudicator_id"] for row in records}
        self.assertEqual(raters, {RATER_A, RATER_B})
        csv_text = render_adjudication_csv(records)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "adjudication.csv"
            path.write_text(csv_text, encoding="utf-8")
            measured = measure_adjudication_csv(path)
        self.assertEqual(measured["adjudicator_count"], 2)
        self.assertEqual(measured["paired_items"], len(units))
        domain = assemble_rt001_dual_rater_simulation(REPO_ROOT)
        self.assertAlmostEqual(
            float(measured["cohens_kappa"]), float(domain["cohens_kappa"]), places=2
        )

    def test_inventing_humans_is_rejected(self) -> None:
        payload = assemble_rt001_dual_rater_simulation(REPO_ROOT)
        dirty = dict(payload)
        dirty["independent_human_raters"] = 2
        with self.assertRaises(Rt001DualRaterSimulationError):
            require_honest_rt001_dual_rater_simulation(dirty)
        dirty = dict(payload)
        dirty["llm_counts_as_rater"] = True
        with self.assertRaises(Rt001DualRaterSimulationError):
            require_honest_rt001_dual_rater_simulation(dirty)
        dirty = dict(payload)
        dirty["b_criterion_dual_rater"] = "CLOSED"
        with self.assertRaises(Rt001DualRaterSimulationError):
            require_honest_rt001_dual_rater_simulation(dirty)
        dirty = dict(payload)
        dirty["closes_rt001"] = True
        with self.assertRaises(Rt001DualRaterSimulationError):
            require_honest_rt001_dual_rater_simulation(dirty)

    def test_volumes_and_readme_keep_human_residual_open(self) -> None:
        volumes = assemble_rt_blocker_volumes(REPO_ROOT)
        self.assertEqual(volumes["RT-001"]["b_protocol_rehearsal"], "CLOSED")
        self.assertEqual(volumes["RT-001"]["b_criterion_dual_rater"], "OPEN")
        self.assertEqual(volumes["RT-001"]["independent_human_raters"], 0)
        self.assertFalse(volumes["closes_rt001"])
        for name in ("README.md", "README.ru.md"):
            text = (REPO_ROOT / name).read_text(encoding="utf-8")
            self.assertIn("b_protocol_rehearsal", text)
            self.assertIn("RT-001b", text)

    def test_committed_csv_matches_live_render(self) -> None:
        path = REPO_ROOT / CSV_REL
        self.assertTrue(path.is_file())
        live = render_adjudication_csv(csv_records(rehearsal_units(REPO_ROOT)))
        self.assertEqual(path.read_text(encoding="utf-8"), live)
        path = REPO_ROOT / EVIDENCE_MD_REL
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("independent_human_raters: 0", text)
        self.assertIn("closes_rt001: false", text)
        self.assertIn("sim-rater-a", text)
        self.assertNotIn("independent_human_raters: 2", text)


if __name__ == "__main__":
    unittest.main()
