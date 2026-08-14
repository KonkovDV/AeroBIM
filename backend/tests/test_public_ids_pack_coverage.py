"""Honesty + inventory for public jurisdiction IDS packs (not Samolet)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.tz_proxy_constructs import (
    moscow_agr_ids_proxy,
    public_jurisdiction_ids_packs,
    spbexp_ids_proxy,
)
from aerobim.tools.export_moexp_ids_coverage import (
    KIND_CLASSIFICATION,
    classify_ids_kind,
    discover_ids,
)

REPO = Path(__file__).resolve().parents[2]


class PublicJurisdictionPackTests(unittest.TestCase):
    def test_three_packs_all_keep_rt002_open(self) -> None:
        packs = public_jurisdiction_ids_packs()
        self.assertEqual(len(packs), 3)
        ids = {row["profile_id"] for row in packs}
        self.assertEqual(
            ids,
            {"MOEXP-GAU-IDS", "MOSCOW-AGR-DGP-IDS", "SPBEXP-GAU-CGE-IDS"},
        )
        for row in packs:
            self.assertFalse(row["closes_rt002"])
            self.assertFalse(row["customer_signed"])
            self.assertFalse(row["samolet_alias"])
            self.assertIsNone(row["approval"])
            self.assertEqual(row["legal_force"], "not_npa")

    def test_moscow_agr_ids_on_disk(self) -> None:
        files = discover_ids(REPO / "samples" / "ids" / "moscow-agr" / "pack")
        self.assertEqual(len(files), 4)
        self.assertEqual(
            classify_ids_kind("Классификация_элементов_ЦИМ_МССК_5_0_1_1.ids"),
            KIND_CLASSIFICATION,
        )
        pointer = json.loads(
            (
                REPO / "samples" / "ids" / "moscow-agr" / "jurisdiction-profile-pointer.json"
            ).read_text(encoding="utf-8")
        )
        self.assertFalse(pointer["closes_rt002"])
        self.assertEqual(pointer["profile_id"], moscow_agr_ids_proxy()["profile_id"])

    def test_spbexp_ids_on_disk(self) -> None:
        files = discover_ids(REPO / "samples" / "ids" / "spbexp" / "pack")
        self.assertEqual(len(files), 22)
        pointer = json.loads(
            (REPO / "samples" / "ids" / "spbexp" / "jurisdiction-profile-pointer.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(pointer["closes_rt002"])
        self.assertEqual(pointer["profile_id"], spbexp_ids_proxy()["profile_id"])

    def test_dgp_xml_artifacts_present(self) -> None:
        dgp = REPO / "samples" / "agr" / "dgp"
        self.assertTrue((dgp / "AGR_TEO.xml").is_file())
        self.assertTrue((dgp / "Vedomost_AGR.xml").is_file())
        self.assertTrue((dgp / "Vedomost_AGR_VED_NEW.xsd").is_file())
        source = (dgp / "SOURCE.md").read_text(encoding="utf-8")
        self.assertIn("Does not close RT-002", source)
        self.assertIn("different documents", source)

    def test_coverage_artifacts_keep_rt002_open(self) -> None:
        for stem in (
            "norm-pack-moscow-agr-coverage-2026-08",
            "norm-pack-spbexp-coverage-2026-08",
        ):
            data = json.loads(
                (REPO / "docs" / "evidence" / f"{stem}.json").read_text(encoding="utf-8")
            )
            self.assertFalse(data["closes_rt002_customer_profile"])
            self.assertFalse(data.get("samolet_alias"))
            self.assertFalse(data.get("customer_signed"))


if __name__ == "__main__":
    unittest.main()
