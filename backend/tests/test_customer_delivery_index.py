"""Three-pack + trial delivery index: not accuracy, not GitHub, not demo-seed."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.customer_delivery_index import (
    PACK_SLOTS,
    DeliveryIndexError,
    empty_delivery_index,
    validate_delivery_index,
)
from aerobim.tools.export_customer_delivery_index import assert_index_path_allowed, main


def _filled(*, status: str = "sent", mode: str = "on_prem_docker") -> dict:
    index = empty_delivery_index()
    index["packs"] = [
        {
            "slot": slot,
            "status": status,
            "report_id": f"r{index:02d}" + "a" * 30,
        }
        for index, slot in enumerate(PACK_SLOTS, start=1)
    ]
    index["trial"] = {"mode": mode}
    return index


class CustomerDeliveryIndexTests(unittest.TestCase):
    def test_empty_index_is_not_ready(self) -> None:
        payload = empty_delivery_index()
        self.assertEqual([row["slot"] for row in payload["packs"]], list(PACK_SLOTS))
        self.assertFalse(payload["ready_for_deadline"])
        self.assertFalse(payload["is_accuracy"])
        self.assertFalse(payload["git_hosts_reports"])
        self.assertFalse(payload["trial"]["independent_test"])
        self.assertFalse(payload["customer_go"])
        self.assertFalse(payload["samolet_direct_contact"])
        self.assertEqual(payload["delivery_channel"], "organizers_only")
        self.assertTrue(payload["customer_deadline_is_final"])
        self.assertTrue(payload["post_deadline_slot_is_not_delivery"])

    def test_demo_seed_rejected(self) -> None:
        payload = _filled()
        payload["packs"][0]["report_id"] = "9" * 32
        with self.assertRaises(DeliveryIndexError):
            validate_delivery_index(payload)

    def test_github_url_rejected(self) -> None:
        payload = _filled()
        payload["packs"][0]["url"] = "https://github.com/org/repo/blob/main/report.html"
        with self.assertRaises(DeliveryIndexError):
            validate_delivery_index(payload)

    def test_screen_share_is_not_independent(self) -> None:
        payload = validate_delivery_index(_filled(mode="screen_share_only"))
        self.assertFalse(payload["trial"]["independent_test"])
        self.assertFalse(payload["ready_for_deadline"])

    def test_sent_plus_on_prem_is_ready(self) -> None:
        payload = validate_delivery_index(_filled())
        self.assertTrue(payload["trial"]["independent_test"])
        self.assertTrue(payload["ready_for_deadline"])

    def test_ready_local_is_not_deadline_ready(self) -> None:
        payload = validate_delivery_index(_filled(status="ready_local"))
        self.assertFalse(payload["ready_for_deadline"])

    def test_sent_without_html_export_rejected(self) -> None:
        payload = _filled()
        payload["packs"][0]["export_kinds"] = ["json", "pdf", "bcf"]
        with self.assertRaises(DeliveryIndexError):
            validate_delivery_index(payload)

    def test_not_run_cannot_carry_report_id(self) -> None:
        payload = empty_delivery_index()
        payload["packs"][0]["report_id"] = "r01" + "a" * 30
        with self.assertRaises(DeliveryIndexError):
            validate_delivery_index(payload)

    def test_direct_samolet_contact_rejected(self) -> None:
        payload = _filled()
        payload["samolet_direct_contact"] = True
        with self.assertRaises(DeliveryIndexError):
            validate_delivery_index(payload)

    def test_anonymous_trial_rejected(self) -> None:
        payload = _filled()
        payload["trial"]["anonymous"] = True
        with self.assertRaises(DeliveryIndexError):
            validate_delivery_index(payload)

    def test_wrong_slot_count_rejected(self) -> None:
        payload = empty_delivery_index()
        payload["packs"] = payload["packs"][:2]
        with self.assertRaises(DeliveryIndexError):
            validate_delivery_index(payload)

    def test_cli_refuses_docs_and_writes_local(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "delivery-index.json"
            code = main(["--repo", str(repo), "--output", str(out)])
            self.assertEqual(code, 0)
            written = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(written["artifact_type"], "customer_delivery_index")
            self.assertFalse(written["ready_for_deadline"])
        with self.assertRaises(ValueError):
            assert_index_path_allowed(repo / "docs" / "evidence" / "delivery-index.json", repo=repo)


if __name__ == "__main__":
    unittest.main()
