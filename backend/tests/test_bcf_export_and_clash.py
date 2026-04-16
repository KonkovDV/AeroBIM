"""Tests for BCF report export adapter and clash detection port."""

from __future__ import annotations

import io
import sys
import tempfile
import types
import unittest
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from aerobim.domain.models import (
    ClashResult,
    FindingCategory,
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
        created_at=datetime.now(tz=UTC).isoformat(),
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


def _make_report_with_clash() -> ValidationReport:
    report = _make_report(issue_count=1, with_guid=True)
    return ValidationReport(
        report_id=report.report_id,
        request_id=report.request_id,
        ifc_path=report.ifc_path,
        created_at=report.created_at,
        requirements=report.requirements,
        issues=report.issues,
        summary=report.summary,
        drawing_annotations=report.drawing_annotations,
        clash_results=(
            ClashResult(
                element_a_guid="clash-a-guid",
                element_b_guid="clash-b-guid",
                clash_type="hard",
                distance=0.015,
                description="Hard clash between wall and pipe",
            ),
        ),
    )


class BcfExportTests(unittest.TestCase):
    def test_bcf_archive_is_valid_zip(self) -> None:
        from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

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
        from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

        report = _make_report(issue_count=1)
        bcf_bytes = export_bcf(report)

        with zipfile.ZipFile(io.BytesIO(bcf_bytes), "r") as zf:
            version_xml = zf.read("bcf.version").decode("utf-8")
            self.assertIn("2.1", version_xml)

    def test_bcf_markup_contains_topic_elements(self) -> None:
        from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

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

    def test_bcf_markup_references_viewpoint_file(self) -> None:
        from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

        report = _make_report(issue_count=1, with_guid=True)
        bcf_bytes = export_bcf(report)

        with zipfile.ZipFile(io.BytesIO(bcf_bytes), "r") as zf:
            markup_files = [n for n in zf.namelist() if n.endswith("/markup.bcf")]
            viewpoint_files = [n for n in zf.namelist() if n.endswith("/viewpoint.bcfv")]
            self.assertEqual(len(markup_files), 1)
            self.assertEqual(len(viewpoint_files), 1)
            markup_xml = zf.read(markup_files[0]).decode("utf-8")
            self.assertIn("<Viewpoints>", markup_xml)
            self.assertIn("viewpoint.bcfv", markup_xml)

    def test_bcf_viewpoint_contains_camera_and_selected_guid(self) -> None:
        from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

        report = _make_report(issue_count=1, with_guid=True)
        bcf_bytes = export_bcf(report)

        with zipfile.ZipFile(io.BytesIO(bcf_bytes), "r") as zf:
            viewpoint_files = [n for n in zf.namelist() if n.endswith("/viewpoint.bcfv")]
            self.assertEqual(len(viewpoint_files), 1)
            viewpoint_xml = zf.read(viewpoint_files[0]).decode("utf-8")
            self.assertIn("<OrthogonalCamera>", viewpoint_xml)
            self.assertIn("<Selection>", viewpoint_xml)
            self.assertIn('IfcGuid="guid-0"', viewpoint_xml)

    def test_bcf_only_includes_errors(self) -> None:
        from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

        report = _make_report(issue_count=3, severity=Severity.WARNING)
        bcf_bytes = export_bcf(report)

        with zipfile.ZipFile(io.BytesIO(bcf_bytes), "r") as zf:
            markup_files = [n for n in zf.namelist() if n.endswith("/markup.bcf")]
            self.assertEqual(len(markup_files), 0, "Warnings should not produce BCF topics")

    def test_bcf_empty_report_produces_version_only(self) -> None:
        from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

        report = _make_report(issue_count=0)
        bcf_bytes = export_bcf(report)

        with zipfile.ZipFile(io.BytesIO(bcf_bytes), "r") as zf:
            names = zf.namelist()
            self.assertEqual(names, ["bcf.version"])

    def test_bcf_exports_openrebar_cross_document_warning(self) -> None:
        from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

        report = ValidationReport(
            report_id=uuid4().hex,
            request_id="req-openrebar-warning",
            ifc_path=Path("test.ifc"),
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=(),
            issues=(
                ValidationIssue(
                    rule_id="OPENREBAR-PROVENANCE-DIGEST",
                    severity=Severity.WARNING,
                    message="OpenRebar provenance digest mismatch",
                    category=FindingCategory.CROSS_DOCUMENT,
                    target_ref="SLAB-03",
                ),
            ),
            summary=ValidationSummary(
                requirement_count=0,
                issue_count=1,
                error_count=0,
                warning_count=1,
                passed=True,
            ),
        )

        bcf_bytes = export_bcf(report)
        with zipfile.ZipFile(io.BytesIO(bcf_bytes), "r") as zf:
            markup_files = [n for n in zf.namelist() if n.endswith("/markup.bcf")]
            self.assertEqual(len(markup_files), 1)
            markup_xml = zf.read(markup_files[0]).decode("utf-8")
            self.assertIn("OPENREBAR-PROVENANCE-DIGEST", markup_xml)
            self.assertIn("CoordinationWarning", markup_xml)

    def test_bcf_exports_clash_results_as_additional_topics(self) -> None:
        from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

        report = _make_report_with_clash()
        bcf_bytes = export_bcf(report)

        with zipfile.ZipFile(io.BytesIO(bcf_bytes), "r") as zf:
            markup_files = [n for n in zf.namelist() if n.endswith("/markup.bcf")]
            viewpoint_files = [n for n in zf.namelist() if n.endswith("/viewpoint.bcfv")]
            self.assertEqual(len(markup_files), 2)
            self.assertEqual(len(viewpoint_files), 2)
            combined_markup = "\n".join(zf.read(name).decode("utf-8") for name in markup_files)
            self.assertIn("Hard clash between wall and pipe", combined_markup)
            combined_viewpoints = "\n".join(
                zf.read(name).decode("utf-8") for name in viewpoint_files
            )
            self.assertIn('IfcGuid="clash-a-guid"', combined_viewpoints)
            self.assertIn('IfcGuid="clash-b-guid"', combined_viewpoints)


class BcfApiExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        import importlib.util
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from aerobim.core.di.tokens import Tokens
        from aerobim.presentation.http.api import create_http_app

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
        cls.store = container.resolve(Tokens.AUDIT_REPORT_STORE)

    def test_bcf_export_nonexistent_report_returns_404(self) -> None:
        response = self.client.get("/v1/reports/00000000000000000000000000000000/export/bcf")
        self.assertEqual(response.status_code, 404)

    def test_bcf_export_returns_zip_content(self) -> None:
        report = _make_report(issue_count=1, with_guid=True)
        self.store.save(report)
        report_id = report.report_id
        bcf_resp = self.client.get(f"/v1/reports/{report_id}/export/bcf")
        self.assertEqual(bcf_resp.status_code, 200)
        self.assertIn("bcfzip", bcf_resp.headers.get("content-type", ""))
        # Must be a valid zip
        with zipfile.ZipFile(io.BytesIO(bcf_resp.content), "r") as zf:
            self.assertIn("bcf.version", zf.namelist())


class ClashDetectorPortTests(unittest.TestCase):
    def test_clash_detector_registered_in_container(self) -> None:
        from aerobim.core.config.settings import Settings
        from aerobim.core.di.tokens import Tokens
        from aerobim.infrastructure.di.bootstrap import bootstrap_container

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
        from aerobim.infrastructure.adapters.ifc_clash_detector import IfcClashDetector

        detector = IfcClashDetector()
        with self.assertRaises(FileNotFoundError):
            detector.detect(Path("/nonexistent/model.ifc"))

    def test_clash_detector_graceful_without_ifcclash(self) -> None:
        """When ifcclash is not installed, detect() returns empty list."""
        from aerobim.infrastructure.adapters.ifc_clash_detector import IfcClashDetector

        detector = IfcClashDetector()
        # Use one of our real IFC fixtures
        ifc_path = (
            Path(__file__).resolve().parents[2] / "samples" / "ifc" / "wall-fire-rating-rei60.ifc"
        )
        if not ifc_path.exists():
            self.skipTest("IFC fixture not available")
        results = detector.detect(ifc_path)
        # ifcclash not installed → returns empty list (graceful fallback)
        self.assertIsInstance(results, list)

    def test_clash_detector_runtime_failure_falls_back_to_empty(self) -> None:
        from aerobim.infrastructure.adapters.ifc_clash_detector import IfcClashDetector

        detector = IfcClashDetector()
        ifc_path = (
            Path(__file__).resolve().parents[2] / "samples" / "ifc" / "wall-fire-rating-rei60.ifc"
        )
        if not ifc_path.exists():
            self.skipTest("IFC fixture not available")

        with patch.object(detector, "_run_clash_detection", side_effect=AssertionError("geom init failed")):
            results = detector.detect(ifc_path)

        self.assertEqual(results, [])

    def test_clash_detector_cleans_temporary_output_directory(self) -> None:
        from aerobim.infrastructure.adapters.ifc_clash_detector import IfcClashDetector

        detector = IfcClashDetector()
        ifc_path = (
            Path(__file__).resolve().parents[2] / "samples" / "ifc" / "wall-fire-rating-rei60.ifc"
        )
        if not ifc_path.exists():
            self.skipTest("IFC fixture not available")

        tracked_dir = Path(tempfile.mkdtemp(prefix="aerobim-clash-test-")) / "tracked-output"
        tracked_dir.mkdir(parents=True, exist_ok=True)

        fake_package = types.ModuleType("ifcclash")
        fake_submodule = types.ModuleType("ifcclash.ifcclash")

        class _FakeClashSettings:
            def __init__(self) -> None:
                self.output = ""

        class _FakeClasher:
            def __init__(self, settings: _FakeClashSettings) -> None:
                self.settings = settings
                self.clash_sets: list[dict[str, object]] = []

            def clash(self) -> None:
                self.clash_sets = [{"clashes": {}}]

        fake_submodule.ClashSettings = _FakeClashSettings
        fake_submodule.Clasher = _FakeClasher
        fake_package.ifcclash = fake_submodule

        try:
            with patch("tempfile.TemporaryDirectory") as temp_dir_factory:
                temp_dir_factory.return_value.__enter__.return_value = str(tracked_dir)
                temp_dir_factory.return_value.__exit__.side_effect = (
                    lambda exc_type, exc, tb: tracked_dir.rmdir()
                )

                with patch.dict(
                    sys.modules,
                    {
                        "ifcclash": fake_package,
                        "ifcclash.ifcclash": fake_submodule,
                    },
                ):
                    detector.detect(ifc_path)

            self.assertFalse(tracked_dir.exists())
        finally:
            if tracked_dir.exists():
                tracked_dir.rmdir()

    def test_clash_result_dataclass_fields(self) -> None:
        from aerobim.domain.models import ClashResult

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
