from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import ifcopenshell
import ifcopenshell.api
import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.domain.models import ClashResult, RequirementSource
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.ifc_clash_detector import IfcClashDetector


def _has_optional_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _build_geometric_ifc_fixture(target_path: Path) -> Path:
    model = ifcopenshell.api.run("project.create_file")
    project = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcProject", name="Probe"
    )
    length = ifcopenshell.api.run("unit.add_si_unit", model, unit_type="LENGTHUNIT", prefix="MILLI")
    area = ifcopenshell.api.run("unit.add_si_unit", model, unit_type="AREAUNIT")
    ifcopenshell.api.run("unit.assign_unit", model, units=[length, area])

    model3d = ifcopenshell.api.run("context.add_context", model, context_type="Model")
    body = ifcopenshell.api.run(
        "context.add_context",
        model,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=model3d,
    )

    site = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSite", name="Site")
    building = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcBuilding", name="Building"
    )
    storey = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcBuildingStorey", name="Storey"
    )
    ifcopenshell.api.run("aggregate.assign_object", model, products=[site], relating_object=project)
    ifcopenshell.api.run(
        "aggregate.assign_object", model, products=[building], relating_object=site
    )
    ifcopenshell.api.run(
        "aggregate.assign_object", model, products=[storey], relating_object=building
    )

    wall1 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Wall-1")
    wall2 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Wall-2")
    ifcopenshell.api.run(
        "spatial.assign_container", model, products=[wall1, wall2], relating_structure=storey
    )

    rep1 = ifcopenshell.api.run(
        "geometry.create_2pt_wall",
        model,
        element=wall1,
        context=body,
        p1=(0.0, 0.0),
        p2=(4.0, 0.0),
        elevation=0.0,
        height=3.0,
        thickness=0.2,
    )
    ifcopenshell.api.run(
        "geometry.assign_representation", model, product=wall1, representation=rep1
    )

    rep2 = ifcopenshell.api.run(
        "geometry.create_2pt_wall",
        model,
        element=wall2,
        context=body,
        p1=(2.0, -1.0),
        p2=(2.0, 1.0),
        elevation=0.0,
        height=3.0,
        thickness=0.2,
    )
    ifcopenshell.api.run(
        "geometry.assign_representation", model, product=wall2, representation=rep2
    )

    model.write(str(target_path))
    return target_path


class OptionalAdapterIntegrationTests(unittest.TestCase):
    def test_ifcclash_detector_executes_real_engine_when_extra_installed(self) -> None:
        if not _has_optional_module("ifcclash"):
            self.skipTest("ifcclash extra not installed in the active backend environment")

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = _build_geometric_ifc_fixture(Path(tmpdir) / "geometric-clash.ifc")
            results = IfcClashDetector().detect(fixture)

            self.assertGreaterEqual(len(results), 1)
            for result in results:
                self.assertIsInstance(result, ClashResult)
                self.assertEqual(result.clash_type, "hard")
                self.assertIsInstance(result.element_a_guid, str)
                self.assertIsInstance(result.element_b_guid, str)
                self.assertIsInstance(result.distance, float)

    def test_docling_extractor_reads_pdf_requirement_source_when_extra_installed(self) -> None:
        if not _has_optional_module("docling"):
            self.skipTest("docling extra not installed in the active backend environment")

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "requirements.pdf"
            document = pymupdf.open()
            page = document.new_page(width=400, height=180)
            page.insert_text(
                (24, 40),
                "REQ-DOCLING-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
            )
            document.save(pdf_path)
            document.close()

            requirements = StructuredRequirementExtractor().extract(
                RequirementSource(text="", path=pdf_path)
            )

            self.assertEqual(len(requirements), 1)
            self.assertEqual(requirements[0].rule_id, "REQ-DOCLING-001")
            self.assertEqual(requirements[0].ifc_entity, "IFCWALL")
            self.assertEqual(requirements[0].property_set, "Pset_WallCommon")
            self.assertEqual(requirements[0].property_name, "FireRating")
            self.assertEqual(requirements[0].expected_value, "REI60")
            self.assertEqual(requirements[0].source, str(pdf_path))


if __name__ == "__main__":
    unittest.main()
