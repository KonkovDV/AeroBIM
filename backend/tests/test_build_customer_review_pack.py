from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.build_customer_review_pack import (
    build_customer_review_pack,
    main,
    render_customer_review_form,
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
                "observed_value": "C20/25",
                "expected_value": "C25/30",
                "unit": "concrete class",
                "norm_clause": "SP 63.13330 6.1",
                "evidence_refs": ["ifc://house-5#IfcWall:42", "pdf://AR-12#p3"],
                "remark": {"body": "Machine T0"},
                "review": {
                    "state": "accepted",
                    "effective_text": "Expert T1",
                    "actor": "expert-1",
                    "event_id": "evt-1",
                },
            },
            {
                "finding_id": "duplicate-det",
                "rule_id": "CC-2",
                "severity": "error",
                "priority": 70,
                "origin": "deterministic",
                "message": "Same rule and element family",
                "target_ref": "IfcWall:77",
                "observed_value": "C20/25",
                "expected_value": "C25/30",
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
                "message": "Advisory candidate",
                "target_ref": "IfcSlab:9",
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
        self.assertEqual(
            [row["finding_id"] for row in findings],
            ["accepted-det", "advisory-error"],
        )
        self.assertEqual(findings[0]["baseline_comparison"], "known_match")
        self.assertEqual(findings[0]["effective_text"], "Expert T1")
        self.assertEqual(findings[0]["evidence_completeness"], "full")
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
        markdown = render_customer_review_markdown(pack)
        self.assertIn("не акт приёмки", markdown)

    def test_triage_funnel_coverage_and_data_gaps(self) -> None:
        pack = build_customer_review_pack(
            _report(),
            top_k=20,
            known_findings_payload={"findings": [{"rule_id": "CC-2", "target_ref": "IfcWall:42"}]},
            generated_at="2026-09-10T06:00:00+00:00",
        )
        counts = pack["counts"]
        self.assertEqual(counts["duplicates_collapsed"], 1)
        self.assertEqual(counts["deferred_needs_data"], 1)
        self.assertEqual(counts["selected"], 2)
        self.assertEqual(pack["findings"][0]["similar_count"], 2)
        self.assertEqual(pack["needs_data"]["by_rule"], {"CC-4": 1})
        self.assertEqual(pack["evidence_completeness_counts"]["insufficient"], 1)
        self.assertEqual(pack["known_baseline"]["matched_baseline_count"], 1)
        self.assertEqual(pack["known_baseline"]["coverage_ratio"], 1.0)
        self.assertEqual(pack["known_baseline"]["coverage_scope"], "identity_key_match_only")
        stages = {stage["stage"]: stage["count"] for stage in pack["funnel"]}
        self.assertEqual(stages["machine_findings"], 5)
        self.assertEqual(stages["terminal_excluded"], 1)
        self.assertEqual(stages["shortlisted"], 2)
        strict = build_customer_review_pack(_report(), top_k=20, strict_evidence=True)
        self.assertEqual([row["finding_id"] for row in strict["findings"]], ["accepted-det"])
        self.assertEqual(strict["counts"]["excluded_incomplete_evidence"], 1)
        verbose = build_customer_review_pack(
            _report(),
            top_k=20,
            include_needs_data=True,
            keep_duplicates=True,
        )
        self.assertEqual(
            [row["finding_id"] for row in verbose["findings"]],
            ["accepted-det", "duplicate-det", "det-warning", "advisory-error"],
        )

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
            self.assertEqual(len(manifest["files"]), 3)
            self.assertTrue((output / "customer-review.md").is_file())
            raw = (output / "customer-review-form.csv").read_bytes()
            form = raw.decode("utf-8-sig")
            rows = [line for line in form.split("\r\n") if line]
            self.assertIn("decision", rows[0])
            self.assertEqual(len(rows), 3)
        pack = build_customer_review_pack(_report(), top_k=1)
        self.assertEqual(render_customer_review_form(pack).count("\r\n"), 2)


if __name__ == "__main__":
    unittest.main()
