from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.models import ComparisonOperator, RulePackStatus
from aerobim.infrastructure.adapters.json_norm_rule_pack_loader import (
    JsonNormRulePackLoader,
    compute_norm_pack_content_hash,
)
from aerobim.infrastructure.adapters.local_object_store import LocalObjectStore
from aerobim.infrastructure.adapters.object_store_norm_pack_version_store import (
    ObjectStoreNormRulePackVersionStore,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PACK = REPO_ROOT / "samples" / "rule-packs" / "residential-ar-reference-template.json"
INTAKE_PACK = REPO_ROOT / "samples" / "rule-packs" / "customer-norm-pack-intake-template.json"


def _approved_payload_from_intake() -> dict:
    payload = json.loads(INTAKE_PACK.read_text(encoding="utf-8"))
    payload["status"] = "customer_approved"
    payload["claim_labels"] = ["customer-evidence"]
    payload["jurisdiction"] = "RF"
    payload["rules"][0]["norm_clause"] = "7.1.2"
    payload["approval"] = {
        "approved_by": "customer-qa",
        "approval_date": "2026-07-17T12:00:00+03:00",
        "approval_status": "customer_approved",
        "document_title": "Samolet residential AR norms",
        "document_edition": "2026-07",
        "effective_date": "2026-07-01",
        "scope_reference": "SIGNED-MEMO-REF",
    }
    payload["approval_ref"] = "SIGNED-MEMO-REF"
    payload["pack_hash"] = compute_norm_pack_content_hash(payload)
    return payload


class JsonNormRulePackLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loader = JsonNormRulePackLoader()

    def test_loads_bounded_reference_pack_with_provenance(self) -> None:
        pack = self.loader.load(REFERENCE_PACK)

        self.assertEqual(pack.pack_id, "SAMOLET-RESIDENTIAL-AR-REFERENCE")
        self.assertEqual(pack.status, RulePackStatus.SYNTHETIC_TEMPLATE)
        self.assertTrue(pack.advisory_only)
        self.assertIn("synthetic", pack.claim_labels)
        self.assertEqual(pack.disciplines, ("AR",))
        self.assertEqual(len(pack.rules), 20)
        self.assertEqual(len(pack.sha256), 64)
        self.assertIsNone(pack.approval_reference)
        self.assertEqual(pack.rules[0].evidence_modality, "norm-rule-pack")
        self.assertEqual(pack.rules[0].approval_status, "synthetic")
        self.assertIsNone(pack.rules[0].approval_ref)
        self.assertEqual(pack.rules[-1].operator, ComparisonOperator.GREATER_OR_EQUAL)
        self.assertAlmostEqual(pack.rules[-1].quantity.si_value, 1.2)

    def test_customer_approved_without_approval_ref_fails_closed(self) -> None:
        payload = json.loads(REFERENCE_PACK.read_text(encoding="utf-8"))
        payload["status"] = "customer_approved"
        payload["approval"] = None
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "no-ref.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "synthetic/fixture claim_labels"):
                self.loader.load(path)

    def test_malformed_approval_object_rejected(self) -> None:
        payload = _approved_payload_from_intake()
        del payload["approval"]["document_title"]
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "bad-approval.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "document_title"):
                self.loader.load(path)

    def test_approval_ref_only_rejected(self) -> None:
        payload = _approved_payload_from_intake()
        payload["approval"] = None
        payload["approval_ref"] = "SIGNED-MEMO-REF-ONLY"
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "ref-only.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "approval_ref alone is not sufficient"):
                self.loader.load(path)

    def test_synthetic_marked_pack_cannot_claim_customer_approved(self) -> None:
        payload = _approved_payload_from_intake()
        payload["claim_labels"] = ["synthetic", "fixture"]
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "synth-claim.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cannot claim customer_approved"):
                self.loader.load(path)

    def test_pack_hash_mismatch_blocks_signoff(self) -> None:
        payload = _approved_payload_from_intake()
        payload["pack_hash"] = "0" * 64
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "hash-mismatch.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "pack_hash/source_hash mismatch"):
                self.loader.load(path)

    def test_full_customer_approved_pack_loads(self) -> None:
        payload = _approved_payload_from_intake()
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "approved.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            pack = self.loader.load(path)
        self.assertEqual(pack.status, RulePackStatus.APPROVED)
        self.assertFalse(pack.advisory_only)
        self.assertEqual(pack.jurisdiction, "RF")
        self.assertEqual(pack.document_title, "Samolet residential AR norms")
        self.assertEqual(pack.rules[0].norm_clause, "7.1.2")
        self.assertEqual(pack.rules[0].approval_status, "customer_approved")

    def test_norm_provenance_reaches_validation_issue(self) -> None:
        from aerobim.domain.models import (
            FindingCategory,
            ParsedRequirement,
            Severity,
            issue_from_requirement,
        )

        requirement = ParsedRequirement(
            rule_id="SAM-AR-PROV",
            ifc_entity="IFCWALL",
            property_set="Pset_WallCommon",
            property_name="FireRating",
            expected_value="REI60",
            norm_source="СП 54.13330",
            norm_edition="2022",
            norm_clause="7.1.2",
            approval_status="synthetic",
            approval_ref=None,
            evidence_modality="norm-rule-pack",
        )
        issue = issue_from_requirement(
            requirement,
            severity=Severity.ERROR,
            message="Property does not match",
            category=FindingCategory.IFC_VALIDATION,
            observed_value="REI30",
        )
        self.assertEqual(issue.norm_source, "СП 54.13330")
        self.assertEqual(issue.norm_edition, "2022")
        self.assertEqual(issue.norm_clause, "7.1.2")
        self.assertEqual(issue.approval_status, "synthetic")
        self.assertIsNone(issue.approval_ref)

    def test_duplicate_rule_id_is_rejected(self) -> None:
        payload = json.loads(REFERENCE_PACK.read_text(encoding="utf-8"))
        payload["rules"].append(dict(payload["rules"][0]))
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "duplicate.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate rule_id"):
                self.loader.load(path)

    def test_approved_pack_requires_approval_metadata(self) -> None:
        payload = json.loads(REFERENCE_PACK.read_text(encoding="utf-8"))
        payload["status"] = "approved"
        payload["claim_labels"] = ["customer-evidence"]
        payload["approval"] = None
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "unapproved.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "require an approval object"):
                self.loader.load(path)

    def test_approved_pack_preserves_explicit_approval_reference(self) -> None:
        payload = _approved_payload_from_intake()
        payload["status"] = "approved"
        payload["approval"]["approval_status"] = "approved"
        payload["pack_hash"] = compute_norm_pack_content_hash(payload)
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "approved.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            pack = self.loader.load(path)

        self.assertEqual(pack.status, RulePackStatus.APPROVED)
        self.assertIn("SIGNED-MEMO-REF", pack.approval_reference or "")

    def test_non_json_extension_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "pack.txt"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must use the .json extension"):
                self.loader.load(path)


