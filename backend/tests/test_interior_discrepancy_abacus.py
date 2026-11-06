"""The interior abacus is a shared vocabulary, not a verdict and not a customer album."""

from __future__ import annotations

import unittest

from aerobim.domain.interior_discrepancy_abacus import (
    INTERIOR_DISCREPANCY_CLASSES,
    INTERIOR_PHASE_GATES,
    writes_summary_passed,
)


class InteriorDiscrepancyAbacusTests(unittest.TestCase):
    def test_twelve_classes_and_five_gates_are_stable(self) -> None:
        codes = [row.code for row in INTERIOR_DISCREPANCY_CLASSES]
        self.assertEqual(codes, [f"D{index:02d}" for index in range(1, 13)])
        self.assertEqual([gate.code for gate in INTERIOR_PHASE_GATES], list("ABCDE"))

    def test_partner_export_is_named_where_the_engine_has_no_source(self) -> None:
        by_code = {gate.code: gate for gate in INTERIOR_PHASE_GATES}
        self.assertTrue(by_code["A"].needs_partner_export)
        self.assertTrue(by_code["B"].needs_partner_export)
        self.assertTrue(by_code["E"].needs_partner_export)
        self.assertFalse(by_code["C"].needs_partner_export)
        self.assertFalse(by_code["D"].needs_partner_export)

    def test_catalog_does_not_write_the_pack_flag(self) -> None:
        self.assertFalse(writes_summary_passed())
        self.assertTrue(INTERIOR_PHASE_GATES)
        self.assertFalse(any(gate.rules_signed for gate in INTERIOR_PHASE_GATES))

    def test_examples_carry_no_customer_album(self) -> None:
        blob = " ".join(row.didactic_example for row in INTERIOR_DISCREPANCY_CLASSES)
        self.assertNotIn("DIMORA", blob)
        self.assertNotIn("₽", blob)
