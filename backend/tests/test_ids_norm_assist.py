from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.application.use_cases.compile_requirements_to_ids import (
    CompileRequirementsToIdsUseCase,
)
from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import ParsedRequirement, RequirementSource
from aerobim.infrastructure.adapters.deterministic_requirement_to_ids_compiler import (
    DeterministicRequirementToIdsCompiler,
)
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.filesystem_norm_corpus_retriever import (
    FilesystemNormCorpusRetriever,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container


class IdsNormAssistTests(unittest.TestCase):
    def test_compile_requirements_to_ids_xml(self) -> None:
        compiler = DeterministicRequirementToIdsCompiler()
        draft = compiler.compile_requirements(
            [
                ParsedRequirement(
                    rule_id="FIRE-1",
                    ifc_entity="IFCWALL",
                    property_set="Pset_WallCommon",
                    property_name="FireRating",
                    expected_value="REI60",
                )
            ]
        )
        self.assertTrue(draft.advisory_only)
        self.assertIn("<ids", draft.suggested_ids_xml)
        self.assertIn("FireRating", draft.suggested_ids_xml)
        self.assertIn("REI60", draft.suggested_ids_xml)
        self.assertEqual(draft.source_requirement_count, 1)

    def test_compile_from_source_via_extractor(self) -> None:
        compiler = DeterministicRequirementToIdsCompiler(StructuredRequirementExtractor())
        source = RequirementSource(
            text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n",
        )
        draft = compiler.compile(source)
        self.assertGreaterEqual(draft.source_requirement_count, 1)
        self.assertIn("IFCWALL", draft.suggested_ids_xml)

    def test_norm_corpus_keyword_retrieve(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "sp54.md").write_text(
                "СП 54.13330 требования к огнестойкости стен REI60",
                encoding="utf-8",
            )
            (root / "other.txt").write_text("unrelated plumbing notes", encoding="utf-8")
            retriever = FilesystemNormCorpusRetriever([root])
            hits = retriever.retrieve("огнестойкости REI60", top_k=3)
        self.assertGreaterEqual(len(hits), 1)
        self.assertIn("sp54", hits[0].title)

    def test_compile_use_case_with_enrichment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "fire.txt").write_text("FireRating REI60 wall common", encoding="utf-8")
            use_case = CompileRequirementsToIdsUseCase(
                compiler=DeterministicRequirementToIdsCompiler(StructuredRequirementExtractor()),
                norm_retriever=FilesystemNormCorpusRetriever([root]),
            )
            draft, passages = use_case.execute(
                RequirementSource(text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"),
                enrich_query="FireRating REI60",
            )
        self.assertTrue(draft.advisory_only)
        self.assertGreaterEqual(len(passages), 1)

    def test_bootstrap_registers_i4_tokens(self) -> None:
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
        self.assertTrue(container.is_registered(Tokens.REQUIREMENT_TO_IDS_COMPILER))
        self.assertTrue(container.is_registered(Tokens.NORM_CORPUS_RETRIEVER))
        self.assertTrue(container.is_registered(Tokens.COMPILE_REQUIREMENTS_TO_IDS_USE_CASE))


if __name__ == "__main__":
    unittest.main()
