"""Expert review overlay: T1 in GET/export, T0 stays machine text, summary.passed untouched."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
import zipfile
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
    ReviewEvent,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.domain.review_event_append import ReviewEventAppendSpec
from aerobim.domain.review_projection import (
    FINAL_REMARK_NOTE_PREFIX,
    attach_review_projection,
    bcf_hitl_overlay,
    decode_final_remark_note,
    encode_final_remark_note,
    project_issue_review,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app
from aerobim.presentation.http.report_html import render_report_html
from aerobim.presentation.http.report_pdf import render_report_pdf_bytes


def _events(*, finding_id: str, note: str) -> tuple[ReviewEvent, ReviewEvent]:
    report_id = "r" * 32
    return (
        ReviewEvent(
            event_id="e-open",
            report_id=report_id,
            event_type="opened",
            created_at="2026-09-07T00:00:00+00:00",
            issue_rule_id="FIRE-1",
            finding_id=finding_id,
            resulting_state="opened",
            actor="expert-1",
        ),
        ReviewEvent(
            event_id="e-edit",
            report_id=report_id,
            event_type="edited_remark",
            created_at="2026-09-07T00:01:00+00:00",
            issue_rule_id="FIRE-1",
            finding_id=finding_id,
            note=note,
            resulting_state="edited",
            actor="expert-1",
        ),
    )


class ReviewProjectionUnitTests(unittest.TestCase):
    def test_overlay_keeps_machine_text_and_does_not_touch_passed(self) -> None:
        events = _events(finding_id="fid-a", note="T1")
        issues = [
            {
                "finding_id": "fid-a",
                "rule_id": "FIRE-1",
                "remark": {"title": "m", "body": "T0"},
                "message": "mismatch",
            },
            {
                "finding_id": "fid-b",
                "rule_id": "FIRE-1",
                "remark": {"title": "m", "body": "other-T0"},
                "message": "other",
            },
        ]
        projected = attach_review_projection(issues, events)
        self.assertEqual(projected[0]["remark"]["body"], "T0")
        self.assertEqual(projected[0]["review"]["effective_text"], "T1")
        self.assertEqual(projected[0]["review"]["machine_text"], "T0")
        self.assertEqual(projected[0]["review"]["state"], "edited")
        self.assertEqual(projected[1]["review"]["effective_text"], "other-T0")
        summary = {"passed": False, "issue_count": 2}
        self.assertFalse(summary["passed"])

    def test_final_remark_envelope_preserves_exact_non_empty_suffix(self) -> None:
        exact = "  final text\nsecond line  "
        encoded = encode_final_remark_note(exact)
        self.assertEqual(encoded, f"{FINAL_REMARK_NOTE_PREFIX}{exact}")
        self.assertEqual(decode_final_remark_note(encoded), exact)
        self.assertIsNone(decode_final_remark_note(FINAL_REMARK_NOTE_PREFIX))
        self.assertIsNone(decode_final_remark_note("legacy decision note"))

    def test_enveloped_decision_note_is_effective_final_text(self) -> None:
        for event_type in ("accepted", "rejected"):
            with self.subTest(event_type=event_type):
                exact = f"  final {event_type}\nline 2  "
                decision = ReviewEvent(
                    event_id=f"e-{event_type}",
                    report_id="r" * 32,
                    event_type=event_type,
                    created_at="2026-09-07T00:02:00+00:00",
                    issue_rule_id="FIRE-1",
                    finding_id="fid-a",
                    note=encode_final_remark_note(exact),
                    resulting_state=event_type,
                    actor="expert-1",
                )
                overlay = project_issue_review(
                    finding_id="fid-a",
                    rule_id="FIRE-1",
                    machine_text="T0",
                    events=(*_events(finding_id="fid-a", note="prior edit"), decision),
                )
                self.assertEqual(overlay["effective_text"], exact)
                self.assertEqual(overlay["state"], event_type)

    def test_plain_decision_note_is_legacy_comment_and_keeps_previous_text(self) -> None:
        for event_type in ("accepted", "rejected"):
            for prior_events, expected in (
                (_events(finding_id="fid-a", note="prior edit"), "prior edit"),
                ((_events(finding_id="fid-a", note="unused")[0],), "T0"),
            ):
                with self.subTest(event_type=event_type, expected=expected):
                    decision = ReviewEvent(
                        event_id=f"e-{event_type}",
                        report_id="r" * 32,
                        event_type=event_type,
                        created_at="2026-09-07T00:02:00+00:00",
                        issue_rule_id="FIRE-1",
                        finding_id="fid-a",
                        note="legacy decision comment",
                        resulting_state=event_type,
                        actor="expert-1",
                    )
                    overlay = project_issue_review(
                        finding_id="fid-a",
                        rule_id="FIRE-1",
                        machine_text="T0",
                        events=(*prior_events, decision),
                    )
                    self.assertEqual(overlay["effective_text"], expected)
                    self.assertEqual(overlay["state"], event_type)

    def test_legacy_empty_decision_note_keeps_previous_text(self) -> None:
        for prior_events, expected in (
            (_events(finding_id="fid-a", note="prior edit"), "prior edit"),
            ((_events(finding_id="fid-a", note="unused")[0],), "T0"),
        ):
            with self.subTest(expected=expected):
                decision = ReviewEvent(
                    event_id="e-accepted",
                    report_id="r" * 32,
                    event_type="accepted",
                    created_at="2026-09-07T00:02:00+00:00",
                    issue_rule_id="FIRE-1",
                    finding_id="fid-a",
                    note="",
                    resulting_state="accepted",
                    actor="expert-1",
                )
                overlay = project_issue_review(
                    finding_id="fid-a",
                    rule_id="FIRE-1",
                    machine_text="T0",
                    events=(*prior_events, decision),
                )
                self.assertEqual(overlay["effective_text"], expected)
                self.assertEqual(overlay["state"], "accepted")

    def test_bcf_comment_decodes_enveloped_decision_text(self) -> None:
        issue = ensure_finding_provenance(
            ValidationIssue(
                rule_id="FIRE-1",
                severity=Severity.ERROR,
                message="mismatch",
                category=FindingCategory.IFC_VALIDATION,
                remark=GeneratedRemark(title="Machine", body="T0"),
                origin="deterministic",
            )
        )
        exact = "  exact final\ntext  "
        decision = ReviewEvent(
            event_id="e-accepted",
            report_id="r" * 32,
            event_type="accepted",
            created_at="2026-09-07T00:02:00+00:00",
            issue_rule_id=issue.rule_id,
            finding_id=issue.finding_id,
            note=encode_final_remark_note(exact),
            resulting_state="accepted",
            actor="expert-1",
        )
        overlay = bcf_hitl_overlay(issue, (decision,))
        self.assertEqual(overlay.comments[0].text.split("\nfinding_id=", 1)[0], exact)
        self.assertNotIn(FINAL_REMARK_NOTE_PREFIX, overlay.comments[0].text)

    def test_html_and_pdf_show_effective_text(self) -> None:
        overlay = project_issue_review(
            finding_id="fid-a",
            rule_id="FIRE-1",
            machine_text="T0",
            events=_events(finding_id="fid-a", note="T1"),
        )
        data = {
            "summary": {
                "passed": False,
                "issue_count": 1,
                "error_count": 1,
                "warning_count": 0,
                "requirement_count": 0,
            },
            "issues": [
                {
                    "severity": "error",
                    "priority": 40,
                    "rule_id": "FIRE-1",
                    "message": "mismatch",
                    "finding_id": "fid-a",
                    "source_id": "src-1",
                    "evidence_refs": ["src-1"],
                    "remark": {"title": "m", "body": "T0"},
                    "review": overlay,
                }
            ],
        }
        html = render_report_html("r" * 32, data)
        self.assertIn("effective=T1", html)
        self.assertIn("machine=T0", html)
        pdf = render_report_pdf_bytes("r" * 32, data)
        from test_report_pdf_coverage import extract_pdf_text
        text = extract_pdf_text(pdf)
        self.assertIn("T1", text)
        self.assertIn("T0", text)


class ReviewProjectionHttpTests(unittest.TestCase):
    def test_get_and_exports_include_t1_without_flipping_passed(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="review-proj",
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
            review_store = container.resolve(Tokens.REVIEW_EVENT_STORE)
            ifc_path = settings.storage_dir / "models" / "model.ifc"
            ifc_path.parent.mkdir(parents=True, exist_ok=True)
            ifc_path.write_text("ISO-10303-21;\n", encoding="utf-8")
            report_id = uuid4().hex
            issue = ensure_finding_provenance(
                ValidationIssue(
                    rule_id="FIRE-1",
                    severity=Severity.ERROR,
                    message="mismatch",
                    category=FindingCategory.IFC_VALIDATION,
                    remark=GeneratedRemark(title="Машина", body="T0"),
                    origin="deterministic",
                )
            )
            store.save(
                ValidationReport(
                    report_id=report_id,
                    request_id="rev-proj",
                    ifc_path=ifc_path,
                    created_at=datetime.now(tz=UTC).isoformat(),
                    requirements=(),
                    issues=(issue,),
                    summary=ValidationSummary(0, 1, 1, 0, False),
                )
            )
            review_store.append_api_event(
                ReviewEventAppendSpec(
                    report_id=report_id,
                    event_type="opened",
                    created_at=datetime.now(tz=UTC).isoformat(),
                    issue_rule_id=issue.rule_id,
                    finding_id=issue.finding_id,
                    actor="expert-1",
                    idempotency_key="open-t1",
                )
            )
            review_store.append_api_event(
                ReviewEventAppendSpec(
                    report_id=report_id,
                    event_type="edited_remark",
                    created_at=datetime.now(tz=UTC).isoformat(),
                    issue_rule_id=issue.rule_id,
                    finding_id=issue.finding_id,
                    actor="expert-1",
                    note="T1",
                    previous_state="opened",
                    idempotency_key="edit-t1",
                )
            )
            headers = {"Authorization": "Bearer secret-token"}
            got = client.get(f"/v1/reports/{report_id}", headers=headers)
            self.assertEqual(got.status_code, 200, got.text)
            body = got.json()
            self.assertFalse(body["summary"]["passed"])
            self.assertEqual(body["issues"][0]["remark"]["body"], "T0")
            self.assertEqual(body["issues"][0]["review"]["effective_text"], "T1")
            exported = client.get(f"/v1/reports/{report_id}/export/json", headers=headers)
            self.assertEqual(exported.status_code, 200, exported.text)
            payload = exported.json()
            self.assertFalse(payload["summary"]["passed"])
            self.assertEqual(payload["issues"][0]["review"]["effective_text"], "T1")
            html = client.get(f"/v1/reports/{report_id}/export/html", headers=headers)
            self.assertEqual(html.status_code, 200, html.text)
            self.assertIn("effective=T1", html.text)
            self.assertIn("machine=T0", html.text)

            pdf = client.get(f"/v1/reports/{report_id}/export/pdf", headers=headers)
            self.assertEqual(pdf.status_code, 200, pdf.text)
            from test_report_pdf_coverage import extract_pdf_text
            self.assertIn("T1", extract_pdf_text(pdf.content))
            bcf = client.get(f"/v1/reports/{report_id}/export/bcf", headers=headers)
            self.assertEqual(bcf.status_code, 200, bcf.text)
            with zipfile.ZipFile(io.BytesIO(bcf.content), "r") as archive:
                markup = next(name for name in archive.namelist() if name.endswith("/markup.bcf"))
                xml = archive.read(markup).decode("utf-8")
            self.assertIn("T1", xml)
            self.assertIn("machine_text=T0", xml)


if __name__ == "__main__":
    unittest.main()
