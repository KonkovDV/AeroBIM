"""Supplemental edge-case tests covering remaining audit-identified gaps.

A: FilesystemAuditStore malformed JSON resilience
B: ValidateIfcAgainstIdsUseCase with IDS path
C: AnalyzeProjectPackageUseCase — _compare_values operator branches
D: API CORS preflight and correlation header propagation
E: Drawing dimension pattern in NarrativeRuleSynthesizer
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ---------------------------------------------------------------------------
# A: FilesystemAuditStore — malformed JSON resilience
# ---------------------------------------------------------------------------

class FilesystemStoreResilienceTests(unittest.TestCase):
    def test_get_returns_none_for_corrupt_json(self) -> None:
        from samolet.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore

        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemAuditStore(Path(tmp))
            reports_dir = Path(tmp) / "reports"
            reports_dir.mkdir(exist_ok=True)
            (reports_dir / "bad-report.json").write_text("not valid json {{{", encoding="utf-8")

            result = store.get("bad-report")
            self.assertIsNone(result, "Corrupt JSON should return None, not raise")

    def test_get_returns_none_for_missing_keys(self) -> None:
        from samolet.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore

        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemAuditStore(Path(tmp))
            reports_dir = Path(tmp) / "reports"
            reports_dir.mkdir(exist_ok=True)
            # Valid JSON but missing required fields
            (reports_dir / "incomplete.json").write_text('{"foo": "bar"}', encoding="utf-8")

            result = store.get("incomplete")
            self.assertIsNone(result, "Missing keys should return None, not KeyError")

    def test_list_reports_skips_corrupt_files(self) -> None:
        from samolet.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore, FilesystemAuditStore as FS
        from samolet.domain.models import ValidationReport, ValidationSummary

        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemAuditStore(Path(tmp))
            # Save one valid report
            store.save(ValidationReport(
                report_id="good",
                request_id="req",
                ifc_path=Path("x.ifc"),
                created_at="2026-01-01T00:00:00Z",
                requirements=(),
                issues=(),
                summary=ValidationSummary(
                    requirement_count=0, issue_count=0,
                    error_count=0, warning_count=0, passed=True,
                ),
            ))
            # Write a corrupt file next to it
            reports_dir = Path(tmp) / "reports"
            (reports_dir / "corrupt.json").write_text("{invalid", encoding="utf-8")

            entries = store.list_reports()
            self.assertEqual(len(entries), 1, "Should skip corrupt, return only valid")
            self.assertEqual(entries[0].report_id, "good")


# ---------------------------------------------------------------------------
# B: ValidateIfcAgainstIdsUseCase — IDS + requirement combined path
# ---------------------------------------------------------------------------

class ValidateWithIdsPathTests(unittest.TestCase):
    def test_ids_issues_combined_with_requirement_issues(self) -> None:
        from samolet.application.use_cases.validate_ifc_against_ids import ValidateIfcAgainstIdsUseCase
        from samolet.domain.models import (
            ParsedRequirement, RequirementSource, Severity,
            ValidationIssue, ValidationReport, ValidationRequest, ValidationSummary,
        )

        class StubExtractor:
            def extract(self, _src):
                return [ParsedRequirement(rule_id="R1", ifc_entity="IFCWALL",
                                          property_set="Pset_WallCommon",
                                          property_name="FireRating",
                                          expected_value="REI60")]

        class StubIfcValidator:
            def validate(self, _path, _reqs):
                return [ValidationIssue(rule_id="R1", severity=Severity.ERROR,
                                        message="IFC mismatch")]

        class StubIdsValidator:
            def validate(self, _ids_path, _ifc_path):
                return [ValidationIssue(rule_id="IDS-1", severity=Severity.WARNING,
                                        message="IDS violation")]

        class StubStore:
            saved = None
            def save(self, report):
                self.saved = report
                return report.report_id

        store = StubStore()
        uc = ValidateIfcAgainstIdsUseCase(
            requirement_extractor=StubExtractor(),
            ifc_validator=StubIfcValidator(),
            audit_report_store=store,
            ids_validator=StubIdsValidator(),
        )

        report = uc.execute(ValidationRequest(
            request_id="req-ids",
            ifc_path=Path("model.ifc"),
            requirement_source=RequirementSource(text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60"),
            ids_path=Path("rules.ids"),
        ))

        self.assertEqual(report.summary.issue_count, 2, "Should combine IFC + IDS issues")
        self.assertEqual(report.summary.error_count, 1)
        self.assertEqual(report.summary.warning_count, 1)
        self.assertFalse(report.summary.passed)

    def test_no_requirements_and_no_ids_raises(self) -> None:
        from samolet.application.use_cases.validate_ifc_against_ids import ValidateIfcAgainstIdsUseCase
        from samolet.domain.models import RequirementSource, ValidationRequest

        class EmptyExtractor:
            def extract(self, _src):
                return []

        class NoOpValidator:
            def validate(self, *_args):
                return []

        class DummyStore:
            def save(self, report):
                return report.report_id

        uc = ValidateIfcAgainstIdsUseCase(
            requirement_extractor=EmptyExtractor(),
            ifc_validator=NoOpValidator(),
            audit_report_store=DummyStore(),
        )

        with self.assertRaises(ValueError):
            uc.execute(ValidationRequest(
                request_id="empty",
                ifc_path=Path("model.ifc"),
                requirement_source=RequirementSource(text=""),
            ))


# ---------------------------------------------------------------------------
# C: AnalyzeProjectPackageUseCase — cross-document + drawing validation
# ---------------------------------------------------------------------------

class CompareValuesTests(unittest.TestCase):
    """Test the _compare_values helper in AnalyzeProjectPackageUseCase."""

    def _make_uc(self, tolerance=None):
        from samolet.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase as UC
        from samolet.domain.models import ToleranceConfig
        uc = UC.__new__(UC)
        uc._tolerance = tolerance or ToleranceConfig()
        return uc

    def test_lte_operator(self) -> None:
        from samolet.domain.models import ComparisonOperator
        uc = self._make_uc()
        self.assertTrue(uc._compare_values("100", "200", ComparisonOperator.LESS_OR_EQUAL))
        self.assertTrue(uc._compare_values("200", "200", ComparisonOperator.LESS_OR_EQUAL))
        self.assertFalse(uc._compare_values("300", "200", ComparisonOperator.LESS_OR_EQUAL))

    def test_gte_operator(self) -> None:
        from samolet.domain.models import ComparisonOperator
        uc = self._make_uc()
        self.assertTrue(uc._compare_values("200", "100", ComparisonOperator.GREATER_OR_EQUAL))
        self.assertFalse(uc._compare_values("50", "100", ComparisonOperator.GREATER_OR_EQUAL))

    def test_equals_operator(self) -> None:
        from samolet.domain.models import ComparisonOperator
        uc = self._make_uc()
        self.assertTrue(uc._compare_values("REI60", "REI60", ComparisonOperator.EQUALS))
        self.assertFalse(uc._compare_values("REI90", "REI60", ComparisonOperator.EQUALS))

    def test_exists_operator(self) -> None:
        from samolet.domain.models import ComparisonOperator
        uc = self._make_uc()
        self.assertTrue(uc._compare_values("anything", None, ComparisonOperator.EXISTS))
        self.assertFalse(uc._compare_values(None, None, ComparisonOperator.EXISTS))

    def test_non_numeric_gte_falls_back_to_string_equality(self) -> None:
        from samolet.domain.models import ComparisonOperator
        uc = self._make_uc()
        self.assertTrue(uc._compare_values("abc", "abc", ComparisonOperator.GREATER_OR_EQUAL))
        self.assertFalse(uc._compare_values("abc", "xyz", ComparisonOperator.GREATER_OR_EQUAL))

    def test_none_observed_returns_false(self) -> None:
        from samolet.domain.models import ComparisonOperator
        uc = self._make_uc()
        self.assertFalse(uc._compare_values(None, "100", ComparisonOperator.EQUALS))

    # -- Fuzzy tolerance tests (ISO 12006-3 aligned) --

    def test_fuzzy_equals_within_length_epsilon(self) -> None:
        """200.0005 ≈ 200.0 within default length_epsilon=0.001 mm."""
        from samolet.domain.models import ComparisonOperator
        uc = self._make_uc()
        self.assertTrue(
            uc._compare_values("200.0005", "200.0", ComparisonOperator.EQUALS, unit="mm")
        )

    def test_fuzzy_equals_outside_length_epsilon(self) -> None:
        """200.5 ≠ 200.0 — well outside 0.001 epsilon."""
        from samolet.domain.models import ComparisonOperator
        uc = self._make_uc()
        self.assertFalse(
            uc._compare_values("200.5", "200.0", ComparisonOperator.EQUALS, unit="mm")
        )

    def test_fuzzy_gte_within_epsilon_boundary(self) -> None:
        """199.9995 is within ε of 200.0 for GTE (passes with tolerance)."""
        from samolet.domain.models import ComparisonOperator
        uc = self._make_uc()
        self.assertTrue(
            uc._compare_values("199.9995", "200.0", ComparisonOperator.GREATER_OR_EQUAL, unit="mm")
        )

    def test_fuzzy_lte_within_epsilon_boundary(self) -> None:
        """200.0005 is within ε of 200.0 for LTE (passes with tolerance)."""
        from samolet.domain.models import ComparisonOperator
        uc = self._make_uc()
        self.assertTrue(
            uc._compare_values("200.0005", "200.0", ComparisonOperator.LESS_OR_EQUAL, unit="mm")
        )

    def test_fuzzy_area_unit(self) -> None:
        """42.005 ≈ 42.0 within area_epsilon=0.01 m²."""
        from samolet.domain.models import ComparisonOperator
        uc = self._make_uc()
        self.assertTrue(
            uc._compare_values("42.005", "42.0", ComparisonOperator.EQUALS, unit="м2")
        )
        self.assertFalse(
            uc._compare_values("42.05", "42.0", ComparisonOperator.EQUALS, unit="м2")
        )

    def test_fuzzy_custom_tolerance(self) -> None:
        """Custom tolerance: 1.0 epsilon makes 200.5 ≈ 200.0."""
        from samolet.domain.models import ComparisonOperator, ToleranceConfig
        custom = ToleranceConfig(length_epsilon=1.0)
        uc = self._make_uc(tolerance=custom)
        self.assertTrue(
            uc._compare_values("200.5", "200.0", ComparisonOperator.EQUALS, unit="mm")
        )

    def test_no_unit_uses_default_epsilon(self) -> None:
        """Without unit, default_epsilon=1e-6 applies."""
        from samolet.domain.models import ComparisonOperator
        uc = self._make_uc()
        self.assertTrue(
            uc._compare_values("42.0000005", "42.0", ComparisonOperator.EQUALS)
        )
        self.assertFalse(
            uc._compare_values("42.001", "42.0", ComparisonOperator.EQUALS)
        )


# ---------------------------------------------------------------------------
# D: API CORS + correlation integration
# ---------------------------------------------------------------------------

class ApiCorsAndCorrelationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError:
            raise unittest.SkipTest("FastAPI/httpx not installed")

        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "test_api_security",
            Path(__file__).resolve().parent / "test_api_security.py",
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        container = mod._make_test_container()

        from samolet.presentation.http.api import create_http_app
        app = create_http_app(container)
        cls.client = TestClient(app)

    def test_correlation_id_auto_generated(self) -> None:
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        cid = resp.headers.get("X-Request-ID", "")
        self.assertEqual(len(cid), 32, "Should be a uuid4 hex")

    def test_correlation_id_passthrough(self) -> None:
        custom_id = "my-trace-id-12345"
        resp = self.client.get("/health", headers={"X-Request-ID": custom_id})
        self.assertEqual(resp.headers.get("X-Request-ID"), custom_id)

    def test_cors_preflight_health(self) -> None:
        resp = self.client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # In debug mode, allow_origins=["*"]
        self.assertIn("access-control-allow-origin", resp.headers)


# ---------------------------------------------------------------------------
# E: Narrative synthesizer — drawing dimension pattern
# ---------------------------------------------------------------------------

class DrawingDimensionPatternTests(unittest.TestCase):
    def test_drawing_dimension_russian(self) -> None:
        from samolet.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
        from samolet.domain.models import RequirementSource, RuleScope, SourceKind, ComparisonOperator

        synthesizer = NarrativeRuleSynthesizer()
        source = RequirementSource(
            text="Лист A-101: толщина WALL-01 не менее 200 мм",
            source_kind=SourceKind.TECHNICAL_SPECIFICATION,
        )
        result = synthesizer.synthesize(source)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_scope, RuleScope.DRAWING_ANNOTATION)
        self.assertEqual(result[0].target_ref, "WALL-01")
        self.assertEqual(result[0].operator, ComparisonOperator.GREATER_OR_EQUAL)
        self.assertEqual(result[0].expected_value, "200")
        self.assertEqual(result[0].unit, "мм")

    def test_drawing_dimension_english(self) -> None:
        from samolet.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
        from samolet.domain.models import RequirementSource, RuleScope, SourceKind

        synthesizer = NarrativeRuleSynthesizer()
        source = RequirementSource(
            text="Sheet B-202: dimension BEAM-03 at least 300 mm",
            source_kind=SourceKind.TECHNICAL_SPECIFICATION,
        )
        result = synthesizer.synthesize(source)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_scope, RuleScope.DRAWING_ANNOTATION)
        self.assertEqual(result[0].expected_value, "300")


# ---------------------------------------------------------------------------
# F: ToleranceConfig domain value object
# ---------------------------------------------------------------------------

class ToleranceConfigTests(unittest.TestCase):
    def test_default_values(self) -> None:
        from samolet.domain.models import ToleranceConfig
        tc = ToleranceConfig()
        self.assertEqual(tc.length_epsilon, 0.001)
        self.assertEqual(tc.area_epsilon, 0.01)
        self.assertEqual(tc.default_epsilon, 1e-6)

    def test_epsilon_for_length_units(self) -> None:
        from samolet.domain.models import ToleranceConfig
        tc = ToleranceConfig()
        for unit in ("mm", "мм", "m", "м", "cm", "см"):
            self.assertEqual(tc.epsilon_for_unit(unit), 0.001, f"Failed for unit={unit}")

    def test_epsilon_for_area_units(self) -> None:
        from samolet.domain.models import ToleranceConfig
        tc = ToleranceConfig()
        for unit in ("m2", "м2", "sqm", "sq.m", "m²", "м²"):
            self.assertEqual(tc.epsilon_for_unit(unit), 0.01, f"Failed for unit={unit}")

    def test_epsilon_for_unknown_unit(self) -> None:
        from samolet.domain.models import ToleranceConfig
        tc = ToleranceConfig()
        self.assertEqual(tc.epsilon_for_unit("kg"), 1e-6)
        self.assertEqual(tc.epsilon_for_unit(None), 1e-6)

    def test_custom_epsilon(self) -> None:
        from samolet.domain.models import ToleranceConfig
        tc = ToleranceConfig(length_epsilon=0.5, area_epsilon=1.0, default_epsilon=0.01)
        self.assertEqual(tc.epsilon_for_unit("mm"), 0.5)
        self.assertEqual(tc.epsilon_for_unit("m2"), 1.0)
        self.assertEqual(tc.epsilon_for_unit(None), 0.01)


# ---------------------------------------------------------------------------
# G: VLM DrawingAnalyzer port + adapter contract
# ---------------------------------------------------------------------------

class VlmDrawingAnalyzerContractTests(unittest.TestCase):
    def test_stub_returns_empty_for_existing_file(self) -> None:
        import tempfile
        from samolet.infrastructure.adapters.vlm_drawing_analyzer import VlmDrawingAnalyzer

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"\x89PNG\r\n\x1a\n")  # minimal PNG header
            tmp_path = Path(tmp.name)

        try:
            analyzer = VlmDrawingAnalyzer()
            result = analyzer.analyze_image(tmp_path, sheet_id="A-101")
            self.assertEqual(result, [])
        finally:
            tmp_path.unlink()

    def test_stub_raises_for_missing_file(self) -> None:
        from samolet.infrastructure.adapters.vlm_drawing_analyzer import VlmDrawingAnalyzer

        analyzer = VlmDrawingAnalyzer()
        with self.assertRaises(FileNotFoundError):
            analyzer.analyze_image(Path("/nonexistent/drawing.pdf"))

    def test_port_protocol_compliance(self) -> None:
        """VlmDrawingAnalyzer satisfies VisionDrawingAnalyzer protocol."""
        from samolet.infrastructure.adapters.vlm_drawing_analyzer import VlmDrawingAnalyzer
        from samolet.domain.ports import VisionDrawingAnalyzer

        analyzer = VlmDrawingAnalyzer()
        # Protocol structural check: must have analyze_image method
        self.assertTrue(hasattr(analyzer, "analyze_image"))
        self.assertTrue(callable(analyzer.analyze_image))
        # isinstance works with runtime_checkable protocols in Python 3.12+
        # For older versions, structural check above suffices

    def test_token_registered_in_bootstrap(self) -> None:
        from samolet.core.di.tokens import Tokens
        self.assertTrue(hasattr(Tokens, "VISION_DRAWING_ANALYZER"))


if __name__ == "__main__":
    unittest.main()
