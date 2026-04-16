from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.application.use_cases.analyze_project_package import (
    build_openrebar_provenance_digest,
)
from aerobim.tools.openrebar_provenance_digest import (
    compute_openrebar_provenance_digest,
)


def _fixture_payload() -> dict[str, object]:
    return {
        "contractId": "OpenRebar.reinforcement.report.v1",
        "schemaVersion": "1.0.0",
        "generatedAtUtc": "2026-04-16T00:00:00Z",
        "metadata": {
            "projectCode": "Residential Tower Alpha",
            "slabId": "SLAB-03",
            "sourceSystem": "OpenRebar",
            "targetSystem": "AeroBIM",
            "countryCode": "RU",
            "designCode": "SP63",
            "normativeProfileId": "ru.sp63.2018",
            "normativeTablesVersion": "v1",
        },
        "normativeProfile": {
            "profileId": "ru.sp63.2018",
            "jurisdiction": "RU",
            "designCode": "SP63",
            "tablesVersion": "v1",
        },
        "analysisProvenance": {
            "geometry": {
                "decompositionAlgorithm": "grid-scan",
                "rectangularShortcutFillRatio": 0.9,
                "minRectangleAreaMm2": 1000.0,
                "samplingResolutionPerAxis": 64,
                "cellCoverageInclusionThreshold": 0.5,
            },
            "optimization": {
                "optimizerId": "column-generation",
                "masterProblemStrategy": "restricted-master-lp-highs",
                "pricingStrategy": "bounded-knapsack-dp",
                "integerizationStrategy": "repair-ffd",
                "demandAggregationPrecisionMm": 0.1,
                "qualityFloor": "production",
                "anyFallbackMasterSolverUsed": False,
            },
        },
        "isolineFileName": "floor-03.dxf",
        "isolineFileFormat": "dxf",
        "summary": {
            "parsedZoneCount": 0,
            "classifiedZoneCount": 0,
            "totalRebarSegments": 0,
            "totalWastePercent": 0.0,
            "totalWasteMm": 0.0,
            "totalMassKg": 0.0,
        },
    }


class OpenRebarProvenanceDigestToolTests(unittest.TestCase):
    def test_compute_openrebar_provenance_digest_returns_expected_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "openrebar.result.json"
            payload = _fixture_payload()
            report_path.write_text(json.dumps(payload), encoding="utf-8")

            result = compute_openrebar_provenance_digest(report_path)

            self.assertEqual(result["contract_id"], "OpenRebar.reinforcement.report.v1")
            self.assertEqual(result["schema_version"], "1.0.0")
            self.assertEqual(result["project_code"], "Residential Tower Alpha")
            self.assertEqual(result["slab_id"], "SLAB-03")
            self.assertEqual(
                result["provenance_digest"],
                build_openrebar_provenance_digest(payload),
            )

    def test_compute_openrebar_provenance_digest_raises_for_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "openrebar.result.json"
            report_path.write_text("{invalid-json", encoding="utf-8")

            with self.assertRaises(ValueError):
                compute_openrebar_provenance_digest(report_path)

    def test_compute_openrebar_provenance_digest_raises_for_non_object_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "openrebar.result.json"
            report_path.write_text("[1,2,3]", encoding="utf-8")

            with self.assertRaises(ValueError):
                compute_openrebar_provenance_digest(report_path)


if __name__ == "__main__":
    unittest.main()