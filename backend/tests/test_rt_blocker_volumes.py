"""RT-001/002/003 measurement volumes close on substitutes; residuals stay open."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.kt3_without_customer import assemble_kt3_without_customer
from aerobim.domain.rt_blocker_volumes import (
    VOLUME_RE_SCOPE_DATE,
    RtBlockerVolumeError,
    assemble_rt_blocker_volumes,
    require_honest_rt_blocker_volumes,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class RtBlockerVolumeTests(unittest.TestCase):
    def test_live_repo_closes_measurement_volumes_only(self) -> None:
        payload = assemble_rt_blocker_volumes(REPO_ROOT)
        self.assertEqual(payload["schema_version"], "1.5.0")
        self.assertEqual(payload["checkpoint"], CHECKPOINT)
        self.assertEqual(payload["go_kind"], "regulatory_measurement_mvp")
        self.assertFalse(payload["customer_go"])
        self.assertEqual(payload["volume_re_scope_date"], VOLUME_RE_SCOPE_DATE)
        self.assertFalse(payload["closes_rt001"])
        self.assertFalse(payload["closes_rt002"])
        self.assertFalse(payload["closes_rt003"])
        self.assertFalse(payload["precision_claim_publishable"])
        self.assertFalse(payload["mep_delivered"])
        self.assertEqual(payload["RT-001"]["a_content_pairing"], "CLOSED")
        self.assertEqual(payload["RT-001"]["b_criterion_dual_rater"], "OPEN")
        self.assertEqual(payload["RT-001"]["b_protocol_rehearsal"], "CLOSED")
        self.assertEqual(payload["RT-001"]["b1_protocol_rehearsal"], "CLOSED")
        self.assertEqual(payload["RT-001"]["b2_criterion_dual_rater"], "OPEN")
        self.assertEqual(payload["volume_speech_map"]["RT-001b"], "b2_criterion_dual_rater")
        self.assertEqual(payload["volume_speech_map"]["RT-003c"], "b3_mep_system_clash")
        self.assertIn("RT-001b CLOSED", payload["undifferentiated_letter_closed_forbidden"])
        self.assertIn("RT-003c CLOSED", payload["undifferentiated_letter_closed_forbidden"])
        self.assertGreaterEqual(float(payload["RT-001"]["dual_rater_kappa"]), 0.60)
        self.assertEqual(payload["RT-001"]["c_customer_corpus"], "OPEN")
        self.assertEqual(payload["RT-001"]["independent_human_raters"], 0)
        self.assertTrue(payload["RT-001"]["open_benches_are_different_contour"])
        self.assertEqual(payload["RT-002"]["a_regulatory"], "CLOSED")
        self.assertEqual(payload["RT-002"]["b_eir_carrier"], "CLOSED")
        self.assertEqual(payload["RT-002"]["b_corporate"], "OPEN")
        self.assertEqual(payload["RT-002"]["c_corporate_signed"], "OPEN")
        self.assertTrue(payload["RT-002"]["eir_v4_present"])
        self.assertTrue(payload["RT-002"]["bim_standard_v4_present"])
        self.assertFalse(payload["RT-002"]["customer_approved_ids"])
        self.assertFalse(payload["RT-002"]["pointer_samolet_alias"])
        self.assertGreaterEqual(payload["RT-002"]["ids_counts"]["moexp"], 20)
        self.assertGreaterEqual(payload["RT-002"]["ids_counts"]["spb_cge"], 15)
        self.assertGreaterEqual(payload["RT-002"]["ids_counts"]["moscow_agr"], 3)
        self.assertEqual(payload["RT-003"]["a_federated_geometric_rehearsal"], "CLOSED")
        self.assertEqual(payload["RT-003"]["b_navis_federation_carrier"], "CLOSED")
        self.assertEqual(payload["RT-003"]["b_ifc_system_graph_rehearsal"], "CLOSED")
        self.assertEqual(payload["RT-003"]["b_mep_system_clash"], "OPEN")
        self.assertEqual(payload["RT-003"]["b1_navis_federation_carrier"], "CLOSED")
        self.assertEqual(payload["RT-003"]["b2_ifc_system_graph_rehearsal"], "CLOSED")
        self.assertEqual(payload["RT-003"]["b3_mep_system_clash"], "OPEN")
        self.assertEqual(payload["RT-003"]["mep_system_clash"], "NOT_VERIFIED")
        self.assertGreaterEqual(payload["RT-003"]["nwd_federation_count"], 3)
        self.assertEqual(payload["RT-003"]["mep_duct_pipe_cable_count"], 0)
        self.assertFalse(payload["RT-003"]["parse_rvt_nwd_lira"])
        self.assertTrue(all(payload["evidence_present"].values()))

    def test_undifferentiated_close_is_rejected(self) -> None:
        payload = assemble_rt_blocker_volumes(REPO_ROOT)
        dirty = dict(payload)
        dirty["closes_rt001"] = True
        with self.assertRaises(RtBlockerVolumeError):
            require_honest_rt_blocker_volumes(dirty)
        dirty = dict(payload)
        rt002 = dict(payload["RT-002"])
        rt002["c_corporate_signed"] = "CLOSED"
        dirty["RT-002"] = rt002
        with self.assertRaises(RtBlockerVolumeError):
            require_honest_rt_blocker_volumes(dirty)
        dirty = dict(payload)
        rt003 = dict(payload["RT-003"])
        rt003["b_mep_system_clash"] = "CLOSED"
        dirty["RT-003"] = rt003
        with self.assertRaises(RtBlockerVolumeError):
            require_honest_rt_blocker_volumes(dirty)

    def test_readme_table_uses_volume_split(self) -> None:
        for name in ("README.md", "README.ru.md"):
            text = (REPO_ROOT / name).read_text(encoding="utf-8")
            self.assertIn("RT-001a", text)
            self.assertIn("RT-001b", text)
            self.assertIn("RT-002a", text)
            self.assertIn("RT-002b", text)
            self.assertIn("RT-002c", text)
            self.assertIn("RT-003a", text)
            self.assertIn("RT-003b", text)
            self.assertIn("b_eir_carrier", text)
            self.assertIn("b_navis_federation_carrier", text)
            self.assertIn("b_ifc_system_graph_rehearsal", text)
            self.assertIn("b_protocol_rehearsal", text)
            self.assertIn("RT-001b", text)
            self.assertNotIn("closes_rt001: true", text)

    def test_kt3_without_customer_embeds_volume_split(self) -> None:
        payload = assemble_kt3_without_customer(REPO_ROOT, generated_at="2026-09-04T00:00:00+00:00")
        self.assertEqual(payload["schema_version"], "1.6.0")
        self.assertEqual(payload["rt001_split"]["a_content_pairing"], "CLOSED")
        self.assertEqual(payload["rt001_split"]["b_criterion_dual_rater"], "OPEN")
        self.assertEqual(payload["rt001_split"]["b_protocol_rehearsal"], "CLOSED")
        self.assertEqual(payload["rt003_split"]["a_federated_geometric_rehearsal"], "CLOSED")
        self.assertEqual(payload["rt003_split"]["b_navis_federation_carrier"], "CLOSED")
        self.assertEqual(payload["rt003_split"]["b_ifc_system_graph_rehearsal"], "CLOSED")
        self.assertEqual(payload["rt003_split"]["b_mep_system_clash"], "OPEN")
        self.assertEqual(payload["rt002_split"]["a_regulatory"], "CLOSED")
        self.assertEqual(payload["rt002_split"]["b_eir_carrier"], "CLOSED")
        self.assertFalse(payload["closes_rt001"])
