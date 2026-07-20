"""TZ P0 — upload ingest, EN remarks, review-event wiring smoke."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.core.config.settings import Settings
from aerobim.domain.models import (
    ComparisonOperator,
    FindingCategory,
    Severity,
    ValidationIssue,
)
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app


class EnRemarkTemplateTests(unittest.TestCase):
    def test_english_locale_templates(self) -> None:
        generator = TemplateRemarkGenerator(locale="en")
        issue = ValidationIssue(
            rule_id="QTO-001",
            severity=Severity.ERROR,
            message="Area mismatch",
            ifc_entity="IFCSPACE",
            category=FindingCategory.IFC_VALIDATION,
            property_set="Qto_SpaceBaseQuantities",
            property_name="NetFloorArea",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value="25",
            observed_value="20",
            unit="m2",
        )
        remark = generator.generate(issue)
        self.assertIn("Model remark", remark.title)
        self.assertIn("at least", remark.body)
        self.assertNotIn("не менее", remark.body)


class UploadApiTests(unittest.TestCase):
    def test_multipart_upload_returns_storage_path(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="aerobim-test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
                allow_anonymous_dev=True,
            )
            container = bootstrap_container(settings)
            client = TestClient(create_http_app(container))
            response = client.post(
                "/v1/uploads",
                files={"file": ("pilot.ifc", b"ISO-10303-21;", "application/octet-stream")},
            )
            self.assertEqual(response.status_code, 200, response.text)
            body = response.json()
            self.assertEqual(body["filename"], "pilot.ifc")
            path = body["path"]
            self.assertTrue(
                path.startswith("tenants/anonymous-dev/uploads/")
                or path.startswith("tenants/anonymous/uploads/"),
                path,
            )
            self.assertEqual(body["size_bytes"], len(b"ISO-10303-21;"))
            stored = Path(tmp) / body["path"]
            self.assertTrue(stored.is_file())
            self.assertEqual(stored.read_bytes(), b"ISO-10303-21;")


if __name__ == "__main__":
    unittest.main()
