"""Honesty lock: NPA legal-force cannot promote IDS/AGR pre-check to expertise or RT CLOSED."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.npa_legal_force import (
    AGR_EXCHANGE_LEGAL,
    AS_OF,
    DEFAULT_CONFIG_RELATIVE,
    EGRZ_INTAKE_LEGAL,
    FORCE_AGENCY_ORDER,
    FORCE_DRAFT,
    FORCE_NOT_NPA,
    FORCE_TERRITORIAL_NPA,
    IDS_PACK_LEGAL,
    MINSTROY_CIM_COMPOSITION,
    PP614_FORMATS_CITATION,
    PP878_DISAMBIGUATION,
    agr_exchange_legal_payload,
    cites_cim_composition_order_as_in_force,
    overlay_egrz_intake,
    overlay_ids_pack,
)
from aerobim.domain.tz_proxy_constructs import egrz_intake_xml_proxy, public_jurisdiction_ids_packs
from aerobim.tools.run_agr_exchange_fixture import run_manifest

REPO = Path(__file__).resolve().parents[2]
REGISTER = REPO / DEFAULT_CONFIG_RELATIVE
POINTERS = (
    REPO / "samples" / "ids" / "moexp" / "jurisdiction-profile-pointer.json",
    REPO / "samples" / "ids" / "moscow-agr" / "jurisdiction-profile-pointer.json",
    REPO / "samples" / "ids" / "spbexp" / "jurisdiction-profile-pointer.json",
)
LIVING_DOCS = (
    REPO / "docs" / "regulatory-baseline-2026.md",
    REPO / "docs" / "dwg-blocker-memo-2026-08.md",
    REPO / "docs" / "partners" / "SAMOLET_WHAT_WE_NEED_2026_07-ru.md",
)


class NpaLegalForceTests(unittest.TestCase):
    def test_minstroy_cim_composition_is_draft(self) -> None:
        self.assertEqual(MINSTROY_CIM_COMPOSITION["legal_force"], FORCE_DRAFT)
        self.assertFalse(MINSTROY_CIM_COMPOSITION["in_force_on_as_of"])
        self.assertEqual(MINSTROY_CIM_COMPOSITION["regulation_gov_id"], "155923")
        self.assertEqual(AS_OF, "2026-08-14")

    def test_pp878_egrz_is_not_radioelectronics(self) -> None:
        egrz = PP878_DISAMBIGUATION["egrz"]
        trap = PP878_DISAMBIGUATION["radioelectronics_trap"]
        self.assertEqual(egrz["date"], "2017-07-24")
        self.assertEqual(trap["date"], "2019-07-10")
        self.assertEqual(trap["not"], "egrz")
        self.assertNotEqual(egrz["instrument_id"], trap["instrument_id"])

    def test_pp614_formats_citation_rejects_rules_item_7(self) -> None:
        self.assertIn("subitems b/g/d", PP614_FORMATS_CITATION)
        self.assertIn("Do not cite Rules item 7", PP614_FORMATS_CITATION)

    def test_ids_packs_are_not_npa_and_cannot_close_rt(self) -> None:
        for profile_id, legal in IDS_PACK_LEGAL.items():
            self.assertEqual(legal["legal_force"], FORCE_NOT_NPA, profile_id)
            self.assertFalse(legal["substitutes_grk_art_49_expertise"], profile_id)
            self.assertFalse(legal["substitutes_customer_eir"], profile_id)
            self.assertFalse(legal["closes_rt002"], profile_id)

    def test_overlay_refuses_rt_close(self) -> None:
        with self.assertRaises(ValueError):
            overlay_ids_pack("MOEXP-GAU-IDS", {"closes_rt002": True})
        with self.assertRaises(ValueError):
            overlay_egrz_intake({"closes_rt001": True})

    def test_egrz_intake_is_agency_order_precheck_not_expertise(self) -> None:
        self.assertEqual(EGRZ_INTAKE_LEGAL["product_function"], "egrz_intake_precheck")
        self.assertEqual(EGRZ_INTAKE_LEGAL["legal_force_of_cited_npa"], FORCE_AGENCY_ORDER)
        self.assertEqual(EGRZ_INTAKE_LEGAL["xsd_files_legal_force"], FORCE_NOT_NPA)
        self.assertFalse(EGRZ_INTAKE_LEGAL["substitutes_grk_art_49_expertise"])
        self.assertFalse(EGRZ_INTAKE_LEGAL["substitutes_egrz_remark_corpus"])
        proxy = egrz_intake_xml_proxy()
        self.assertFalse(proxy["closes_rt001"])
        self.assertEqual(proxy["product_function"], "egrz_intake_precheck")

    def test_proxy_packs_carry_legal_force(self) -> None:
        packs = public_jurisdiction_ids_packs()
        self.assertEqual(len(packs), 3)
        for row in packs:
            self.assertEqual(row["legal_force"], FORCE_NOT_NPA)
            self.assertFalse(row["closes_rt001"])
            self.assertFalse(row["closes_rt002"])
            self.assertFalse(row["closes_rt003"])
            self.assertFalse(row["substitutes_grk_art_49_expertise"])
            self.assertFalse(row["substitutes_agr_certificate"])

    def test_checked_in_pointers_match_domain(self) -> None:
        for path in POINTERS:
            data = json.loads(path.read_text(encoding="utf-8"))
            legal = IDS_PACK_LEGAL[str(data["profile_id"])]
            self.assertEqual(data["legal_force"], legal["legal_force"])
            self.assertEqual(data["territorial_scope"], legal["territorial_scope"])
            self.assertEqual(data["instrument_id"], legal["instrument_id"])
            self.assertFalse(data["closes_rt002"])
            self.assertFalse(data["substitutes_grk_art_49_expertise"])
            self.assertFalse(data["substitutes_agr_certificate"])

    def test_json_register_mirrors_draft_and_ids_force(self) -> None:
        payload = json.loads(REGISTER.read_text(encoding="utf-8"))
        self.assertEqual(payload["as_of"], AS_OF)
        self.assertTrue(payload["not_legal_advice"])
        self.assertEqual(payload["checkpoint"], "NO_GO")
        draft = payload["minstroy_cim_composition"]
        self.assertEqual(draft["legal_force"], FORCE_DRAFT)
        self.assertFalse(draft["in_force_on_as_of"])
        bindings = payload["ids_pack_bindings"]
        for profile_id, legal in IDS_PACK_LEGAL.items():
            self.assertEqual(bindings[profile_id]["legal_force"], legal["legal_force"])
            self.assertEqual(bindings[profile_id]["territorial_scope"], legal["territorial_scope"])
        intake = payload["product_checks"]["egrz_intake_xml"]
        self.assertEqual(intake["product_function"], "egrz_intake_precheck")
        self.assertFalse(intake["closes_rt001"])
        self.assertEqual(payload["minstroy_xml_schemas"]["ecpe_pz"], "01.07")
        self.assertEqual(payload["minstroy_xml_schemas"]["listed_pz"], "01.07")
        self.assertEqual(payload["minstroy_xml_schemas"]["listed_assignment"], "01.01")
        self.assertEqual(payload["minstroy_xml_schemas"]["stale_vs_ecpe"], [])

    def test_agr_exchange_is_territorial_precheck(self) -> None:
        self.assertEqual(AGR_EXCHANGE_LEGAL["product_function"], "precheck_exchange_shape")
        self.assertEqual(AGR_EXCHANGE_LEGAL["legal_force_of_cited_npa"], FORCE_TERRITORIAL_NPA)
        self.assertEqual(AGR_EXCHANGE_LEGAL["ids_zip_legal_force"], FORCE_NOT_NPA)
        self.assertFalse(AGR_EXCHANGE_LEGAL["substitutes_agr_certificate"])
        payload = run_manifest(
            REPO / "samples" / "agr" / "exchange-fixture-manifest.json",
            root=REPO,
        )
        qual = payload["legal_qualification"]
        self.assertEqual(qual, agr_exchange_legal_payload())
        self.assertFalse(qual["substitutes_grk_art_49_expertise"])
        self.assertFalse(qual["federal_im_obligation_created"])

    def test_living_docs_do_not_cite_draft_order_as_in_force(self) -> None:
        for path in LIVING_DOCS:
            hits = cites_cim_composition_order_as_in_force(path.read_text(encoding="utf-8"))
            self.assertEqual(hits, [], msg=f"{path}: {hits}")

    def test_scanner_flags_bare_in_force_citation(self) -> None:
        bad = "ПП 331 + 614 + состав ЦИМ с 01.03.2026: модель в экспертизе."
        self.assertEqual(len(cites_cim_composition_order_as_in_force(bad)), 1)
        ok = (
            "Приказ Минстроя «состав ЦИМ к графике ПД» на 14.08.2026 — "
            "проект ID 155923, не НПА (не цитировать как «усиление с 01.03.2026»)."
        )
        self.assertEqual(cites_cim_composition_order_as_in_force(ok), [])


if __name__ == "__main__":
    unittest.main()
