"""WP-R12: HTML revision section; honesty sentence; same id rejected."""

from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.finding_provenance import ensure_finding_provenance
from aerobim.domain.models import (
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app
from aerobim.presentation.http.report_html import render_report_html


class ExportRevisionSectionRenderTests(unittest.TestCase):
    def test_section_absent_without_against(self) -> None:
        html = render_report_html(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 0,
                    "error_count": 0,
                    "warning_count": 0,
                    "requirement_count": 0,
                },
                "issues": [],
            },
        )
        self.assertNotIn("id='revision-diff'", html)
        self.assertNotIn("Сравнение с ревизией", html)

    def test_no_longer_reported_carries_the_honesty_sentence(self) -> None:
        html = render_report_html(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 1,
                    "error_count": 0,
                    "warning_count": 1,
                    "requirement_count": 0,
                },
                "issues": [],
                "revision_diff": {
                    "newly_reported": ["fid:new"],
                    "still_reported": ["fid:stay"],
                    "no_longer_reported": ["fid:old"],
                },
            },
        )
        self.assertIn("id='revision-diff'", html)
        self.assertIn("не означает", html)
        self.assertIn("не воспроизведено", html)


class ExportRevisionAgainstHttpTests(unittest.TestCase):
    def test_same_report_id_is_rejected(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="rev",
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
            report_id = uuid4().hex
            issue = ensure_finding_provenance(
                ValidationIssue(
                    rule_id="FIRE-1",
                    severity=Severity.ERROR,
                    message="mismatch",
                    category=FindingCategory.IFC_VALIDATION,
                )
            )
            store.save(
                ValidationReport(
                    report_id=report_id,
                    request_id="rev",
                    ifc_path=ifc_path,
                    created_at=datetime.now(tz=UTC).isoformat(),
                    requirements=(),
                    issues=(issue,),
                    summary=ValidationSummary(0, 1, 1, 0, False),
                )
            )
            headers = {"Authorization": "Bearer secret-token"}
            response = client.get(
                f"/v1/reports/{report_id}/export/html?against={report_id}",
                headers=headers,
            )
            self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
