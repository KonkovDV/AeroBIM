"""inject_defects mutates files below the validator; same seed is stable."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.tools.inject_defects import inject_defects

_MINI_IFC = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('mini.ifc','2026-08-24T00:00:00',('AeroBIM'),('AeroBIM'),'ifc','ifc','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('0x1',$,'P',$,$,$,$,$,$);
#2=IFCBUILDINGSTOREY('0x2',$,'Level 1',$,$,$,$,$,.ELEMENT.,0.0);
#3=IFCWALL('0x3',$,'W1',$,$,$,$,$,$);
#4=IFCSIUNIT(*,.LENGTHUNIT.,.MILLI.,.METRE.);
#5=IFCQUANTITYAREA('GrossFloorArea',$,$,12.5,$);
ENDSEC;
END-ISO-10303-21;
"""


class InjectDefectsTests(unittest.TestCase):
    def _seed_pack(self, root: Path) -> Path:
        pack = root / "clean"
        pack.mkdir()
        (pack / "model.ifc").write_text(_MINI_IFC, encoding="utf-8")
        (pack / "sheet.txt").write_text("PD area 12.5\nRD area 12.5\n", encoding="utf-8")
        (pack / "tz.txt").write_text("brief rooms 4\n", encoding="utf-8")
        (pack / "calc.txt").write_text("note 10.0\n", encoding="utf-8")
        return pack

    def test_same_seed_same_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pack = self._seed_pack(root)
            first = inject_defects(pack, root / "a", seed=20260824)
            second = inject_defects(pack, root / "b", seed=20260824)
            self.assertEqual(first["seed"], 20260824)
            self.assertFalse(first["calls_aerobim_api"])
            self.assertTrue(first["injects_below_validator"])
            self.assertIn("Recall is not measured", first["claim_boundary"])
            self.assertEqual(
                [{k: v for k, v in row.items() if k != "locator"} for row in first["variants"]],
                [{k: v for k, v in row.items() if k != "locator"} for row in second["variants"]],
            )
            left = root / "a" / "area_mismatch" / "model.ifc"
            right = root / "b" / "area_mismatch" / "model.ifc"
            self.assertEqual(left.read_bytes(), right.read_bytes())
            applied = [row for row in first["variants"] if row["class"] != "CONTROL"]
            self.assertTrue(any(row["applied"] for row in applied))

    def test_control_is_byte_identical_to_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pack = self._seed_pack(root)
            inject_defects(pack, root / "out", seed=1, classes=("CONTROL",))
            source = (pack / "model.ifc").read_bytes()
            control = (root / "out" / "control" / "model.ifc").read_bytes()
            self.assertEqual(source, control)

    def test_area_mismatch_changes_quantity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pack = self._seed_pack(root)
            inject_defects(pack, root / "out", seed=7, classes=("AREA_MISMATCH",))
            mutated = (root / "out" / "area_mismatch" / "model.ifc").read_text(encoding="utf-8")
            self.assertNotIn("12.5", mutated.split("IFCQUANTITYAREA", 1)[-1][:80])

    def test_city_agr_examples_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            blocked = root / "moscow-agr-examples" / "ifc"
            blocked.mkdir(parents=True)
            (blocked / "model.ifc").write_text(_MINI_IFC, encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                inject_defects(blocked, root / "out", seed=1)
            self.assertIn("not a clean PD pack", str(ctx.exception))

    def test_nested_output_inside_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pack = self._seed_pack(root)
            with self.assertRaises(ValueError) as ctx:
                inject_defects(pack, pack / "out", seed=1, classes=("CONTROL",))
            self.assertIn("must not nest", str(ctx.exception))
            self.assertTrue((pack / "model.ifc").is_file())

    def test_same_tree_as_output_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            pack = self._seed_pack(Path(temporary_directory))
            with self.assertRaises(ValueError) as ctx:
                inject_defects(pack, pack, seed=1, classes=("CONTROL",))
            self.assertIn("must not be the source tree", str(ctx.exception))

    def test_customer_tree_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            customer = root / "samples" / "customer" / "pack"
            customer.mkdir(parents=True)
            (customer / "model.ifc").write_text(_MINI_IFC, encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                inject_defects(customer, root / "out", seed=1, classes=("CONTROL",))
            self.assertIn("customer trees", str(ctx.exception))

    def test_owner_files_tree_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            owner = root / "AeroBIM" / "files" / "pack"
            owner.mkdir(parents=True)
            (owner / "model.ifc").write_text(_MINI_IFC, encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                inject_defects(owner, root / "out", seed=1, classes=("CONTROL",))
            self.assertIn("files/", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
