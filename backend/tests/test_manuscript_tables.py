"""Manuscript cells copy a number only from a CI-attested, claim-leveled pin."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.manuscript_tables import (
    ManuscriptSpec,
    manuscript_cells,
    render_manuscript_markdown,
)


def _repo() -> Path:
    return Path(__file__).resolve().parents[2]


class ManuscriptTableTests(unittest.TestCase):
    def test_citable_cell_copies_the_pin_and_withheld_cells_do_not(self) -> None:
        specs = (
            ManuscriptSpec("Architecture", "Passed", "ok.json", "n"),
            ManuscriptSpec("Evaluation", "Local", "local.json", "n"),
            ManuscriptSpec("Evaluation", "Unleveled", "bare.json", "n"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "docs" / "evidence"
            evidence.mkdir(parents=True)
            (evidence / "ok.json").write_text(
                json.dumps({"attested_by": "ci", "claim_level": "fixture_only", "n": 17}),
                encoding="utf-8",
            )
            (evidence / "local.json").write_text(
                json.dumps({"attested_by": "local", "claim_level": "fixture_only", "n": 91}),
                encoding="utf-8",
            )
            (evidence / "bare.json").write_text(
                json.dumps(
                    {
                        "attestation": {"attested_by": "ci"},
                        "n": 83,
                    }
                ),
                encoding="utf-8",
            )
            # Remap pins onto the temp tree by rewriting spec paths.
            remapped = tuple(
                ManuscriptSpec(
                    spec.section, spec.label, f"docs/evidence/{Path(spec.pin).name}", spec.pointer
                )
                for spec in specs
            )
            cells = manuscript_cells(root, remapped)
            text = render_manuscript_markdown(cells)
        self.assertIn("17", text)
        self.assertNotIn("91", text)
        self.assertNotIn("83", text)
        self.assertIn("withheld", text)
        by_label = {cell.spec.label: cell for cell in cells}
        self.assertTrue(by_label["Passed"].citable)
        self.assertEqual(by_label["Passed"].value, 17)
        self.assertFalse(by_label["Local"].citable)
        self.assertIsNone(by_label["Local"].value)
        self.assertFalse(by_label["Unleveled"].citable)

    def test_live_pins_stay_withheld_until_both_gates_pass(self) -> None:
        repo = _repo()
        cells = manuscript_cells(repo)
        self.assertTrue(cells)
        arch = [cell for cell in cells if cell.spec.section == "Architecture"]
        eval_cells = [cell for cell in cells if cell.spec.section == "Evaluation"]
        self.assertTrue(arch)
        self.assertTrue(eval_cells)
        self.assertTrue(all(not cell.citable and cell.value is None for cell in eval_cells))
        baseline = json.loads(
            (repo / "docs" / "evidence" / "runtime-baseline-latest.json").read_text(
                encoding="utf-8"
            )
        )
        baseline_leveled = bool(str(baseline.get("claim_level") or "").strip())
        if baseline_leveled:
            self.assertTrue(all(cell.citable and cell.value is not None for cell in arch))
        else:
            self.assertTrue(all(not cell.citable and cell.value is None for cell in arch))
        text = render_manuscript_markdown(cells)
        self.assertNotIn("0.125", text)
        self.assertIn("attested_by is None", text)
