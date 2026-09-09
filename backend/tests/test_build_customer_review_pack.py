from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.build_customer_review_pack import (
    build_customer_review_pack,
    main,
    render_customer_review_markdown,
)


def _report() -> dict[str, object]:
    return {
        "report_id": "a" * 32,
        "project_name": "House 5",
        "summary": {"passed": False, "outcome": "review_required"},
        "capabilities": {
            "ifc": {"status": "ok"},
            "mep_system_clash": {"status": "not_verified", "reason": "no geometry"},
        },
        "source_path": "/home/operator/private/customer.ifc",
        "issues": [
            {
                "finding_id": "accepted-det",
                "rule_id": "CC-2",
                "severity": "error",
                "priority": 80,
                "origin": "deterministic",
                "message": "Mismatch in /home/operator/private/customer.ifc",
                "target_ref": "IfcWall:42",
                "remark": {"body": "Machine T0"},
                "review": {
                    "state": "accepted",
                    "effective_text": "Expert T1",
                    "actor": "expert-1",
                    "event_id": "evt-1",
                },
            },
            {
                "finding_id": "det-warning",
                "rule_id": "CC-4",
                "severity": "warning",
                "priority": 60,
                "origin": "deterministic",
            },
            {
                "finding_id": "advisory-error",
                "rule_id": "VLM-1",
                "severity": "error",
                "priority": 99,
                "origin": "advisory",
                "confidence": 0.99,
            },
            {
                "finding_id": "rejected-det",
                "rule_id": "OLD-1",
                "severity": "error",
                "priority": 100,
                "origin": "deterministic",
                "review": {"state": "rejected"},
            },
        ],
    }


class CustomerReviewPackTests(unittest.TestCase):
    def test_ranking_redaction_baseline_and_claim_boundaries(self) -> None:
        pack = build_customer_review_pack(
            _report(),
            top_k=2,
            known_findings_payload={"findings": [{"rule_id": "CC-2", "target_ref": "IfcWall:42"}]},
            generated_at="2026-09-09T20:00:00+00:00",
        )
        findings = pack["findings"]
        self.assertEqual([row["finding_id"] for row in findings], ["accepted-det", "det-warning"])
        self.assertEqual(findings[0]["baseline_comparison"], "known_match")
        self.assertEqual(findings[0]["effective_text"], "Expert T1")
        self.assertEqual(pack["counts"]["excluded_terminal"], 1)
        self.assertFalse(pack["machine_result"]["passed"])
        self.assertEqual(pack["customer_acceptance"], "NOT_EVALUATED")
        self.assertEqual(pack["accuracy_claim"], "NOT_ESTABLISHED")
        self.assertEqual(pack["sla_claim"], "NOT_ESTABLISHED")
        self.assertIn("mep_system_clash", pack["not_evaluated_or_unverified"])
        serialized = json.dumps(pack, ensure_ascii=False)
        self.assertNotIn("source_path", serialized)
        self.assertNotIn("/home/operator/private", serialized)
        self.assertIn("not probability of a true defect", serialized)
        self.assertIn("не акт приёмки", render_customer_review_markdown(pack))

    def test_cli_writes_hashed_artifacts_and_bounds_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            build_customer_review_pack(_report(), top_k=0)
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            report = root / "report.json"
            report.write_text(json.dumps(_report()), encoding="utf-8")
            output = root / "out"
            self.assertEqual(
                main(["--report-json", str(report), "--output-dir", str(output)]),
                0,
            )
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["customer_acceptance"], "NOT_EVALUATED")
            self.assertEqual(len(manifest["files"]["customer-review.json"]["sha256"]), 64)
            self.assertTrue((output / "customer-review.md").is_file())


if __name__ == "__main__":
    unittest.main()
