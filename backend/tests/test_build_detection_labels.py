from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.build_detection_labels import (
    AdjudicationError,
    build_labels,
    load_rows,
    main,
)
from aerobim.tools.evaluate_detection_precision import evaluate_detection_precision

REPO_ROOT = Path(__file__).resolve().parents[2]
DP_DIR = REPO_ROOT / "samples" / "benchmarks" / "detection-precision"
TEMPLATE_CSV = DP_DIR / "adjudication-template.csv"
LABELS_SCHEMA = DP_DIR / "labels.schema.json"

_HEADER = (
    "finding_id,case_id,finding_class,rule_id,target_ref,element_guid,"
    "match_key,adjudicator_id,verdict,notes,timestamp\n"
)


def _write_csv(tmp: Path, body: str) -> Path:
    path = tmp / "adj.csv"
    path.write_text(_HEADER + body, encoding="utf-8")
    return path


class TemplateCsvTests(unittest.TestCase):
    def test_template_compiles_to_draft_labels(self) -> None:
        rows = load_rows(TEMPLATE_CSV)
        payload = build_labels(
            rows,
            dataset_id="EX",
            dataset_status="draft",
            scope_reference="EX-ONLY",
            method="consensus",
            completed_at=None,
        )
        findings = payload["cases"][0]["expected_findings"]
        statuses = sorted(f["adjudication_status"] for f in findings)
        # 2 confirmed (agree TP, agree FN), 1 excluded (agree FP), 1 unresolved (disagree)
        self.assertEqual(statuses, ["confirmed", "confirmed", "excluded", "unresolved"])
        self.assertEqual(len(payload["adjudication"]["adjudicators"]), 2)

    def test_template_output_conforms_to_labels_schema(self) -> None:
        import jsonschema

        rows = load_rows(TEMPLATE_CSV)
        payload = build_labels(
            rows,
            dataset_id="EX",
            dataset_status="draft",
            scope_reference="EX-ONLY",
            method="consensus",
            completed_at=None,
        )
        schema = json.loads(LABELS_SCHEMA.read_text(encoding="utf-8"))
        errors = list(jsonschema.Draft202012Validator(schema).iter_errors(payload))
        self.assertEqual(errors, [], [e.message for e in errors])


class ReconciliationTests(unittest.TestCase):
    def test_verdict_reconciliation_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            csv_path = _write_csv(
                tmp,
                # agree TP -> confirmed
                "f1,C,cross-document,R1,T1,,,a,TP,,2026-07-11T10:00:00+03:00\n"
                "f1,C,cross-document,R1,T1,,,b,TP,,2026-07-11T10:00:00+03:00\n"
                # agree FP -> excluded
                "f2,C,cross-document,R2,T2,,,a,FP,,2026-07-11T10:00:00+03:00\n"
                "f2,C,cross-document,R2,T2,,,b,FP,,2026-07-11T10:00:00+03:00\n"
                # disagree -> unresolved
                "f3,C,clash,SP,,,GX|GY,a,TP,,2026-07-11T10:00:00+03:00\n"
                "f3,C,clash,SP,,,GX|GY,b,FP,,2026-07-11T10:00:00+03:00\n"
                # agree FN -> confirmed
                "f4,C,missing-element,R4,T4,,,a,FN,,2026-07-11T10:00:00+03:00\n"
                "f4,C,missing-element,R4,T4,,,b,FN,,2026-07-11T10:00:00+03:00\n",
            )
            payload = build_labels(
                load_rows(csv_path),
                dataset_id="EX",
                dataset_status="draft",
                scope_reference=None,
                method="consensus",
                completed_at=None,
            )
        by_rule = {
            f["rule_id"]: f["adjudication_status"]
            for f in payload["cases"][0]["expected_findings"]
        }
        self.assertEqual(by_rule["R1"], "confirmed")
        self.assertEqual(by_rule["R2"], "excluded")
        self.assertEqual(by_rule["SP"], "unresolved")
        self.assertEqual(by_rule["R4"], "confirmed")

    def test_same_adjudicator_conflicting_verdict_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            csv_path = _write_csv(
                Path(td),
                "f1,C,cross-document,R1,T1,,,a,TP,,2026-07-11T10:00:00+03:00\n"
                "f1,C,cross-document,R1,T1,,,a,FP,,2026-07-11T10:00:00+03:00\n",
            )
            with self.assertRaisesRegex(AdjudicationError, "conflicting"):
                build_labels(
                    load_rows(csv_path),
                    dataset_id="EX",
                    dataset_status="draft",
                    scope_reference=None,
                    method="consensus",
                    completed_at=None,
                )