class NormPackImmutableHashTests(unittest.TestCase):
    def test_changing_one_rule_changes_content_hash_and_mismatch_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = ObjectStoreNormRulePackVersionStore(
                LocalObjectStore(root / "objects"),
                index_dir=root / "index",
            )
            pack_id = "SAMOLET-RESIDENTIAL-AR-REFERENCE"
            v1 = REFERENCE_PACK.read_bytes()
            record = store.save_version(
                pack_id=pack_id,
                version="0.1.0",
                payload=v1,
                created_by="seed",
                parent_version=None,
                approval_status="synthetic",
                approval_ref=None,
            )
            self.assertEqual(record.content_sha256, hashlib.sha256(v1).hexdigest())
            observed = store.verify_version_integrity(pack_id, "0.1.0")
            self.assertEqual(observed, record.content_sha256)

            mutated = json.loads(v1.decode("utf-8"))
            mutated["rules"][0]["evidence_text"] = "mutated evidence"
            mutated_bytes = json.dumps(mutated, ensure_ascii=False).encode("utf-8")
            self.assertNotEqual(hashlib.sha256(mutated_bytes).hexdigest(), record.content_sha256)

            # Simulate tampering of stored object while index keeps old hash.
            key = record.object_key
            store._store.put_bytes(key, mutated_bytes, content_type="application/json")  # noqa: SLF001
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                store.verify_version_integrity(pack_id, "0.1.0")

    def test_store_rejects_synthetic_customer_approved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = ObjectStoreNormRulePackVersionStore(
                LocalObjectStore(root / "objects"),
                index_dir=root / "index",
            )
            with self.assertRaisesRegex(ValueError, "synthetic/fixture claim_labels"):
                store.save_version(
                    pack_id="SAMOLET-RESIDENTIAL-AR-REFERENCE",
                    version="9.9.9-bad",
                    payload=REFERENCE_PACK.read_bytes(),
                    created_by="attacker",
                    parent_version=None,
                    approval_status="customer_approved",
                    approval_ref="FAKE-REF",
                )

    def test_content_hash_helper_changes_when_rule_changes(self) -> None:
        payload = json.loads(REFERENCE_PACK.read_text(encoding="utf-8"))
        h1 = compute_norm_pack_content_hash(payload)
        mutated = copy.deepcopy(payload)
        mutated["rules"][0]["property_name"] = "MutatedProperty"
        h2 = compute_norm_pack_content_hash(mutated)
        self.assertNotEqual(h1, h2)


if __name__ == "__main__":
    unittest.main()
