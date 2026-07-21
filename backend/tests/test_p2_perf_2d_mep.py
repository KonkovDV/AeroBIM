"""P2 iteration — IFC parse cache, 2D coords, annotation↔IFC, federated MEP graph."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.annotation_ifc_matching import (
    link_annotation_to_ifc_target,
    match_annotations_to_regions,
)
from aerobim.domain.drawing_coordinate_system import (
    SheetCoordinateSystem,
    coordinate_system_from_asset,
    coordinate_system_from_region,
)
from aerobim.domain.ifc_spatial_index import IfcSpatialElement, IfcSpatialIndex
from aerobim.domain.mep import FederatedMepScope, UnconfiguredMepSystemGraphProvider
from aerobim.domain.models import (
    ComparisonOperator,
    DrawingAnnotation,
    DrawingAsset,
    DrawingRegionRef,
    ParsedRequirement,
    ProblemZone,
    RuleScope,
)
from aerobim.infrastructure.adapters.federated_ifc_mep_system_graph import (
    FederatedIfcMepSystemGraphProvider,
    _nodes_from_spatial_index,
)
from aerobim.infrastructure.adapters.ifc_file_open import (
    configure_ifc_parse_cache,
    ifc_parse_cache_stats,
    open_ifc_session,
    reset_ifc_parse_cache_for_tests,
)
from aerobim.infrastructure.adapters.scoped_mep_system_graph_provider import (
    ScopedMepSystemGraphProvider,
)

REPO = Path(__file__).resolve().parents[2]
WALL_IFC = REPO / "samples" / "ifc" / "wall-pset-qto-pass.ifc"
WALL_GUID = "3ZAR7ASd14MuxcHc7_fqIb"
MEP_IFC = REPO / "samples" / "mep" / "hvac-sprinkler-systems.ifc"
MATRIX_TEMPLATE = REPO / "samples" / "mep" / "clearance-matrix-template.json"
VERIFIED_SCOPE = REPO / "samples" / "mep" / "federated-scope-verified-fixture.json"


class IfcParseSessionTests(unittest.TestCase):
    def tearDown(self) -> None:
        reset_ifc_parse_cache_for_tests()

    def test_open_session_builds_spatial_index_and_cache_hit(self) -> None:
        if not WALL_IFC.exists():
            self.skipTest("fixture IFC missing")
        try:
            import ifcopenshell  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("ifcopenshell not installed")

        first = open_ifc_session(WALL_IFC)
        second = open_ifc_session(WALL_IFC)
        self.assertFalse(first.cache_hit)
        self.assertTrue(second.cache_hit)
        self.assertIsInstance(first.spatial_index, IfcSpatialIndex)
        hit = first.spatial_index.lookup(WALL_GUID)
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit.ifc_type, "IfcWall")

        stats = ifc_parse_cache_stats()
        self.assertGreaterEqual(stats["opens"], 2)
        self.assertGreaterEqual(stats["hits"], 1)

    def test_cache_dir_writes_marker(self) -> None:
        if not WALL_IFC.exists():
            self.skipTest("fixture IFC missing")
        try:
            import ifcopenshell  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("ifcopenshell not installed")

        with tempfile.TemporaryDirectory() as tmp:
            configure_ifc_parse_cache(tmp)
            open_ifc_session(WALL_IFC)
            markers = list(Path(tmp).glob("*.json"))
            self.assertEqual(len(markers), 1)
            payload = json.loads(markers[0].read_text(encoding="utf-8"))
            self.assertIn("claim_boundary", payload)


class DrawingCoordinateSystemTests(unittest.TestCase):
    def test_normalize_bbox_to_unit_square(self) -> None:
        cs = SheetCoordinateSystem(sheet_id="AR-01", width=1000.0, height=500.0)
        norm = cs.normalize_bbox((100.0, 50.0, 300.0, 250.0))
        self.assertAlmostEqual(norm[0], 0.1)
        self.assertAlmostEqual(norm[1], 0.1)
        self.assertAlmostEqual(norm[2], 0.3)
        self.assertAlmostEqual(norm[3], 0.5)

    def test_coordinate_system_from_region_fixture_pack(self) -> None:
        region = DrawingRegionRef(
            sheet_id="AR-01",
            bbox_xyxy=(0.1, 0.2, 0.3, 0.4),
            confidence=0.9,
            modality="detector",
            coordinate_system="page-pixel",
            page_width=2480.0,
            page_height=3508.0,
        )
        cs = coordinate_system_from_region(region)
        assert cs is not None
        self.assertEqual(cs.sheet_id, "AR-01")
        self.assertEqual(cs.units, "page-pixel")

    def test_coordinate_system_from_asset(self) -> None:
        asset = DrawingAsset(
            asset_id="a1",
            sheet_id="AR-02",
            coordinate_width=320.0,
            coordinate_height=240.0,
        )
        cs = coordinate_system_from_asset(asset)
        assert cs is not None
        self.assertEqual(cs.width, 320.0)


class AnnotationIfcMatchingTests(unittest.TestCase):
    def test_problem_zone_guid_link(self) -> None:
        ann = DrawingAnnotation(
            annotation_id="ann-1",
            sheet_id="AR-01",
            target_ref="Wall PQ",
            measure_name="FireRating",
            observed_value="REI60",
            problem_zone=ProblemZone(
                sheet_id="AR-01",
                x=10.0,
                y=20.0,
                width=100.0,
                height=50.0,
                element_guid=WALL_GUID,
            ),
        )
        link = link_annotation_to_ifc_target(ann)
        self.assertIsNone(link.ifc_guid)
        self.assertIn("claimed_guid:", link.evidence_ref)
        self.assertLessEqual(link.confidence, 0.4)

    def test_region_overlap_fixture_pack(self) -> None:
        ann = DrawingAnnotation(
            annotation_id="ann-2",
            sheet_id="AR-01",
            target_ref="Wall PQ",
            measure_name="Width",
            observed_value="300",
            problem_zone=ProblemZone(x=100.0, y=100.0, width=80.0, height=80.0),
        )
        region = DrawingRegionRef(
            sheet_id="AR-01",
            bbox_xyxy=(110.0, 110.0, 200.0, 200.0),
            confidence=0.85,
            modality="detector",
            page_width=1000.0,
            page_height=1000.0,
        )
        links = match_annotations_to_regions((ann,), (region,))
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].match_basis, "region_overlap")
        self.assertGreater(links[0].confidence, 0.25)

    def test_requirement_confirms_sheet_measure(self) -> None:
        ann = DrawingAnnotation(
            annotation_id="ann-3",
            sheet_id="AR-01",
            target_ref=WALL_GUID,
            measure_name="FireRating",
            observed_value="REI60",
        )
        req = ParsedRequirement(
            rule_id="R1",
            ifc_entity="IfcWall",
            target_ref=WALL_GUID,
            property_name="FireRating",
            rule_scope=RuleScope.IFC_PROPERTY,
            operator=ComparisonOperator.EQUALS,
            expected_value="REI60",
            instructions="sheet=AR-01",
            confidence=0.9,
        )
        link = link_annotation_to_ifc_target(ann, requirements=(req,))
        self.assertEqual(link.match_basis, "sheet+measure")
        self.assertIsNone(link.ifc_guid)


class FederatedMepGraphTests(unittest.TestCase):
    def tearDown(self) -> None:
        reset_ifc_parse_cache_for_tests()

    def test_nodes_from_spatial_index_synthetic(self) -> None:
        index = IfcSpatialIndex(
            elements={
                "g1": IfcSpatialElement("g1", "IfcDuctSegment", "D1", ("HVAC-1",)),
                "g2": IfcSpatialElement("g2", "IfcPipeSegment", "P1", ("SPR-1",)),
            },
            systems={"HVAC-1": ("g1",), "SPR-1": ("g2",)},
        )
        nodes, edges = _nodes_from_spatial_index(index, source_ifc="hvac.ifc")
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(edges), 1)

    def test_eng_fixture_scope_builds_from_mep_systems_fixture(self) -> None:
        if not MEP_IFC.exists():
            self.skipTest("MEP systems fixture missing")
        try:
            import ifcopenshell  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("ifcopenshell not installed")

        rel_path = MEP_IFC.relative_to(REPO).as_posix()
        scope = FederatedMepScope(
            schema_version="1.0.0",
            status="ENG_FIXTURE",
            federated_ifc_paths=(rel_path,),
            scope_memo_ref="eng-fixture",
            clearance_matrix_ref=MATRIX_TEMPLATE.relative_to(REPO).as_posix(),
            claim_boundary="Engineering fixture only",
        )
        provider = FederatedIfcMepSystemGraphProvider(scope, repo_root=REPO)
        graph = provider.build(MEP_IFC)
        self.assertTrue(graph.synthetic)
        system_ids = {node.system_id for node in graph.nodes}
        self.assertIn("HVAC-SUPPLY", system_ids)
        self.assertIn("SPRINKLER", system_ids)

    def test_path_jail_rejects_absolute_and_escape(self) -> None:
        from aerobim.core.security.path_jail import PathJailError

        scope = FederatedMepScope(
            schema_version="1.0.0",
            status="ENG_FIXTURE",
            federated_ifc_paths=("C:/Windows/win.ini",),
            scope_memo_ref="eng",
            clearance_matrix_ref=None,
            claim_boundary="fixture",
        )
        provider = FederatedIfcMepSystemGraphProvider(scope, repo_root=REPO)
        with self.assertRaises(PathJailError):
            provider.build(MEP_IFC)

        escape = FederatedMepScope(
            schema_version="1.0.0",
            status="ENG_FIXTURE",
            federated_ifc_paths=("../outside.ifc",),
            scope_memo_ref="eng",
            clearance_matrix_ref=None,
            claim_boundary="fixture",
        )
        provider2 = FederatedIfcMepSystemGraphProvider(escape, repo_root=REPO)
        with self.assertRaises(PathJailError):
            provider2.build(MEP_IFC)

    def test_wall_fixture_without_systems_fails_closed(self) -> None:
        if not WALL_IFC.exists():
            self.skipTest("fixture IFC missing")
        try:
            import ifcopenshell  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("ifcopenshell not installed")

        rel_path = WALL_IFC.relative_to(REPO).as_posix()
        scope = FederatedMepScope(
            schema_version="1.0.0",
            status="VERIFIED",
            federated_ifc_paths=(rel_path,),
            scope_memo_ref="test-memo",
            clearance_matrix_ref=None,
            claim_boundary="test only",
            expert_signed_by="tester",
            expert_signed_at="2026-07-21T00:00:00Z",
        )
        provider = FederatedIfcMepSystemGraphProvider(scope, repo_root=REPO)
        with self.assertRaises(RuntimeError):
            provider.build(WALL_IFC)

    def test_clearance_matrix_loader_and_eval(self) -> None:
        from aerobim.domain.mep import (
            evaluate_matrix_against_graph,
            load_mep_clearance_matrix,
            mep_finding_to_issue,
        )

        if not MATRIX_TEMPLATE.exists():
            self.skipTest("matrix template missing")
        matrix = load_mep_clearance_matrix(MATRIX_TEMPLATE)
        self.assertGreaterEqual(len(matrix.rules), 1)
        self.assertAlmostEqual(matrix.rules[0].min_clearance_m or 0.0, 0.05)

        if not MEP_IFC.exists():
            self.skipTest("MEP fixture missing")
        try:
            import ifcopenshell  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("ifcopenshell not installed")

        scope = FederatedMepScope(
            schema_version="1.0.0",
            status="ENG_FIXTURE",
            federated_ifc_paths=(MEP_IFC.relative_to(REPO).as_posix(),),
            scope_memo_ref="eng",
            clearance_matrix_ref=None,
            claim_boundary="fixture",
        )
        graph = FederatedIfcMepSystemGraphProvider(scope, repo_root=REPO).build(MEP_IFC)
        findings = evaluate_matrix_against_graph(graph, matrix)
        self.assertTrue(any(f.verdict == "forbidden" for f in findings))
        issue = mep_finding_to_issue(
            findings[0],
            matrix_synthetic=True,
            geometry_verified=False,
        )
        self.assertEqual(issue.severity.value, "warning")
        self.assertEqual(issue.rule_id, "AEROBIM-MEP-TEMPLATE")
        self.assertNotEqual(issue.rule_id, "AEROBIM-MEP-FORBIDDEN")

    def test_scoped_provider_falls_back_when_not_verified(self) -> None:
        template = REPO / "samples" / "mep" / "federated-scope-template.json"
        if not template.exists():
            self.skipTest("template missing")
        scoped = ScopedMepSystemGraphProvider(
            scope_path=template,
            repo_root=REPO,
            fallback=UnconfiguredMepSystemGraphProvider(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            ifc = Path(tmp) / "x.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                scoped.build(ifc)

    def test_verified_fixture_scope_json_loads(self) -> None:
        from aerobim.domain.mep import load_federated_mep_scope

        if not VERIFIED_SCOPE.exists():
            self.skipTest("verified fixture scope missing")
        scope = load_federated_mep_scope(VERIFIED_SCOPE)
        self.assertFalse(scope.verified)
        self.assertTrue(scope.eng_fixture)
        self.assertTrue(scope.allows_federated_graph)
        self.assertTrue(scope.clearance_matrix_ref)


if __name__ == "__main__":
    unittest.main()
