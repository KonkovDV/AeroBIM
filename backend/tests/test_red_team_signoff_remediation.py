"""Red Team remediations RT-A/B/C/D/E/F — sign-off reliability & honesty."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.services.analyze_orchestrators import (
    AdvisoryOrchestrator,
    DeterministicValidationOrchestrator,
    EvidenceAssembler,
    IngestionOrchestrator,
)
from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.cad_ingest import CadIngestResult
from aerobim.domain.models import (
    CapabilityState,
    DrawingSource,
    RequirementSource,
    Severity,
    SourceKind,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator
from aerobim.infrastructure.di.bootstrap import bootstrap_container


def _minimal_uc(**kwargs: object) -> AnalyzeProjectPackageUseCase:
    base = {
        "requirement_extractor": StructuredRequirementExtractor(),
        "narrative_rule_synthesizer": NarrativeRuleSynthesizer(),
        "drawing_analyzer": StructuredDrawingAnalyzer(),
        "ifc_validator": MagicMock(validate=MagicMock(return_value=[])),
        "remark_generator": TemplateRemarkGenerator(),
        "audit_report_store": InMemoryAuditStore(),
    }
    base.update(kwargs)
    return AnalyzeProjectPackageUseCase(**base)  # type: ignore[arg-type]


def _engine_signature(report) -> tuple:  # noqa: ANN001
    """Deterministic findings only — exclude advisory agent / HITL INFO noise."""

    engine = []
    for issue in report.issues:
        if issue.source_id == "compliance-agent":
            continue
        if issue.rule_id.startswith("AGENT-") or issue.rule_id.startswith("AEROBIM-AGENT-"):
            continue
        engine.append(
            (
                issue.rule_id,
                issue.severity.value,
                issue.category.value if hasattr(issue.category, "value") else str(issue.category),
                issue.target_ref or "",
                issue.message,
            )
        )
    return tuple(sorted(engine))


class RedTeamSignoffRemediationTests(unittest.TestCase):
    def test_rt_a_use_case_wires_contour_orchestrators(self) -> None:
        uc = _minimal_uc()
        self.assertIsInstance(uc._ingestion, IngestionOrchestrator)
        self.assertIsInstance(uc._deterministic, DeterministicValidationOrchestrator)
        self.assertIsInstance(uc._advisory, AdvisoryOrchestrator)
        self.assertIsInstance(uc._evidence, EvidenceAssembler)

    def test_rt_b_replace_not_dict_reflection(self) -> None:
        orch = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "aerobim"
            / "application"
            / "services"
            / "analyze_orchestrators.py"
        )
        uc = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "aerobim"
            / "application"
            / "use_cases"
            / "analyze_project_package.py"
        )
        orch_text = orch.read_text(encoding="utf-8")
        uc_text = uc.read_text(encoding="utf-8")
        self.assertNotIn("__dict__", orch_text)
        self.assertNotIn("req.__dict__", uc_text)
        self.assertNotIn("issue.__dict__", uc_text)
        self.assertIn("replace(req, confidence=", orch_text)
        self.assertIn("from dataclasses import dataclass, replace", orch_text)
        self.assertIn("priority=compute_issue_priority", orch_text)
        self.assertIn("replace(", orch_text)

    def test_rt_c_quantity_infra_failure_blocks_pass(self) -> None:
        from aerobim.domain.models import (
            ComparisonOperator,
            ParsedRequirement,
            RuleScope,
        )

        class _BoomQty:
            def check(self, ifc_path, claims):  # noqa: ANN001
                raise OSError("disk I/O failed")

        class _Extractor:
            def extract(self, source):  # noqa: ANN001
                return [
                    ParsedRequirement(
                        rule_id="AREA-1",
                        rule_scope=RuleScope.IFC_QUANTITY,
                        ifc_entity="IfcSpace",
                        property_set="Qto_SpaceBaseQuantities",
                        property_name="NetFloorArea",
                        operator=ComparisonOperator.EQUALS,
                        expected_value="12",
                        unit="m2",
                        target_ref="APT-01",
                    )
                ]

        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            uc = _minimal_uc(
                requirement_extractor=_Extractor(),
                quantity_consistency_checker=_BoomQty(),
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="rt-c-qty",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(text="area"),
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.ifc_validation.status, CapabilityState.FAILED)
        self.assertFalse(report.summary.passed)
        self.assertTrue(
            any(
                i.rule_id == "AEROBIM-QTY-ERROR" and i.severity is Severity.ERROR
                for i in report.issues
            )
        )

    def test_rt_c_load_infra_failure_blocks_pass(self) -> None:
        class _BoomLoad:
            def verify(self, request):  # noqa: ANN001
                raise RuntimeError("spreadsheet backend down")

        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            uc = _minimal_uc(load_evidence_verifier=_BoomLoad())
            report = uc.execute(
                ValidationRequest(
                    request_id="rt-c-load",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                    calculation_source=RequirementSource(
                        text="LOAD|L1|snow|10|kN|12\n",
                        source_kind=SourceKind.CALCULATION,
                    ),
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.calculation_match.status, CapabilityState.FAILED)
        self.assertFalse(report.summary.passed)

    def test_rt_c_mep_unexpected_failure_is_failed(self) -> None:
        class _BoomMep:
            def build(self, ifc_path):  # noqa: ANN001
                raise OSError("ifc mmap failed")

        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            uc = _minimal_uc(mep_system_graph_provider=_BoomMep())
            report = uc.execute(
                ValidationRequest(
                    request_id="rt-c-mep",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.mep_system_clash.status, CapabilityState.FAILED)
        self.assertFalse(report.summary.passed)

    def test_rt_d_mixed_dwg_dxf_capability_failed(self) -> None:
        class _Cad:
            def ingest(self, path, *, sheet_id=None):  # noqa: ANN001
                if path.suffix.lower() == ".dwg":
                    return CadIngestResult(
                        annotations=(),
                        format_resolved="dwg",
                        entity_count=0,
                        degraded=True,
                        supported=False,
                        reason="ODA not configured",
                    )
                return CadIngestResult(
                    annotations=(),
                    format_resolved="dxf",
                    entity_count=1,
                    degraded=False,
                    supported=True,
                    reason=None,
                )

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            ifc = root / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            dwg = root / "a.dwg"
            dxf = root / "b.dxf"
            dwg.write_bytes(b"AC1015")
            dxf.write_text("0\nEOF\n", encoding="utf-8")
            uc = _minimal_uc(cad_model_ingestor=_Cad())
            report = uc.execute(
                ValidationRequest(
                    request_id="rt-d",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                    drawing_sources=(
                        DrawingSource(path=dwg, sheet_id="DWG1"),
                        DrawingSource(path=dxf, sheet_id="DXF1"),
                    ),
                )
            )
        assert report.capabilities is not None
        status = report.capabilities.dwg_dxf.status
        self.assertEqual(status, CapabilityState.FAILED)
        self.assertNotEqual(status, CapabilityState.NOT_VERIFIED)
        self.assertNotEqual(status, CapabilityState.OK)

    def test_rt_e_advisory_on_off_same_engine_and_passed(self) -> None:
        from aerobim.tools.benchmark_project_package import load_benchmark_pack

        repo_root = Path(__file__).resolve().parents[2]
        pack_path = repo_root / "samples" / "benchmarks" / "project-package-baseline.json"
        if not pack_path.exists():
            self.skipTest("baseline pack missing")
        pack = load_benchmark_pack(pack_path, repo_root_path=repo_root)

        settings = Settings(
            application_name="test",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path(tempfile.mkdtemp()) / "var",
            debug=True,
        )
        settings.storage_dir.mkdir(parents=True, exist_ok=True)
        container = bootstrap_container(settings)
        uc = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)

        request_on = replace(pack.request, request_id="rt-e-on")
        report_on = uc.execute(request_on)

        # Force advisory OFF by clearing agent on a fresh container resolve path:
        uc_off = replace  # placate linters
        del uc_off
        uc._compliance_agent = None
        uc._advisory_issues = ()
        request_off = replace(pack.request, request_id="rt-e-off")
        report_off = uc.execute(request_off)

        self.assertEqual(report_on.summary.passed, report_off.summary.passed)
        self.assertEqual(_engine_signature(report_on), _engine_signature(report_off))

        # Report-hash over deterministic fields (not report_id / created_at / advisory drafts)
        def _hash(report) -> str:  # noqa: ANN001
            payload = {
                "passed": report.summary.passed,
                "engine": _engine_signature(report),
                "caps": {
                    name: getattr(report.capabilities, name).status.value
                    for name in (
                        "clash",
                        "ids",
                        "ifc_validation",
                        "dwg_dxf",
                        "calculation_match",
                        "mep_system_clash",
                    )
                    if report.capabilities is not None
                },
            }
            return hashlib.sha256(
                json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
            ).hexdigest()

        self.assertEqual(_hash(report_on), _hash(report_off))

    def test_rt_f_non_dev_from_env_without_token_fails(self) -> None:
        import os
        from unittest.mock import patch

        with patch.dict(
            os.environ,
            {
                "AEROBIM_ENV": "production",
                "AEROBIM_API_BEARER_TOKEN": "",
                "AEROBIM_ALLOW_ANONYMOUS_DEV": "false",
                "AEROBIM_OIDC_ISSUER": "",
                "AEROBIM_OIDC_AUDIENCE": "",
                "AEROBIM_OIDC_JWKS_URL": "",
            },
            clear=False,
        ):
            with self.assertRaises(RuntimeError):
                Settings.from_env()


if __name__ == "__main__":
    unittest.main()
