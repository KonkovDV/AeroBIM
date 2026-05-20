from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.application.services.extraction_benchmark import run_extraction_benchmark
from aerobim.domain.models import RequirementSource, SourceKind
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer


class NarrativeRussianAecTests(unittest.TestCase):
    def test_wall_thermal_fixture_reaches_academic_f1_threshold(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        manifest = repo_root / "samples" / "benchmarks" / "russian-aec-ground-truth.json"
        synthesizer = NarrativeRuleSynthesizer()

        def extract_fn(path: Path):
            return synthesizer.synthesize(
                RequirementSource(path=path, source_kind=SourceKind.TECHNICAL_SPECIFICATION)
            )

        summary = run_extraction_benchmark(manifest, extract_fn)
        self.assertGreaterEqual(summary.macro_f1, 0.70)
        self.assertGreaterEqual(summary.micro_f1, 0.70)

    def test_extracts_fire_rating_rei180_from_russian_text(self) -> None:
        synthesizer = NarrativeRuleSynthesizer()
        fixture = (
            Path(__file__).resolve().parents[2]
            / "samples"
            / "requirements"
            / "russian-fixture-fire-rating.txt"
        )
        requirements = synthesizer.synthesize(
            RequirementSource(path=fixture, source_kind=SourceKind.TECHNICAL_SPECIFICATION)
        )
        ratings = {
            (req.ifc_entity, req.expected_value)
            for req in requirements
            if req.property_name == "FireRating"
        }
        self.assertIn(("IfcWall", "REI180"), ratings)


if __name__ == "__main__":
    unittest.main()
