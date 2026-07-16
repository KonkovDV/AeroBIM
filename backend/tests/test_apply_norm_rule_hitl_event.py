from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.application.use_cases.apply_norm_rule_hitl_event import ApplyNormRuleHitlEventUseCase
from aerobim.domain.models import issue_from_requirement
from aerobim.infrastructure.adapters.filesystem_review_event_store import FilesystemReviewEventStore
from aerobim.infrastructure.adapters.json_norm_rule_pack_loader import JsonNormRulePackLoader
from aerobim.infrastructure.adapters.local_object_store import LocalObjectStore
from aerobim.infrastructure.adapters.object_store_norm_pack_version_store import (
    ObjectStoreNormRulePackVersionStore,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PACK = REPO_ROOT / "samples" / "rule-packs" / "residential-ar-reference-template.json"


class ApplyNormRuleHitlEventTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.object_store = LocalObjectStore(root / "objects")
        self.versions = ObjectStoreNormRulePackVersionStore(
            self.object_store, index_dir=root / "index"
        )
        self.events = FilesystemReviewEventStore(root / "events")
        self.use_case = ApplyNormRuleHitlEventUseCase(
            version_store=self.versions,
            review_event_store=self.events,
        )
        self.loader = JsonNormRulePackLoader()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_edit_creates_v2_and_preserves_v1_bytes(self) -> None:
        pack_id = "SAMOLET-RESIDENTIAL-AR-REFERENCE"
        v1_bytes = REFERENCE_PACK.read_bytes()
        # Seed immutable v1 explicitly, then apply HITL edit as v2.
        self.versions.save_version(
            pack_id=pack_id,
            version="0.1.0",
            payload=v1_bytes,
            created_by="seed",
            parent_version=None,
            approval_status="synthetic",
            approval_ref=None,
        )
        record, event = self.use_case.execute(
            pack_id=pack_id,
            base_pack_path=REFERENCE_PACK,
            event_type="norm_rule_edited",
            rule_diff={
                "rule_id": "SAM-AR-001",
                "evidence_text": "HITL edited evidence (still synthetic).",
                "norm_source": "СП 54.13330",
            },
            proposed_by="engineer-a",
            target_approval_status="draft",
        )
        self.assertEqual(record.parent_version, "0.1.0")
        self.assertTrue(record.version.startswith("0.1.0+hitl."))
        self.assertEqual(event.resulting_pack_version, record.version)
        self.assertEqual(self.versions.get_version_bytes(pack_id, "0.1.0"), v1_bytes)
        v2 = self.versions.get_version_bytes(pack_id, record.version)
        self.assertIsNotNone(v2)
        assert v2 is not None
        self.assertNotEqual(v2, v1_bytes)
        versions = self.versions.list_versions(pack_id)
        self.assertEqual(len(versions), 2)

    def test_customer_approved_without_approval_ref_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "approval_ref"):
            self.use_case.execute(
                pack_id="SAMOLET-RESIDENTIAL-AR-REFERENCE",
                base_pack_path=REFERENCE_PACK,
                event_type="norm_rule_proposed",
                rule_diff={"rule_id": "SAM-AR-001", "evidence_text": "x"},
                proposed_by="engineer-a",
                target_approval_status="customer_approved",
                approval_ref=None,
            )

    def test_finding_provenance_points_at_hitl_pack_version(self) -> None:
        pack_id = "SAMOLET-RESIDENTIAL-AR-REFERENCE"
        record, _event = self.use_case.execute(
            pack_id=pack_id,
            base_pack_path=REFERENCE_PACK,
            event_type="norm_rule_proposed",
            rule_diff={
                "rule_id": "SAM-AR-NEW",
                "scope": "ifc-property",
                "ifc_entity": "IfcWall",
                "property_set": "Pset_WallCommon",
                "property_name": "FireRating",
                "operator": "exists",
                "norm_source": "СП 54.13330",
                "norm_clause": "7.1",
            },
            proposed_by="engineer-b",
            target_approval_status="draft",
        )
        payload = self.versions.get_version_bytes(pack_id, record.version)
        assert payload is not None
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "hitl.json"
            path.write_bytes(payload)
            loaded = self.loader.load(path)
        rule = next(item for item in loaded.rules if item.rule_id == "SAM-AR-NEW")
        self.assertIn(record.version, rule.source)
        self.assertEqual(rule.approval_status, "draft")
        self.assertEqual(rule.norm_source, "СП 54.13330")
        from aerobim.domain.models import FindingCategory, Severity

        issue = issue_from_requirement(
            rule,
            severity=Severity.ERROR,
            message="missing",
            category=FindingCategory.IFC_VALIDATION,
        )
        self.assertEqual(issue.approval_status, "draft")
        self.assertEqual(issue.norm_source, "СП 54.13330")
        self.assertIn(record.version, issue.source_id or "")


if __name__ == "__main__":
    unittest.main()
