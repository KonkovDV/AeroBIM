"""Regressions for demo-pass findings D05–D07, D13–D14. Synthetic only."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.check_coverage import CoverageStatus, coverage_from_report
from aerobim.domain.models import (
    FindingCategory,
    GeneratedRemark,
    ReviewEvent,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.domain.review_event_append import assert_review_target_in_report
from aerobim.domain.review_projection import project_issue_review
from aerobim.domain.revision_diff import compare_report_revisions
from aerobim.infrastructure.adapters.filesystem_review_event_store import (
    AuditEventCorruptionError,
    FilesystemReviewEventStore,
    SequenceClaimError,
    _write_event_exclusive,
)


def _issue(finding_id: str, rule_id: str = "R1") -> ValidationIssue:
    return ValidationIssue(
        rule_id=rule_id,
        severity=Severity.ERROR,
        message="m",
        category=FindingCategory.IFC_VALIDATION,
        remark=GeneratedRemark(title="t", body="machine"),
        finding_id=finding_id,
    )


def _report(*issues: ValidationIssue, traces: tuple = ()) -> ValidationReport:
    return ValidationReport(
        report_id="a" * 32,
        request_id="req",
        ifc_path=Path("m.ifc"),
        created_at="2026-09-16T00:00:00+00:00",
        requirements=(),
        issues=issues,
        summary=ValidationSummary(0, len(issues), 1, 0, False),
        tool_traces=traces,
        project_name="demo-pack",
        information_container_id="pack-1",
    )


class D05TargetTests(unittest.TestCase):
    def test_empty_report_rejects_finding_event(self) -> None:
        with self.assertRaises(ValueError):
            assert_review_target_in_report(
                _report(),
                finding_id="ghost",
                issue_rule_id="R1",
                event_type="accepted",
            )

    def test_missing_ids_rejected_on_nonempty_report(self) -> None:
        with self.assertRaises(ValueError):
            assert_review_target_in_report(
                _report(_issue("fid-1")),
                finding_id=None,
                issue_rule_id=None,
                event_type="edited_remark",
            )

    def test_foreign_finding_rejected(self) -> None:
        with self.assertRaises(ValueError):
            assert_review_target_in_report(
                _report(_issue("fid-1")),
                finding_id="fid-other",
                issue_rule_id="R1",
                event_type="accepted",
            )

    def test_fid_rid_mismatch_rejected(self) -> None:
        with self.assertRaises(ValueError):
            assert_review_target_in_report(
                _report(_issue("fid-1", "R1")),
                finding_id="fid-1",
                issue_rule_id="R-other",
                event_type="accepted",
            )

    def test_duplicate_rule_id_without_fid_rejected(self) -> None:
        with self.assertRaises(ValueError):
            assert_review_target_in_report(
                _report(_issue("fid-1", "R1"), _issue("fid-2", "R1")),
                finding_id=None,
                issue_rule_id="R1",
                event_type="edited_remark",
            )

    def test_norm_pack_skips_finding_membership(self) -> None:
        assert_review_target_in_report(
            _report(),
            finding_id=None,
            issue_rule_id=None,
            event_type="norm_rule_proposed",
        )


class D01ProjectionTests(unittest.TestCase):
    def test_accepted_note_does_not_become_effective_text(self) -> None:
        events = (
            ReviewEvent(
                event_id="e1",
                report_id="a" * 32,
                event_type="edited_remark",
                created_at="2026-09-16T00:00:01+00:00",
                finding_id="fid-1",
                note="saved revision",
                resulting_state="edited",
            ),
            ReviewEvent(
                event_id="e2",
                report_id="a" * 32,
                event_type="accepted",
                created_at="2026-09-16T00:00:02+00:00",
                finding_id="fid-1",
                note="stale draft in note",
                resulting_state="accepted",
            ),
        )
        overlay = project_issue_review(
            finding_id="fid-1",
            rule_id="R1",
            machine_text="machine",
            events=events,
        )
        self.assertEqual(overlay["effective_text"], "saved revision")
        self.assertEqual(overlay["state"], "accepted")


class D06WriteTests(unittest.TestCase):
    def test_duplicate_slot_does_not_replace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "r.jsonl"
            event = ReviewEvent(
                event_id="e1",
                report_id="r" * 32,
                event_type="opened",
                created_at="2026-09-16T00:00:00+00:00",
                finding_id="fid-1",
                sequence_number=1,
            )
            slot = _write_event_exclusive(target, event, sequence=1)
            self.assertTrue(slot.exists())
            with self.assertRaises(SequenceClaimError):
                _write_event_exclusive(target, event, sequence=1)
            self.assertIn("opened", slot.read_text(encoding="utf-8"))

    def test_empty_seq_slot_is_corrupt_not_empty_journal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = FilesystemReviewEventStore(root, fail_closed=True)
            target = store._path("b" * 32)
            target.parent.mkdir(parents=True, exist_ok=True)
            (target.parent / f"{target.name}.seq.1").write_text("\n", encoding="utf-8")
            with self.assertRaises(AuditEventCorruptionError):
                store.list_for_report("b" * 32)


class D07MigrateTests(unittest.TestCase):
    def test_legacy_jsonl_survives_third_append(self) -> None:
        from aerobim.domain.review_event_append import ReviewEventAppendSpec

        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemReviewEventStore(Path(tmp), fail_closed=True)
            report_id = "c" * 32
            target = store._path(report_id)
            target.parent.mkdir(parents=True, exist_ok=True)
            from dataclasses import asdict

            lines = []
            for index, event_type in enumerate(("opened", "edited_remark"), start=1):
                event = ReviewEvent(
                    event_id=f"e{index}",
                    report_id=report_id,
                    event_type=event_type,  # type: ignore[arg-type]
                    created_at=f"2026-09-16T00:00:0{index}+00:00",
                    finding_id="fid-1",
                    issue_rule_id="R1",
                    actor="expert",
                    note="saved" if event_type == "edited_remark" else None,
                    sequence_number=index,
                    resulting_state="opened" if event_type == "opened" else "edited",
                    previous_state=None if event_type == "opened" else "opened",
                )
                lines.append(json.dumps(asdict(event), ensure_ascii=False))
            target.write_text("\n".join(lines) + "\n", encoding="utf-8")
            stamped = store.append_api_event(
                ReviewEventAppendSpec(
                    report_id=report_id,
                    event_type="accepted",
                    created_at="2026-09-16T00:00:03+00:00",
                    actor="expert",
                    finding_id="fid-1",
                    issue_rule_id="R1",
                    previous_state="edited",
                    idempotency_key="k-accept",
                    event_id="e3",
                )
            )
            self.assertEqual(stamped.event_type, "accepted")
            listed = store.list_for_report(report_id)
            self.assertEqual(len(listed), 3)
            self.assertTrue((target.parent / f"{target.name}.pre-seq.bak").exists())
            self.assertTrue(all(item.content_hash for item in listed))
            self.assertFalse(target.exists(), msg="legacy JSONL is removed after seq commit")
            seq_files = list(target.parent.glob(f"{target.name}.seq.*"))
            self.assertEqual(len(seq_files), 3)
            restarted = FilesystemReviewEventStore(Path(tmp), fail_closed=True)
            again = restarted.list_for_report(report_id)
            self.assertEqual(len(again), 3)
            self.assertEqual(again[-1].event_type, "accepted")


class D13CoverageTests(unittest.TestCase):
    def test_passport_source_without_entities_still_listed(self) -> None:
        traces = (
            {
                "tool": "run_passport",
                "passport": {
                    "artifact_type": "run_passport",
                    "sources": [
                        {"name": "unread.txt", "disposition": "rejected", "reason": "unparsed"}
                    ],
                },
            },
        )
        cov = coverage_from_report(_report(traces=traces))
        ids = [row.source_id for row in cov.rows]
        self.assertIn("unread.txt", ids)
        unread = next(row for row in cov.rows if row.source_id == "unread.txt")
        statuses = [status for _, status in unread.families]
        self.assertTrue(all(status is not CoverageStatus.CHECKED_OK for status in statuses))


class D14LineageTests(unittest.TestCase):
    def test_unrelated_projects_are_not_same_package(self) -> None:
        left = _report(_issue("a"))
        right = ValidationReport(
            report_id="d" * 32,
            request_id="req2",
            ifc_path=Path("n.ifc"),
            created_at="2026-09-16T00:00:00+00:00",
            requirements=(),
            issues=(),
            summary=ValidationSummary(0, 0, 0, 0, False),
            project_name="other",
            information_container_id="pack-2",
        )
        diff = compare_report_revisions(left, right)
        self.assertEqual(diff.to_dict()["compare_kind"], "unrelated_reports")
        self.assertIn("does NOT claim 'resolved'", diff.to_dict()["note"])

    def test_same_container_is_same_package(self) -> None:
        left = _report(_issue("a"))
        right = _report()
        diff = compare_report_revisions(left, right)
        self.assertEqual(diff.to_dict()["compare_kind"], "same_package")


if __name__ == "__main__":
    unittest.main()
