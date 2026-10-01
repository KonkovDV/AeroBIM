"""Pass 13 honesty lock — remark schema, three gates, bSI layers, SP63 demo."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.live_tree_triage import TRIAGE_ROWS
from aerobim.domain.rase_sp63_demo import (
    HJELSETH_NISBET_URL,
    IDS_1_0_FINAL,
    SP63_COVER_CLAUSE,
    SP63_COVER_RULE_ID,
    rase_four_roles_from_cover_rule,
)

_REPO = Path(__file__).resolve().parents[2]

PASS13_KILL_IDS = (
    "RT-GATE-90",
    "RT-SP63-APPR",
    "RT-BSI-REPL",
    "RT-REMARK-SHAPE",
)

PASS13_FORBIDDEN_PHRASES = (
    "заменяем валидатор buildingsmart",
    "шаблон сп 63 утверждён заказчиком",
    "aerobim replaces the bsi validation service",
)

LAYERS_REL = "docs/quality/VALIDATION_LAYERS_BSI_IDS_ENGINE_2026.md"
RASE_REL = "docs/quality/RASE_SP63_COVER_DEMO_2026.md"
SP63_REL = "samples/rule-packs/sp63-cover-template.json"

LAYERS_NEEDLES = (
    "does not check project-specific, national-specific, organization-specific",
    "совместимость не замена",
    "совместимость не сертификация",
    "information delivery specification",
    "engineering content",
)

RASE_NEEDLES = (
    "hjelseth",
    "itc.scix.net/paper/w78-2011-paper-45",
    "8.3 (template)",
    "not sp 63 table 8.1",
    "customer_approved",
    "ids 1.0",
    "2024-06-01",
    "norm_source",
    "rase_elements",
)


class Pass13HonestyLockTests(unittest.TestCase):
    def test_pass13_kill_ids_exist(self) -> None:
        by_id = {row["id"]: row for row in TRIAGE_ROWS}
        for row_id in PASS13_KILL_IDS:
            self.assertIn(row_id, by_id)
            self.assertEqual(by_id[row_id]["verdict"], "KILL")
            self.assertTrue(by_id[row_id]["brake"])

    def test_pass13_phrases_are_in_wording_ssot(self) -> None:
        payload = json.loads(
            (_REPO / "audit" / "claims_forbidden_wording.json").read_text(encoding="utf-8")
        )
        phrases = [str(item).lower() for item in payload["forbidden_affirmative_phrases"]]
        for phrase in PASS13_FORBIDDEN_PHRASES:
            self.assertIn(phrase, phrases)

    def test_validation_layers_doc_exists(self) -> None:
        path = _REPO / LAYERS_REL
        self.assertTrue(path.is_file(), msg=LAYERS_REL)
        text = path.read_text(encoding="utf-8").lower()
        for needle in LAYERS_NEEDLES:
            self.assertIn(needle, text, msg=needle)
        self.assertIn("запрещено", text)

    def test_rase_demo_doc_and_pack_lock(self) -> None:
        pack = json.loads((_REPO / SP63_REL).read_text(encoding="utf-8"))
        self.assertIsNone(pack.get("approval"))
        self.assertNotEqual(pack.get("status"), "customer_approved")
        rule = next(item for item in pack["rules"] if item["rule_id"] == SP63_COVER_RULE_ID)
        self.assertEqual(rule["norm_clause"], SP63_COVER_CLAUSE)
        self.assertEqual(rule["approval_status"], "synthetic")
        demo = rase_four_roles_from_cover_rule(rule)
        self.assertFalse(demo["customer_approved"])
        self.assertEqual(demo["citation_url"], HJELSETH_NISBET_URL)
        self.assertEqual(demo["ids_1_0_final"], IDS_1_0_FINAL)
        self.assertEqual(demo["A"], "IfcSlab")
        self.assertIn("table 8.1", demo["R"])

        path = _REPO / RASE_REL
        self.assertTrue(path.is_file(), msg=RASE_REL)
        text = path.read_text(encoding="utf-8").lower()
        for needle in RASE_NEEDLES:
            self.assertIn(needle, text, msg=needle)
        self.assertNotIn("10.1007/", text)
        self.assertNotIn("doi.org", text)

    def test_customer_approved_cover_rule_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            rase_four_roles_from_cover_rule(
                {
                    "rule_id": SP63_COVER_RULE_ID,
                    "norm_clause": SP63_COVER_CLAUSE,
                    "approval_status": "customer_approved",
                    "property_name": "CoveringThickness",
                    "property_set": "Pset_CoveringCommon",
                    "operator": "gte",
                    "expected_value": 20,
                    "ifc_entity": "IfcSlab",
                }
            )


if __name__ == "__main__":
    unittest.main()
