from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.models import ComparisonOperator, RulePackStatus
from aerobim.infrastructure.adapters.json_norm_rule_pack_loader import JsonNormRulePackLoader

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PACK = REPO_ROOT / "samples" / "rule-packs" / "residential-ar-reference-template.json"


class JsonNormRulePackLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loader = JsonNormRulePackLoader()

    def test_loads_bounded_reference_pack_with_provenance(self) -> None:
        pack = self.loader.load(REFERENCE_PACK)

        self.assertEqual(pack.pack_id, "SAMOLET-RESIDENTIAL-AR-REFERENCE")
        self.assertEqual(pack.status, RulePackStatus.SYNTHETIC_TEMPLATE)
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
            with self.assertRaisesRegex(ValueError, "require an approval object"):
                self.loader.load(path)

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
        payload["approval"] = None
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "unapproved.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "require an approval object"):
                self.loader.load(path)

    def test_approved_pack_preserves_explicit_approval_reference(self) -> None:
        payload = json.loads(REFERENCE_PACK.read_text(encoding="utf-8"))
        payload["status"] = "approved"
        payload["approval"] = {
            "approved_by": "Two customer adjudicators",
            "approved_at": "2026-07-10T12:00:00+03:00",
            "scope_reference": "SCOPE-MEMO-AR-001",
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "approved.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            pack = self.loader.load(path)

        self.assertEqual(pack.status, RulePackStatus.APPROVED)
        self.assertIn("SCOPE-MEMO-AR-001", pack.approval_reference or "")

    def test_non_json_extension_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "pack.txt"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must use the .json extension"):
                self.loader.load(path)


if __name__ == "__main__":
    unittest.main()
