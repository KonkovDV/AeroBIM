"""HITL replay fingerprint, second edit, ABA version, finding membership."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.finding_provenance import ensure_finding_provenance
from aerobim.domain.models import (
    FindingCategory,
    GeneratedRemark,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.domain.review_event_append import (
    HitlStateConflictError,
    ReviewEventAppendSpec,
    assert_review_target_in_report,
)
from aerobim.domain.review_state_machine import assert_hitl_transition
from aerobim.infrastructure.adapters.filesystem_review_event_store import (
    FilesystemReviewEventStore,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app


def _spec(report_id: str, **overrides: object) -> ReviewEventAppendSpec:
    payload = {
        "report_id": report_id,
        "event_type": "opened",
        "created_at": "2026-09-07T12:00:00+00:00",
        "actor": "expert-1",
        "note": None,
        "finding_id": "fid-a",
        "issue_rule_id": "FIRE-1",
        "previous_state": None,
        "idempotency_key": "k-open",
    }
    payload.update(overrides)
    return ReviewEventAppendSpec(**payload)  # type: ignore[arg-type]


class SecondEditAndReplayTests(unittest.TestCase):
    def test_second_edited_remark_is_a_new_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemReviewEventStore(Path(tmp), fail_closed=True)
            report_id = "a" * 32
            store.append_api_event(_spec(report_id))
            first = store.append_api_event(
                _spec(
                    report_id,
                    event_type="edited_remark",
                    note="T1",
                    previous_state="opened",
                    idempotency_key="k-t1",
                )
            )
            second = store.append_api_event(
                _spec(
                    report_id,
                    event_type="edited_remark",
                    note="T2",
                    previous_state="edited",
                    idempotency_key="k-t2",
                )
            )
            self.assertEqual(first.note, "T1")
            self.assertEqual(second.note, "T2")
            self.assertEqual(len(store.list_for_report(report_id)), 3)
            self.assertEqual(
                assert_hitl_transition(
                    current="edited",
                    event_type="edited_remark",
                    actor="expert-1",
                    note="T2",
                ),
                "edited",
            )

    def test_same_key_same_payload_replays(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemReviewEventStore(Path(tmp), fail_closed=True)
            report_id = "b" * 32
            store.append_api_event(_spec(report_id))
            first = store.append_api_event(
                _spec(
                    report_id,
                    event_type="edited_remark",
                    note="T1",
                    previous_state="opened",
                    idempotency_key="k-same",
                    created_at="2026-09-07T12:01:00+00:00",
                )
            )
            replay = store.append_api_event(
                _spec(
                    report_id,
                    event_type="edited_remark",
                    note="T1",
                    previous_state="opened",
                    idempotency_key="k-same",
                    created_at="2026-09-07T12:02:00+00:00",
                )
            )
            self.assertEqual(first.event_id, replay.event_id)
            self.assertEqual(len(store.list_for_report(report_id)), 2)

    def test_same_key_other_payload_is_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemReviewEventStore(Path(tmp), fail_closed=True)
            report_id = "c" * 32
            store.append_api_event(_spec(report_id))
            store.append_api_event(
                _spec(
                    report_id,
                    event_type="edited_remark",
                    note="T1",
                    previous_state="opened",
                    idempotency_key="k-mix",
                )
            )
            with self.assertRaises(HitlStateConflictError):
                store.append_api_event(
                    _spec(
                        report_id,
                        event_type="edited_remark",
                        note="T2-other-finding",
                        previous_state="opened",
                        finding_id="fid-b",
                        idempotency_key="k-mix",
                    )
                )

    def test_stale_review_version_detects_aba(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemReviewEventStore(Path(tmp), fail_closed=True)
            report_id = "d" * 32
            opened = store.append_api_event(_spec(report_id, idempotency_key="aba-open"))
            self.assertEqual(opened.sequence_number, 1)
            store.append_api_event(
                _spec(
                    report_id,
                    event_type="rejected",
                    note="false positive",
                    previous_state="opened",
                    idempotency_key="aba-rej",
                )
            )
            store.append_api_event(
                _spec(
                    report_id,
                    event_type="opened",
                    note=None,
                    previous_state="rejected",
                    idempotency_key="aba-reopen",
                )
            )
            with self.assertRaises(HitlStateConflictError):
                store.append_api_event(
                    _spec(
                        report_id,
                        event_type="edited_remark",
                        note="stale T1",
                        previous_state="opened",
                        expected_review_version=1,
                        idempotency_key="aba-stale",
                    )
                )


class FindingMembershipTests(unittest.TestCase):
    def test_foreign_finding_is_rejected_when_report_has_issues(self) -> None:
        issue = ensure_finding_provenance(
            ValidationIssue(
                rule_id="FIRE-1",
                severity=Severity.ERROR,
                message="m",
                category=FindingCategory.IFC_VALIDATION,
                remark=GeneratedRemark(title="t", body="T0"),
                origin="deterministic",
            )
        )
        report = ValidationReport(
            report_id="e" * 32,
            request_id="mem",
            ifc_path=Path("m.ifc"),
            created_at="2026-09-07T00:00:00+00:00",
            requirements=(),
            issues=(issue,),
            summary=ValidationSummary(0, 1, 1, 0, False),
        )
        assert_review_target_in_report(
            report, finding_id=issue.finding_id, issue_rule_id=issue.rule_id
        )
        with self.assertRaises(ValueError):
            assert_review_target_in_report(
                report, finding_id="not-this-finding", issue_rule_id=issue.rule_id
            )


class FindingMembershipHttpTests(unittest.TestCase):
    def test_post_unknown_finding_returns_400(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="hitl-member",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
                api_bearer_token="secret-token",
                allow_anonymous_dev=False,
            )
            container = bootstrap_container(settings)
            client = TestClient(create_http_app(container))
            store = container.resolve(Tokens.AUDIT_REPORT_STORE)
            ifc_path = settings.storage_dir / "models" / "model.ifc"
            ifc_path.parent.mkdir(parents=True, exist_ok=True)
            ifc_path.write_text("ISO-10303-21;\n", encoding="utf-8")
            issue = ensure_finding_provenance(
                ValidationIssue(
                    rule_id="FIRE-1",
                    severity=Severity.ERROR,
                    message="m",
                    category=FindingCategory.IFC_VALIDATION,
                    origin="deterministic",
                )
            )
            report_id = uuid4().hex
            store.save(
                ValidationReport(
                    report_id=report_id,
                    request_id="mem-http",
                    ifc_path=ifc_path,
                    created_at=datetime.now(tz=UTC).isoformat(),
                    requirements=(),
                    issues=(issue,),
                    summary=ValidationSummary(0, 1, 1, 0, False),
                )
            )
            response = client.post(
                f"/v1/reports/{report_id}/review-events",
                headers={"Authorization": "Bearer secret-token"},
                json={"event_type": "opened", "finding_id": "missing-finding"},
            )
            self.assertEqual(response.status_code, 400, response.text)


if __name__ == "__main__":
    unittest.main()
