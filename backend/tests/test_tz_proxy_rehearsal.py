
"""Honesty lock for the Samolet-free TZ proxy rehearsal."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.errors import ClashCapabilityError
from aerobim.domain.tz_proxy_constructs import (
    construct_validity_frame,
    egrz_intake_xml_proxy,
    jurisdiction_ids_proxy,
    typical_remark_taxonomy_proxy,
    tz_row_proxy_map,
)
from aerobim.tools.run_tz_proxy_rehearsal import build_payload, moexp_live_pointer

REPO_ROOT = Path(__file__).resolve().parents[2]


class ConstructValidityFrameTests(unittest.TestCase):
    def test_frame_keeps_blockers_open_and_names_messick(self) -> None:
        frame = construct_validity_frame()
        self.assertFalse(frame["closes_rt001"])
        self.assertFalse(frame["closes_rt002"])
        self.assertFalse(frame["closes_rt003"])
        self.assertEqual(frame["checkpoint"], CHECKPOINT)
        self.assertIn("external", frame["aspects"])
        self.assertIn("Messick", str(frame["theory"]))

    def test_taxonomy_is_coverage_not_precision(self) -> None:
        taxonomy = typical_remark_taxonomy_proxy()
        self.assertEqual(taxonomy["claim_level"], "coverage_map_only")
        self.assertFalse(taxonomy["closes_rt001"])
        catalogs = {row["id"]: row for row in taxonomy["catalogs"]}
        self.assertEqual(catalogs["kirov-kr"]["n"], 24)
        self.assertEqual(catalogs["kirov-kr"]["detectable"], 4)
        self.assertEqual(len(catalogs["kirov-kr"]["detectable_openers"]), 4)
        self.assertEqual(catalogs["mordovia-vk-3kv2024"]["detectable"], 4)

    def test_jurisdiction_pointer_is_not_samolet(self) -> None:
        pointer = jurisdiction_ids_proxy()
        self.assertFalse(pointer["closes_rt002"])
        self.assertFalse(pointer["customer_signed"])
        self.assertFalse(pointer["samolet_alias"])
        self.assertIsNone(pointer["approval"])
        self.assertEqual(pointer["iso19650_role"], "jurisdiction_eir_like")

    def test_tz_rows_do_not_promote_blocked_status_to_done(self) -> None:
        rows = tz_row_proxy_map()
        self.assertEqual(rows["TR-11"]["status"], "partial")
        self.assertEqual(rows["TR-15"]["status"], "not_verified")
        self.assertEqual(rows["accuracy_protocol"]["status"], "blocked")
        self.assertNotEqual(rows["TR-11"]["status"], "done")
        self.assertNotEqual(rows["TR-15"]["status"], "done")

    def test_egrz_intake_proxy_does_not_close_rt001(self) -> None:
        proxy = egrz_intake_xml_proxy()
        self.assertEqual(proxy["claim_level"], "egrz_intake_precheck")
        self.assertFalse(proxy["closes_rt001"])
        self.assertEqual(proxy["stale_kinds"], [])
        self.assertIn("explanatory_note", proxy["sanitize_loadable_kinds"])


class JurisdictionPointerFileTests(unittest.TestCase):
    def test_checked_in_pointer_cannot_be_read_as_customer_approved(self) -> None:
        path = REPO_ROOT / "samples" / "ids" / "moexp" / "jurisdiction-profile-pointer.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "draft")
        self.assertIsNone(data["approval"])
        self.assertFalse(data["closes_rt002"])
        self.assertFalse(data["customer_signed"])
        self.assertFalse(data["samolet_alias"])
        self.assertIn("not-samolet-profile", data["claim_labels"])
        self.assertIsNone(data["customer_pack_hash"])
        self.assertEqual(data["hash_kind"], "jurisdiction_tree_not_customer_pack")
        from aerobim.domain.norm_pack_hash import compute_directory_tree_hash

        pack = REPO_ROOT / str(data["ids_pack_rel"])
        self.assertEqual(data["jurisdiction_tree_hash"], compute_directory_tree_hash(pack))

    def test_checked_in_moscow_and_spb_pointers_cannot_be_samolet(self) -> None:
        from aerobim.domain.norm_pack_hash import compute_directory_tree_hash

        for rel in (
            "samples/ids/moscow-agr/jurisdiction-profile-pointer.json",
            "samples/ids/spbexp/jurisdiction-profile-pointer.json",
        ):
            data = json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))
            self.assertFalse(data["closes_rt002"])
            self.assertFalse(data["customer_signed"])
            self.assertFalse(data["samolet_alias"])
            self.assertIsNone(data["approval"])
            self.assertIsNone(data["customer_pack_hash"])
            self.assertEqual(data["hash_kind"], "jurisdiction_tree_not_customer_pack")
            pack = REPO_ROOT / str(data["ids_pack_rel"])
            self.assertEqual(data["jurisdiction_tree_hash"], compute_directory_tree_hash(pack))


class TzProxyRehearsalPayloadTests(unittest.TestCase):
    def test_payload_honesty_without_opening_duplex(self) -> None:
        with (
            patch(
                "aerobim.tools.run_tz_proxy_rehearsal.IfcClashDetector.detect",
                side_effect=ClashCapabilityError("skipped", "IfcClash unavailable: test"),
            ),
            patch(
                "aerobim.tools.run_tz_proxy_rehearsal.IfcClashDetector.detect_between",
                side_effect=ClashCapabilityError("skipped", "IfcClash unavailable: test"),
            ),
        ):
            payload = build_payload(repo=REPO_ROOT, include_open_federated=False)
        self.assertFalse(payload["closes_rt001"])
        self.assertFalse(payload["closes_rt002"])
        self.assertFalse(payload["closes_rt003"])
        self.assertEqual(payload["checkpoint"], CHECKPOINT)
        runs = {row["label"]: row for row in payload["rt003_geometric_clash"]["runs"]}
        self.assertEqual(runs["planted_overlapping_boxes"]["status"], "SKIPPED")
        self.assertEqual(runs["planted_federated_crossing_walls"]["status"], "SKIPPED")
        self.assertEqual(runs["planted_federated_pipe_vs_wall"]["status"], "SKIPPED")
        self.assertEqual(runs["duplex_arc_vs_mep"]["status"], "SKIPPED")
        self.assertEqual(payload["rt003_geometric_clash"]["mep_system_clash"], "NOT_VERIFIED")
        ids = payload["rt002_jurisdiction_ids"]
        self.assertGreaterEqual(int(ids["ids_file_count"]), 24)
        self.assertEqual(ids["specification_count"], 389)
        self.assertFalse(ids["customer_signed"])
        self.assertIsNone(ids["customer_pack_hash"])
        self.assertIsNone(ids["approval"])
        self.assertEqual(len(ids["jurisdiction_tree_hash"]), 64)
        packs = payload["rt002_public_ids_packs"]
        self.assertEqual(len(packs), 3)
        self.assertTrue(all(row["closes_rt002"] is False for row in packs))
        intake = payload["rt001_egrz_intake_xml"]
        self.assertFalse(intake["closes_rt001"])
        self.assertEqual(intake["claim_level"], "egrz_intake_precheck")
        self.assertEqual(
            intake["loadable_kinds"],
            ["conclusion", "survey_assignment", "survey_report"],
        )
        self.assertEqual(intake["stale_kinds"], [])
        self.assertIn("explanatory_note", intake["sanitize_loadable_kinds"])

    def test_moexp_pointer_reads_coverage_summary(self) -> None:
        pointer = moexp_live_pointer(REPO_ROOT)
        self.assertGreaterEqual(int(pointer["ids_file_count"]), 24)
        self.assertEqual(pointer["specification_count"], 389)
        self.assertFalse(pointer["closes_rt002"])

    def test_include_open_federated_does_not_mark_rt003_closed(self) -> None:
        with (
            patch(
                "aerobim.tools.run_tz_proxy_rehearsal.IfcClashDetector.detect",
                return_value=[],
            ),
            patch(
                "aerobim.tools.run_tz_proxy_rehearsal.IfcClashDetector.detect_between",
                side_effect=ClashCapabilityError("skipped", "not installed"),
            ),
        ):
            payload = build_payload(repo=REPO_ROOT, include_open_federated=True)
        self.assertFalse(payload["closes_rt003"])
        self.assertEqual(payload["rt003_geometric_clash"]["mep_system_clash"], "NOT_VERIFIED")

    def test_write_stays_in_artifacts_by_default(self) -> None:
        from aerobim.tools.run_tz_proxy_rehearsal import main as rehearsal_main

        with (
            patch(
                "aerobim.tools.run_tz_proxy_rehearsal.IfcClashDetector.detect",
                side_effect=ClashCapabilityError("skipped", "test"),
            ),
            patch(
                "aerobim.tools.run_tz_proxy_rehearsal.IfcClashDetector.detect_between",
                side_effect=ClashCapabilityError("skipped", "test"),
            ),
            patch(
                "aerobim.tools.run_tz_proxy_rehearsal.write_payload",
            ) as writer,
        ):
            code = rehearsal_main([])
        self.assertEqual(code, 0)
        self.assertEqual(writer.call_count, 1)
        out = Path(writer.call_args.kwargs["artifacts_json"])
        self.assertEqual(out.name, "latest.json")
        self.assertEqual(out.parent.name, "tz-proxy-rehearsal")
        self.assertEqual(out.parent.parent.name, "artifacts")


class PlantedFederatedClashTests(unittest.TestCase):
    def test_crossing_wall_pair_is_in_repo(self) -> None:
        self.assertTrue((REPO_ROOT / "samples" / "ifc" / "clash-federated-box-a.ifc").is_file())
        self.assertTrue((REPO_ROOT / "samples" / "ifc" / "clash-federated-box-b.ifc").is_file())
        self.assertTrue((REPO_ROOT / "samples" / "ifc" / "clash-federated-pipe-b.ifc").is_file())

    def test_ifcclash_finds_planted_federated_intersection(self) -> None:
        import importlib.util

        if importlib.util.find_spec("ifcclash") is None:
            self.skipTest("ifcclash extra not installed")
        from aerobim.tools.run_tz_proxy_rehearsal import run_planted_federated_clash

        row = run_planted_federated_clash(REPO_ROOT)
        self.assertEqual(row["status"], "RUN")
        self.assertGreaterEqual(int(row["clash_count"]), 1)
        self.assertFalse(row["closes_rt003"])
        self.assertEqual(row["mep_system_clash"], "NOT_VERIFIED")

    def test_ifcclash_finds_planted_pipe_vs_wall(self) -> None:
        import importlib.util

        if importlib.util.find_spec("ifcclash") is None:
            self.skipTest("ifcclash extra not installed")
        from aerobim.tools.run_tz_proxy_rehearsal import run_planted_federated_pipe_clash

        row = run_planted_federated_pipe_clash(REPO_ROOT)
        self.assertEqual(row["status"], "RUN")
        self.assertGreaterEqual(int(row["clash_count"]), 1)
        self.assertFalse(row["closes_rt003"])
        self.assertEqual(row["mep_system_clash"], "NOT_VERIFIED")
        self.assertFalse(row["geometry_verified"])


class OpenFederatedDuplexTests(unittest.TestCase):
    def test_duplex_run_does_not_close_rt003(self) -> None:
        import importlib.util

        from aerobim.tools.run_tz_proxy_rehearsal import (
            DUPLEX_ARC_REL,
            DUPLEX_MEP_REL,
            run_federated_duplex,
        )

        arc = REPO_ROOT / DUPLEX_ARC_REL
        mep = REPO_ROOT / DUPLEX_MEP_REL
        if not arc.is_file() or not mep.is_file():
            self.skipTest("IFC-Bench duplex not on disk")
        if importlib.util.find_spec("ifcclash") is None:
            self.skipTest("ifcclash extra not installed")
        row = run_federated_duplex(REPO_ROOT)
        self.assertEqual(row["status"], "RUN")
        self.assertGreaterEqual(int(row["clash_count"]), 1)
        self.assertFalse(row["closes_rt003"])
        self.assertEqual(row["mep_system_clash"], "NOT_VERIFIED")
        self.assertFalse(row["geometry_verified"])
        self.assertFalse(row.get("customer_federated_ifc", False))


class Rt001SyntheticFreezeTests(unittest.TestCase):
    def test_preregistration_freeze_is_synthetic_and_open(self) -> None:
        path = (
            REPO_ROOT
            / "samples"
            / "benchmarks"
            / "rt001-preregistration-synthetic-freeze-2026-08-14.json"
        )
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "FROZEN_ON_SYNTHETIC")
        self.assertEqual(data["corpus_kind"], "synthetic")
        self.assertFalse(data["closes_rt001"])
        self.assertEqual(data["checkpoint"], CHECKPOINT)
        self.assertFalse(data["raters"]["llm_counts_as_rater"])
        self.assertEqual(data["raters"]["independent_human_raters"], 0)
        self.assertFalse(data["metrics"]["measured_on_this_freeze"])


class DuplexEvidencePinTests(unittest.TestCase):
    def test_duplex_pin_keeps_rt003_open(self) -> None:
        path = REPO_ROOT / "docs" / "evidence" / "federated-clash-duplex-2026-08.json"
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(data["closes_rt003"])
        self.assertEqual(data["mep_system_clash"], "NOT_VERIFIED")
        self.assertFalse(data["customer_federated_ifc"])
        self.assertFalse(data["signed_scope"])
        self.assertEqual(data["checkpoint"], CHECKPOINT)
