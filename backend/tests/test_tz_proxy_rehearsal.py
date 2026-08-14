"""Honesty lock for the Samolet-free TZ proxy rehearsal."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.domain.errors import ClashCapabilityError
from aerobim.domain.tz_proxy_constructs import (
    construct_validity_frame,
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
        self.assertEqual(frame["checkpoint"], "NO_GO")
        self.assertIn("external", frame["aspects"])
        self.assertIn("Messick", str(frame["theory"]))

    def test_taxonomy_is_coverage_not_precision(self) -> None:
        taxonomy = typical_remark_taxonomy_proxy()
        self.assertEqual(taxonomy["claim_level"], "coverage_map_only")
        self.assertFalse(taxonomy["closes_rt001"])
        catalogs = {row["id"]: row for row in taxonomy["catalogs"]}
        self.assertEqual(catalogs["kirov-kr"]["n"], 24)
        self.assertEqual(catalogs["kirov-kr"]["detectable"], 4)
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


class TzProxyRehearsalPayloadTests(unittest.TestCase):
    def test_payload_honesty_without_opening_duplex(self) -> None:
        with patch(
            "aerobim.tools.run_tz_proxy_rehearsal.IfcClashDetector.detect",
            side_effect=ClashCapabilityError("skipped", "IfcClash unavailable: test"),
        ):
            payload = build_payload(repo=REPO_ROOT, include_open_federated=False)
        self.assertFalse(payload["closes_rt001"])
        self.assertFalse(payload["closes_rt002"])
        self.assertFalse(payload["closes_rt003"])
        self.assertEqual(payload["checkpoint"], "NO_GO")
        runs = {row["label"]: row for row in payload["rt003_geometric_clash"]["runs"]}
        self.assertEqual(runs["planted_overlapping_boxes"]["status"], "SKIPPED")
        self.assertEqual(runs["duplex_arc_vs_mep"]["status"], "SKIPPED")
        self.assertEqual(payload["rt003_geometric_clash"]["mep_system_clash"], "NOT_VERIFIED")
        ids = payload["rt002_jurisdiction_ids"]
        self.assertGreaterEqual(int(ids["ids_file_count"]), 24)
        self.assertEqual(ids["specification_count"], 389)
        self.assertFalse(ids["customer_signed"])

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
