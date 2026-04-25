"""Tests for BCF 3.0 experimental exporter (bcf3_exporter.py).

Verifies:
- ZIP archive structure matches BCF 3.0 layout.
- ``bcf.version`` declares VersionId=3.0.
- ``markup.bcf`` uses BCF 3.0 element structure (no namespace, Comments, Viewpoints).
- ``viewpoint.bcfv`` uses BCF 3.0 structure (no namespace, Guid attr, Coloring before Visibility).
- IFC GUID is propagated to the viewpoint component selection.
- Clash topics are exported correctly in BCF 3.0 format.
- HTTP endpoint responds with BCF 3.0 bytes when ``?version=3`` is supplied.
"""

from __future__ import annotations

import io
import unittest
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree as ET

from aerobim.domain.models import (
    ClashResult,
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.infrastructure.adapters.bcf3_exporter import export_bcf3


def _make_report(
    *,
    issue_count: int = 1,
    severity: Severity = Severity.ERROR,
    with_guid: bool = True,
) -> ValidationReport:
    issues = tuple(
        ValidationIssue(
            rule_id=f"IDS-Rule-{i}",
            severity=severity,
            message=f"BCF3 test issue {i}",
            category=FindingCategory.IDS_VALIDATION,
            element_guid=f"bcf3guid{i:04d}" if with_guid else None,
        )
        for i in range(issue_count)
    )
    return ValidationReport(
        report_id=uuid4().hex,
        request_id="req-bcf3-test",
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
    clash = ClashResult(
        element_a_guid="clashguidA001",
        element_b_guid="clashguidB001",
        clash_type="HardClash",
        description="Beam penetrates wall",
        distance=-0.05,
    )
    return ValidationReport(
        **{
            **report.__dict__,
            "clash_results": (clash,),
        }
    )


class Bcf3ArchiveStructureTests(unittest.TestCase):
    def test_export_returns_bytes(self) -> None:
        report = _make_report()
        result = export_bcf3(report)
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 0)

    def test_archive_is_valid_zip(self) -> None:
        report = _make_report()
        result = export_bcf3(report)
        self.assertTrue(zipfile.is_zipfile(io.BytesIO(result)))

    def test_bcf_version_file_present(self) -> None:
        report = _make_report()
        result = export_bcf3(report)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            self.assertIn("bcf.version", zf.namelist())

    def test_bcf_version_declares_30(self) -> None:
        report = _make_report()
        result = export_bcf3(report)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            version_xml = zf.read("bcf.version").decode("utf-8")

        root = ET.fromstring(version_xml.split("\n", 1)[-1])
        self.assertEqual("3.0", root.get("VersionId"))
        detail = root.find("DetailedVersion")
        self.assertIsNotNone(detail)
        self.assertEqual("3.0", detail.text)  # type: ignore[union-attr]

    def test_topic_directory_and_markup_created(self) -> None:
        report = _make_report(issue_count=1, severity=Severity.ERROR)
        result = export_bcf3(report)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            markup_entries = [n for n in zf.namelist() if n.endswith("markup.bcf")]
        self.assertEqual(1, len(markup_entries))

    def test_viewpoint_file_created(self) -> None:
        report = _make_report(issue_count=1, severity=Severity.ERROR)
        result = export_bcf3(report)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            vp_entries = [n for n in zf.namelist() if n.endswith("viewpoint.bcfv")]
        self.assertEqual(1, len(vp_entries))

    def test_no_topics_for_info_severity(self) -> None:
        report = _make_report(issue_count=3, severity=Severity.INFO)
        result = export_bcf3(report)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            markup_entries = [n for n in zf.namelist() if n.endswith("markup.bcf")]
        self.assertEqual(0, len(markup_entries))


class Bcf3MarkupStructureTests(unittest.TestCase):
    def _get_markup_root(self, report: ValidationReport) -> ET.Element:
        result = export_bcf3(report)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            markup_entries = [n for n in zf.namelist() if n.endswith("markup.bcf")]
            xml_str = zf.read(markup_entries[0]).decode("utf-8")
        return ET.fromstring(xml_str.split("\n", 1)[-1])

    def test_markup_root_is_markup_no_namespace(self) -> None:
        root = self._get_markup_root(_make_report())
        self.assertEqual("Markup", root.tag)

    def test_topic_has_required_bcf30_children(self) -> None:
        root = self._get_markup_root(_make_report())
        topic = root.find("Topic")
        self.assertIsNotNone(topic)
        assert topic is not None  # satisfy type narrowing
        for child_name in ("Title", "CreationDate", "CreationAuthor", "Description"):
            self.assertIsNotNone(
                topic.find(child_name),
                msg=f"Missing BCF 3.0 required field: {child_name}",
            )

    def test_comments_element_present(self) -> None:
        root = self._get_markup_root(_make_report())
        comments = root.find("Comments")
        self.assertIsNotNone(comments, msg="BCF 3.0 requires <Comments> element")

    def test_viewpoints_element_present(self) -> None:
        root = self._get_markup_root(_make_report())
        viewpoints = root.find("Viewpoints")
        self.assertIsNotNone(viewpoints, msg="BCF 3.0 requires <Viewpoints> element")

    def test_viewpoint_has_guid_attribute(self) -> None:
        root = self._get_markup_root(_make_report())
        vp = root.find(".//ViewPoint")
        self.assertIsNotNone(vp)
        assert vp is not None
        self.assertIsNotNone(vp.get("Guid"), msg="BCF 3.0 ViewPoint must have Guid attr")

    def test_topic_type_is_error_for_error_severity(self) -> None:
        root = self._get_markup_root(_make_report(severity=Severity.ERROR))
        topic = root.find("Topic")
        assert topic is not None
        self.assertEqual("Error", topic.get("TopicType"))

    def test_topic_type_is_warning_for_warning_cross_doc(self) -> None:
        issue = ValidationIssue(
            rule_id="OPENREBAR-DIGEST-001",
            severity=Severity.WARNING,
            message="Cross-doc warning",
            category=FindingCategory.CROSS_DOCUMENT,
            element_guid="guidWarn001",
        )
        report = ValidationReport(
            report_id=uuid4().hex,
            request_id="req-warn",
            ifc_path=Path("test.ifc"),
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=(),
            issues=(issue,),
            summary=ValidationSummary(0, 1, 0, 1, True),
        )
        root = self._get_markup_root(report)
        topic = root.find("Topic")
        assert topic is not None
        self.assertEqual("Warning", topic.get("TopicType"))


class Bcf3ViewpointStructureTests(unittest.TestCase):
    def _get_viewpoint_root(self, report: ValidationReport) -> ET.Element:
        result = export_bcf3(report)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            vp_entries = [n for n in zf.namelist() if n.endswith("viewpoint.bcfv")]
            xml_str = zf.read(vp_entries[0]).decode("utf-8")
        return ET.fromstring(xml_str.split("\n", 1)[-1])

    def test_viewpoint_root_has_guid_attribute(self) -> None:
        root = self._get_viewpoint_root(_make_report())
        self.assertIsNotNone(root.get("Guid"))

    def test_viewpoint_root_has_no_namespace(self) -> None:
        root = self._get_viewpoint_root(_make_report())
        self.assertFalse(root.tag.startswith("{"), msg="BCF 3.0 visinfo must not use namespace")

    def test_coloring_before_visibility(self) -> None:
        """BCF 3.0 XSD requires Coloring before Visibility in Components."""
        root = self._get_viewpoint_root(_make_report())
        components = root.find("Components")
        self.assertIsNotNone(components)
        assert components is not None
        children = [c.tag for c in components]
        coloring_idx = children.index("Coloring") if "Coloring" in children else -1
        visibility_idx = children.index("Visibility") if "Visibility" in children else -1
        self.assertGreater(coloring_idx, -1, msg="Coloring element missing from Components")
        self.assertGreater(visibility_idx, -1, msg="Visibility element missing from Components")
        self.assertLess(coloring_idx, visibility_idx, msg="Coloring must precede Visibility")

    def test_ifc_guid_propagated_to_selection(self) -> None:
        report = _make_report(with_guid=True)
        root = self._get_viewpoint_root(report)
        components = root.find("Components")
        assert components is not None
        selection = components.find("Selection")
        self.assertIsNotNone(selection)
        assert selection is not None
        component = selection.find("Component")
        self.assertIsNotNone(component)
        assert component is not None
        self.assertEqual("bcf3guid0000", component.get("IfcGuid"))

    def test_orthogonal_camera_present(self) -> None:
        root = self._get_viewpoint_root(_make_report())
        self.assertIsNotNone(root.find("OrthogonalCamera"))


class Bcf3ClashExportTests(unittest.TestCase):
    def test_clash_topic_exported(self) -> None:
        report = _make_report_with_clash()
        result = export_bcf3(report)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            markup_entries = [n for n in zf.namelist() if n.endswith("markup.bcf")]
        # 1 error issue + 1 clash = 2 topics
        self.assertEqual(2, len(markup_entries))

    def test_clash_topic_type_is_clash(self) -> None:
        report = _make_report_with_clash()
        result = export_bcf3(report)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            markup_entries = [n for n in zf.namelist() if n.endswith("markup.bcf")]
            clash_markup = None
            for entry in markup_entries:
                xml_str = zf.read(entry).decode("utf-8")
                root = ET.fromstring(xml_str.split("\n", 1)[-1])
                topic = root.find("Topic")
                if topic is not None and topic.get("TopicType") == "Clash":
                    clash_markup = root
                    break
        self.assertIsNotNone(clash_markup, msg="No Clash topic found in BCF 3.0 export")


class Bcf3HttpEndpointTests(unittest.TestCase):
    """Integration tests for the ?version=3 query parameter on the BCF endpoint."""

    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError:
            return

        import tempfile

        from aerobim.core.config.settings import Settings
        from aerobim.core.di.tokens import Tokens
        from aerobim.domain.models import ValidationSummary
        from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
        from aerobim.infrastructure.di.bootstrap import bootstrap_container
        from aerobim.presentation.http.api import create_http_app

        cls._tmp = tempfile.TemporaryDirectory()
        settings = Settings(
            application_name="aerobim-test-bcf3",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path(cls._tmp.name),
            debug=True,
        )
        settings.storage_dir.mkdir(parents=True, exist_ok=True)
        container = bootstrap_container(settings)
        cls._app = create_http_app(container)
        cls._client = TestClient(cls._app)

        # Seed a report in the audit store
        store: InMemoryAuditStore = container.resolve(Tokens.AUDIT_REPORT_STORE)
        report = ValidationReport(
               report_id="bcf3cafe1234567890abcdef12345678",
            request_id="req-bcf3-http",
            ifc_path=Path("test.ifc"),
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=(),
            issues=(
                ValidationIssue(
                    rule_id="IDS-HTTP-01",
                    severity=Severity.ERROR,
                    message="HTTP BCF3 test",
                    category=FindingCategory.IDS_VALIDATION,
                    element_guid="httpguid0001",
                ),
            ),
            summary=ValidationSummary(0, 1, 1, 0, False),
        )
        store.save(report)
        cls._report_id = report.report_id

    @classmethod
    def tearDownClass(cls) -> None:
        if hasattr(cls, "_tmp"):
            cls._tmp.cleanup()

    def setUp(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("FastAPI/httpx not installed")
        if not hasattr(self.__class__, "_client"):
            self.skipTest("setUpClass did not initialise client")

    def test_default_version_returns_21_zip(self) -> None:
        response = self._client.get(f"/v1/reports/{self._report_id}/export/bcf")
        self.assertEqual(200, response.status_code)
        content = response.content
        self.assertTrue(zipfile.is_zipfile(io.BytesIO(content)))
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            version_xml = zf.read("bcf.version").decode("utf-8")
        self.assertIn("2.1", version_xml)

    def test_version_3_returns_bcf30_zip(self) -> None:
        response = self._client.get(
            f"/v1/reports/{self._report_id}/export/bcf?version=3"
        )
        self.assertEqual(200, response.status_code)
        content = response.content
        self.assertTrue(zipfile.is_zipfile(io.BytesIO(content)))
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            version_xml = zf.read("bcf.version").decode("utf-8")
        self.assertIn("3.0", version_xml)

    def test_version_30_alias_returns_bcf30_zip(self) -> None:
        response = self._client.get(
            f"/v1/reports/{self._report_id}/export/bcf?version=3.0"
        )
        self.assertEqual(200, response.status_code)
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            version_xml = zf.read("bcf.version").decode("utf-8")
        self.assertIn("3.0", version_xml)

    def test_unknown_version_defaults_to_21(self) -> None:
        response = self._client.get(
            f"/v1/reports/{self._report_id}/export/bcf?version=99"
        )
        self.assertEqual(200, response.status_code)
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            version_xml = zf.read("bcf.version").decode("utf-8")
        self.assertIn("2.1", version_xml)
