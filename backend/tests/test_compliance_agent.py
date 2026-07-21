from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.application.services.compliance_agent_orchestrator import (
    ComplianceAgentOrchestrator,
)
from aerobim.application.services.determinism_gate import DeterminismGate
from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import (
    RequirementSource,
    Severity,
    SourceKind,
    ValidationIssue,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.deterministic_requirement_to_ids_compiler import (
    DeterministicRequirementToIdsCompiler,
)
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.filesystem_norm_corpus_retriever import (
    FilesystemNormCorpusRetriever,
)
from aerobim.infrastructure.adapters.manifest_logic_consistency_adapter import (
    ManifestLogicConsistencyAdapter,
)
from aerobim.infrastructure.adapters.spreadsheet_load_evidence_adapter import (
    SpreadsheetLoadEvidenceAdapter,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container


class ComplianceAgentTests(unittest.TestCase):
    def _request(self, temporary_directory: str, **kwargs: object) -> ValidationRequest:
        ifc = Path(temporary_directory) / "m.ifc"
        ifc.write_text("ISO-10303-21;", encoding="utf-8")
        base = {
            "request_id": "agent-1",
            "ifc_path": ifc,
            "requirement_source": RequirementSource(
                text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
            ),
        }
        base.update(kwargs)
        return ValidationRequest(**base)  # type: ignore[arg-type]

    def test_plan_executes_allowlisted_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "norms.txt").write_text("FireRating REI60 wall", encoding="utf-8")
            agent = ComplianceAgentOrchestrator(
                norm_retriever=FilesystemNormCorpusRetriever([root]),
                ids_compiler=DeterministicRequirementToIdsCompiler(
                    StructuredRequirementExtractor()
                ),
                load_verifier=SpreadsheetLoadEvidenceAdapter(),
                logic_analyzer=ManifestLogicConsistencyAdapter(),
                max_steps=6,
            )
            request = self._request(
                temporary_directory,
                calculation_source=RequirementSource(
                    text="LOAD|L1|snow|10|kN|12\n",
                    source_kind=SourceKind.CALCULATION,
                ),
                pd_section_path=root / "pd.json",
            )
            result = agent.run(request)

        names = [step.tool_name for step in result.steps]
        self.assertIn("retrieve_norms", names)
        self.assertIn("compile_ids_draft", names)
        self.assertIn("verify_loads", names)
        self.assertIn("analyze_logic", names)
        self.assertTrue(all(step.status in {"ok", "skipped", "error"} for step in result.steps))
        self.assertIsNotNone(result.ids_draft)

    def test_quantity_and_clash_tools_are_allowlisted(self) -> None:
        class _Qty:
            def check(self, ifc_path, declared):  # noqa: ANN001
                del ifc_path, declared
                return []

        class _Clash:
            def detect(self, ifc_path):  # noqa: ANN001
                del ifc_path
                return []

        agent = ComplianceAgentOrchestrator(
            quantity_checker=_Qty(),  # type: ignore[arg-type]
            clash_detector=_Clash(),  # type: ignore[arg-type]
            max_steps=4,
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = agent.run(self._request(temporary_directory))
        names = [step.tool_name for step in result.steps]
        self.assertIn("check_quantities", names)
        self.assertIn("detect_clashes", names)
        qty_steps = [s for s in result.steps if s.tool_name == "check_quantities"]
        self.assertEqual(qty_steps[0].status, "skipped")
        self.assertTrue(
            any(i.rule_id.startswith("AEROBIM-AGENT-QTY") for i in result.advisory_issues)
        )
        self.assertTrue(
            any(i.rule_id.startswith("AEROBIM-AGENT-CLASH") for i in result.advisory_issues)
        )

    def test_max_steps_cap(self) -> None:
        agent = ComplianceAgentOrchestrator(
            norm_retriever=FilesystemNormCorpusRetriever([]),
            ids_compiler=DeterministicRequirementToIdsCompiler(StructuredRequirementExtractor()),
            load_verifier=SpreadsheetLoadEvidenceAdapter(),
            logic_analyzer=ManifestLogicConsistencyAdapter(),
            max_steps=1,
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = agent.run(
                self._request(
                    temporary_directory,
                    calculation_source=RequirementSource(
                        text="LOAD|L1|x|1|kN|1\n",
                        source_kind=SourceKind.CALCULATION,
                    ),
                )
            )
        self.assertTrue(result.capped)
        self.assertEqual(len(result.steps), 1)
        self.assertTrue(any(i.rule_id == "AEROBIM-AGENT-CAP" for i in result.advisory_issues))

    def test_agent_emits_registry_tool_traces_with_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "norms.txt").write_text("FireRating REI60 wall", encoding="utf-8")
            orchestrator = ComplianceAgentOrchestrator(
                norm_retriever=FilesystemNormCorpusRetriever([root]),
                ids_compiler=DeterministicRequirementToIdsCompiler(
                    StructuredRequirementExtractor()
                ),
                max_steps=2,
            )
            ifc = root / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            result = orchestrator.run(
                ValidationRequest(
                    request_id="trace-1",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="height = 3 m",
                        source_kind=SourceKind.STRUCTURED_TEXT,
                    ),
                )
            )
        self.assertGreater(len(result.tool_traces), 0)
        self.assertTrue(
            all(row.get("can_change_verdict") is not True for row in result.tool_traces)
        )

    def test_agent_advisory_never_blocks_via_determinism_gate(self) -> None:
        gate = DeterminismGate()
        engine = [
            ValidationIssue(
                rule_id="ENG-OK",
                severity=Severity.WARNING,
                message="engine finding",
                finding_id="e1",
            )
        ]
        advisory = [
            ValidationIssue(
                rule_id="AGENT-FAKE",
                severity=Severity.ERROR,
                message="hallucinated blocker",
                finding_id="a1",
            )
        ]
        merged, divergences = gate.reconcile(engine_issues=engine, advisory_issues=advisory)
        self.assertTrue(any(i.severity is Severity.INFO for i in merged if i.finding_id == "a1"))
        self.assertFalse(
            any(i.severity is Severity.ERROR and i.rule_id == "AGENT-FAKE" for i in merged)
        )
        self.assertEqual(len(divergences), 1)

    def test_bootstrap_registers_agent(self) -> None:
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
        self.assertTrue(container.is_registered(Tokens.COMPLIANCE_AGENT_ORCHESTRATOR))
        agent = container.resolve(Tokens.COMPLIANCE_AGENT_ORCHESTRATOR)
        self.assertIsInstance(agent, ComplianceAgentOrchestrator)


if __name__ == "__main__":
    unittest.main()
