"""WP-R11: export locale ru|en; unknown values are 400."""

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
    GeneratedRemark,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app
from aerobim.presentation.http.report_html import render_report_html


class ExportLocaleRenderTests(unittest.TestCase):
    def test_ru_is_default(self) -> None:
        html = render_report_html(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 1,
                    "error_count": 1,
                    "warning_count": 0,
                    "requirement_count": 0,
                },
                "issues": [
                    {
                        "rule_id": "REQ-FIRE-001",
                        "message": "mismatch",
                        "finding_id": "fid-1",
                        "element_guid": "g1",
                        "target_ref": "W",
                        "evidence_refs": ["g1"],
                        "origin": "deterministic",
                        "gate_class": "regulatory",
                        "remark": {"essence": "Стена", "clause_cite": "СП 2", "clause_bound": True},
                    }
                ],
            },
        )
        self.assertIn('<html lang="ru">', html)
        self.assertIn("Замечания к комплекту", html)
        self.assertIn("finding_id=fid-1", html)

    def test_en_export_has_english_headings_and_essence(self) -> None:
        html = render_report_html(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 1,
                    "error_count": 1,
                    "warning_count": 0,
                    "requirement_count": 0,
                },
                "issues": [
                    {
                        "rule_id": "REQ-FIRE-001",
                        "message": "mismatch",
                        "finding_id": "fid-1",
                        "element_guid": "g1",
                        "target_ref": "W",
                        "evidence_refs": ["g1"],
                        "remark": {
                            "essence": "Wall fire rating mismatch",
                            "clause_cite": "SP 2.13130 cl. 5.4.3",
                            "clause_bound": True,
                            "location_line": "storey 3",
                        },
                    }
                ],
            },
            locale="en",
        )
        self.assertIn('<html lang="en">', html)
        self.assertIn("Pack findings", html)
        self.assertIn("Wall fire rating mismatch", html)
        self.assertIn("Essence", html)

    def test_machine_tokens_are_not_translated(self) -> None:
        html = render_report_html(
            "r" * 32,
            {
                "summary": {
                    "passed": False,
                    "issue_count": 1,
                    "error_count": 1,
                    "warning_count": 0,
                    "requirement_count": 0,
                },
                "issues": [
                    {
                        "rule_id": "REQ-FIRE-001",
                        "message": "mismatch",
                        "finding_id": "fid-1",
                        "origin": "deterministic",
                        "gate_class": "regulatory",
                        "element_guid": "g1",
                        "target_ref": "W",
                        "evidence_refs": ["g1"],
                    }
                ],
            },
            locale="en",
        )
        self.assertIn("finding_id=fid-1", html)
        self.assertIn("origin=deterministic", html)
        self.assertIn("gate=regulatory", html)
        self.assertIn("machine=mismatch", html)


class ExportLocaleHttpTests(unittest.TestCase):
    def test_unknown_locale_is_rejected(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="locale",
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
                    remark=GeneratedRemark(title="Машина", body="T0"),
                    origin="deterministic",
                )
            )
            store.save(
                ValidationReport(
                    report_id=report_id,
                    request_id="loc",
                    ifc_path=ifc_path,
                    created_at=datetime.now(tz=UTC).isoformat(),
                    requirements=(),
                    issues=(issue,),
                    summary=ValidationSummary(0, 1, 1, 0, False),
                )
            )
            headers = {"Authorization": "Bearer secret-token"}
            bad = client.get(f"/v1/reports/{report_id}/export/html?locale=de", headers=headers)
            self.assertEqual(bad.status_code, 400)
            ok = client.get(f"/v1/reports/{report_id}/export/html", headers=headers)
            self.assertEqual(ok.status_code, 200)
            self.assertIn('<html lang="ru">', ok.text)
            en = client.get(f"/v1/reports/{report_id}/export/html?locale=en", headers=headers)
            self.assertEqual(en.status_code, 200)
            self.assertIn('<html lang="en">', en.text)


if __name__ == "__main__":
    unittest.main()
