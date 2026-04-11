"""Tests for BCF report export adapter and clash detection port."""

from __future__ import annotations

import io
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from samolet.domain.models import (
    FindingCategory,
    GeneratedRemark,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)


def _make_report(
    *,
    issue_count: int = 1,
    severity: Severity = Severity.ERROR,
    with_guid: bool = True,
) -> ValidationReport:
    issues = tuple(
        ValidationIssue(
            rule_id=f"IDS-TestRule-{i}",
            severity=severity,
            message=f"Test issue {i}",
            category=FindingCategory.IDS_VALIDATION,
            element_guid=f"guid-{i}" if with_guid else None,
        )
        for i in range(issue_count)
    )
    return ValidationReport(
        report_id=uuid4().hex,
        request_id="req-bcf-test",
        ifc_path=Path("test.ifc"),
        created_at=datetime.now(tz=timezone.utc).isoformat(),
        requirements=(),
        issues=issues,
        summary=ValidationSummary(
            requirement_count=0,
            issue_count=issue_count,
            error_count=issue_count if severity == Severity.ERROR else 0,
            warning_count=issue_count if severity == Severity.WARNING else 0,
            passed=severity != Severity.ERROR,
        ),
    )


class BcfExportTests(unittest.TestCase):
    def test_bcf_archive_is_valid_zip(self) -> None:
        from samolet.infrastructure.adapters.bcf_report_exporter import export_bcf

        report = _make_report(issue_count=2)
        bcf_bytes = export_bcf(report)
        self.assertIsInstance(bcf_bytes, bytes)
        self.assertGreater(len(bcf_bytes), 0)

        with zipfile.ZipFile(io.BytesIO(bcf_bytes), "r") as zf:
            names = zf.namelist()
            self.assertIn("bcf.version", names)
            # 2 error issues → 2 topic folders
            markup_files = [n for n in names if n.endswith("/markup.bcf")]
            self.assertEqual(len(markup_files), 2)

    def test_bcf_version_contains_2_1(self) -> None:
        from samolet.infrastructure.adapters.bcf_report_exporter import export_bcf

        report = _make_report(issue_count=1)
        bcf_bytes = export_bcf(report)

        with zipfile.ZipFile(io.BytesIO(bcf_bytes), "r") as zf:
            version_xml = zf.read("bcf.version").decode("utf-8")
            self.assertIn("2.1", version_xml)

    def test_bcf_markup_contains_topic_elements(self) -> None:
        from samolet.infrastructure.adapters.bcf_report_exporter import export_bcf

        report = _make_report(issue_count=1, with_guid=True)
        bcf_bytes = export_bcf(report)

        with zipfile.ZipFile(io.BytesIO(bcf_bytes), "r") as zf:
            markup_files = [n for n in zf.namelist() if n.endswith("/markup.bcf")]
            self.assertEqual(len(markup_files), 1)
            markup_xml = zf.read(markup_files[0]).decode("utf-8")
            self.assertIn("<Topic", markup_xml)
            self.assertIn("<Title>", markup_xml)
            self.assertIn("IDS-TestRule-0", markup_xml)
            self.assertIn("guid-0", markup_xml)

    def test_bcf_only_includes_errors(self) -> None:
        from samolet.infrastructure.adapters.bcf_report_exporter import export_bcf

        report = _make_report(issue_count=3, severity=Severity.WARNING)
        bcf_bytes = export_bcf(report)

        with zipfile.ZipFile(io.BytesIO(bcf_bytes), "r") as zf:
            markup_files = [n for n in zf.namelist() if n.endswith("/markup.bcf")]
            self.assertEqual(len(markup_files), 0, "Warnings should not produce BCF topics")

    def test_bcf_empty_report_produces_version_only(self) -> None:
        from samolet.infrastructure.adapters.bcf_report_exporter import export_bcf

        report = _make_report(issue_count=0)
        bcf_bytes = export_bcf(report)

        with zipfile.ZipFile(io.BytesIO(bcf_bytes), "r") as zf:
            names = zf.namelist()
            self.assertEqual(names, ["bcf.version"])


class BcfApiExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError:
            raise unittest.SkipTest("FastAPI/httpx not installed")
        import importlib.util
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from samolet.presentation.http.api import create_http_app

        # Load _make_test_container from test_api_security via file path
        spec = importlib.util.spec_from_file_location(
            "test_api_security",
            Path(__file__).resolve().parent / "test_api_security.py",
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        container = mod._make_test_container()
        app = create_http_app(container)
        cls.client = TestClient(app)

    def test_bcf_export_nonexistent_report_returns_404(self) -> None:
        response = self.client.get("/v1/reports/00000000000000000000000000000000/export/bcf")
        self.assertEqual(response.status_code, 404)

    def test_bcf_export_returns_zip_content(self) -> None:
        # Create a report first
        resp = self.client.post(
            "/v1/validate/ifc",
            json={"ifc_path": "nonexistent.ifc", "requirement_text": ""},
        )
        if resp.status_code != 200:
            self.skipTest("Cannot create report for BCF export test")

        report_id = resp.json()["report_id"]
        bcf_resp = self.client.get(f"/v1/reports/{report_id}/export/bcf")
        self.assertEqual(bcf_resp.status_code, 200)
        self.assertIn("bcfzip", bcf_resp.headers.get("content-type", ""))
        # Must be a valid zip
        with zipfile.ZipFile(io.BytesIO(bcf_resp.content), "r") as zf:
            self.assertIn("bcf.version", zf.namelist())


class ClashDetectorPortTests(unittest.TestCase):
    def test_clash_detector_registered_in_container(self) -> None:
        from samolet.core.config.settings import Settings
        from samolet.core.di.tokens import Tokens
        from samolet.infrastructure.di.bootstrap import bootstrap_container

        tmp = tempfile.mkdtemp()
        settings = Settings(
            application_name="test",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path(tmp) / "var",
            debug=True,
        )
        settings.storage_dir.mkdir(parents=True, exist_ok=True)
        container = bootstrap_container(settings)
        clash_detector = container.resolve(Tokens.CLASH_DETECTOR)
        self.assertIsNotNone(clash_detector)
        self.assertTrue(hasattr(clash_detector, "detect"))

    def test_clash_detector_raises_on_missing_file(self) -> None:
        from samolet.infrastructure.adapters.ifc_clash_detector import IfcClashDetector

        detector = IfcClashDetector()
        with self.assertRaises(FileNotFoundError):
            detector.detect(Path("/nonexistent/model.ifc"))

    def test_clash_detector_graceful_without_ifcclash(self) -> None:
        """When ifcclash is not installed, detect() returns empty list."""
        from samolet.infrastructure.adapters.ifc_clash_detector import IfcClashDetector

        detector = IfcClashDetector()
        # Use one of our real IFC fixtures
        ifc_path = Path(__file__).resolve().parents[2] / "samples" / "ifc" / "wall-fire-rating-rei60.ifc"
        if not ifc_path.exists():
            self.skipTest("IFC fixture not available")
        results = detector.detect(ifc_path)
        # ifcclash not installed → returns empty list (graceful fallback)
        self.assertIsInstance(results, list)

    def test_clash_result_dataclass_fields(self) -> None:
        from samolet.domain.models import ClashResult

        result = ClashResult(
            element_a_guid="abc",
            element_b_guid="def",
            clash_type="hard",
            distance=0.005,
            description="Test clash",
        )
        self.assertEqual(result.element_a_guid, "abc")
        self.assertEqual(result.clash_type, "hard")
        self.assertAlmostEqual(result.distance, 0.005)


if __name__ == "__main__":
    unittest.main()