class FailClosedTests(unittest.TestCase):
    def _rows(self, td: Path, *, two: bool = True, unresolved: bool = False):
        body = (
            "f1,C,cross-document,R1,T1,,,a,TP,,2026-07-11T10:00:00+03:00\n"
        )
        if two:
            verdict = "FP" if unresolved else "TP"
            body += f"f1,C,cross-document,R1,T1,,,b,{verdict},,2026-07-11T10:00:00+03:00\n"
        return load_rows(_write_csv(td, body))

    def test_adjudicated_requires_two_adjudicators(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            rows = self._rows(Path(td), two=False)
            with self.assertRaisesRegex(AdjudicationError, ">=2 distinct adjudicator"):
                build_labels(
                    rows, dataset_id="EX", dataset_status="adjudicated",
                    scope_reference="S", method="consensus",
                    completed_at="2026-07-11T12:00:00+03:00",
                )

    def test_adjudicated_rejects_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            rows = self._rows(Path(td), two=True, unresolved=True)
            with self.assertRaisesRegex(AdjudicationError, "unresolved"):
                build_labels(
                    rows, dataset_id="EX", dataset_status="adjudicated",
                    scope_reference="S", method="consensus",
                    completed_at="2026-07-11T12:00:00+03:00",
                )

    def test_adjudicated_requires_scope_and_tz_completed_at(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            rows = self._rows(Path(td), two=True)
            with self.assertRaisesRegex(AdjudicationError, "scope_reference"):
                build_labels(
                    rows, dataset_id="EX", dataset_status="adjudicated",
                    scope_reference=None, method="consensus",
                    completed_at="2026-07-11T12:00:00+03:00",
                )
            with self.assertRaisesRegex(AdjudicationError, "completed_at"):
                build_labels(
                    rows, dataset_id="EX", dataset_status="adjudicated",
                    scope_reference="S", method="consensus",
                    completed_at="2026-07-11T12:00:00",  # naive, no tz
                )


class MalformedCsvTests(unittest.TestCase):
    def test_missing_required_column_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.csv"
            path.write_text("case_id,verdict\nC,TP\n", encoding="utf-8")
            with self.assertRaisesRegex(AdjudicationError, "missing columns"):
                load_rows(path)

    def test_invalid_verdict_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            csv_path = _write_csv(
                Path(td), "f1,C,cross-document,R1,T1,,,a,MAYBE,,2026-07-11T10:00:00+03:00\n"
            )
            with self.assertRaisesRegex(AdjudicationError, "verdict must be"):
                load_rows(csv_path)

    def test_finding_without_any_ref_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            csv_path = _write_csv(
                Path(td), "f1,C,cross-document,R1,,,,a,TP,,2026-07-11T10:00:00+03:00\n"
            )
            with self.assertRaisesRegex(AdjudicationError, "target_ref / element_guid / match_key"):
                load_rows(csv_path)


class EndToEndHarnessTests(unittest.TestCase):
    def test_compiled_adjudicated_labels_pass_publishable_gate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            csv_path = _write_csv(
                tmp,
                "f1,CASE-1,cross-document,R-AREA,APT-01,,,a,TP,,2026-07-11T10:00:00+03:00\n"
                "f1,CASE-1,cross-document,R-AREA,APT-01,,,b,TP,,2026-07-11T10:00:00+03:00\n",
            )
            labels_path = tmp / "labels.json"
            rc = main(
                [
                    "--adjudication", str(csv_path),
                    "--output", str(labels_path),
                    "--dataset-id", "CUST",
                    "--dataset-status", "adjudicated",
                    "--scope-reference", "SCOPE-MEMO",
                    "--completed-at", "2026-07-11T12:00:00+03:00",
                ]
            )
            self.assertEqual(rc, 0)
            detections = tmp / "det.json"
            detections.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "run_id": "R",
                        "cases": [
                            {
                                "case_id": "CASE-1",
                                "findings": [
                                    {
                                        "finding_class": "cross-document",
                                        "rule_id": "R-AREA",
                                        "target_ref": "APT-01",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            report = evaluate_detection_precision(
                labels_path, detections, require_publishable=True
            )
        self.assertTrue(report["publishable_protocol_gate"])
        self.assertIsNone(report["warning"])
        self.assertEqual(report["micro"]["tp"], 1)


if __name__ == "__main__":
    unittest.main()
