"""AABB broadphase for MEP pairs — domain purity + analyze-path honesty."""

from __future__ import annotations

import inspect
import unittest

from aerobim.application.services.mep_scope_probe import MepScopeProbe
from aerobim.domain.mep import MepSystemGraph, MepSystemNode, evaluate_matrix_against_graph
from aerobim.domain.mep_aabb import (
    AxisAlignedBox3d,
    aabb_overlap,
    applied_aabb_result,
    filter_pairs_by_aabb,
    skipped_aabb_result,
    unavailable_aabb_result,
    union_aabb,
)


class MepAabbDomainTests(unittest.TestCase):
    def test_aabb_overlap_and_separation(self) -> None:
        a = AxisAlignedBox3d(0, 0, 0, 1, 1, 1)
        b = AxisAlignedBox3d(0.5, 0.5, 0.5, 2, 2, 2)
        c = AxisAlignedBox3d(3, 3, 3, 4, 4, 4)
        self.assertTrue(aabb_overlap(a, b))
        self.assertFalse(aabb_overlap(a, c))

    def test_union_and_filter_pairs(self) -> None:
        boxes = {
            "HVAC-SUPPLY": AxisAlignedBox3d(0, 0, 0, 1, 1, 1),
            "SPRINKLER": AxisAlignedBox3d(0.5, 0, 0, 1.5, 1, 1),
            "CABLE-TRAY": AxisAlignedBox3d(10, 10, 10, 11, 11, 11),
        }
        pairs = {
            ("HVAC-SUPPLY", "SPRINKLER"),
            ("HVAC-SUPPLY", "CABLE-TRAY"),
            ("SPRINKLER", "CABLE-TRAY"),
        }
        kept = filter_pairs_by_aabb(pairs, boxes)
        self.assertEqual(kept, frozenset({("HVAC-SUPPLY", "SPRINKLER")}))
        merged = union_aabb([boxes["HVAC-SUPPLY"], boxes["SPRINKLER"]])
        assert merged is not None
        self.assertEqual(merged.xmin, 0)
        self.assertEqual(merged.xmax, 1.5)

    def test_applied_filter_shrinks_matrix_candidates(self) -> None:
        from aerobim.domain.mep import (
            MepClashMatrix,
            MepClearanceClass,
            MepClearanceRule,
        )

        graph = MepSystemGraph(
            nodes=(
                MepSystemNode("HVAC-SUPPLY", "HVAC", ("a",)),
                MepSystemNode("SPRINKLER", "FIRE", ("b",)),
                MepSystemNode("CABLE-TRAY", "EL", ("c",)),
            ),
            edges=(
                ("HVAC-SUPPLY", "SPRINKLER"),
                ("HVAC-SUPPLY", "CABLE-TRAY"),
            ),
        )
        matrix = MepClashMatrix(
            synthetic=True,
            rules=(
                MepClearanceRule(
                    system_a="HVAC-SUPPLY",
                    system_b="SPRINKLER",
                    allowed_intersection=False,
                    clearance_class=MepClearanceClass.HARD,
                ),
                MepClearanceRule(
                    system_a="HVAC-SUPPLY",
                    system_b="CABLE-TRAY",
                    allowed_intersection=False,
                    clearance_class=MepClearanceClass.SOFT,
                ),
            ),
        )
        aabb = applied_aabb_result(
            frozenset({("HVAC-SUPPLY", "SPRINKLER")}),
            boxes_built=2,
            pairs_before=2,
        )
        findings = evaluate_matrix_against_graph(
            graph,
            matrix,
            intersecting_pairs=set(aabb.pairs),
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].system_a, "HVAC-SUPPLY")
        self.assertEqual(findings[0].system_b, "SPRINKLER")

    def test_probe_still_hardcodes_geometry_verified_false(self) -> None:
        source = inspect.getsource(MepScopeProbe.evaluate_clearance_matrix)
        self.assertIn("geometry_verified=False", source)
        self.assertNotIn("geometry_verified=True", source)
        self.assertIn("aabb_filter", source)

    def test_status_tokens(self) -> None:
        self.assertEqual(skipped_aabb_result().evidence_token, "aabb_filter:skipped")
        self.assertEqual(
            unavailable_aabb_result(reason="x").evidence_token,
            "aabb_filter:unavailable",
        )


class IfcAabbFilterFixtureTests(unittest.TestCase):
    def test_fixture_without_geometry_falls_back_unavailable(self) -> None:
        from pathlib import Path

        from aerobim.domain.mep import load_federated_mep_scope
        from aerobim.infrastructure.adapters.federated_ifc_mep_system_graph import (
            FederatedIfcMepSystemGraphProvider,
        )
        from aerobim.infrastructure.adapters.ifc_aabb_mep_pair_filter import IfcAabbMepPairFilter

        repo = Path(__file__).resolve().parents[2]
        scope_path = repo / "samples" / "mep" / "federated-scope-verified-fixture.json"
        mep_ifc = repo / "samples" / "mep" / "hvac-sprinkler-systems.ifc"
        if not scope_path.exists() or not mep_ifc.exists():
            self.skipTest("MEP fixture missing")
        try:
            import ifcopenshell  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("ifcopenshell not installed")

        scope = load_federated_mep_scope(scope_path)
        graph = FederatedIfcMepSystemGraphProvider(scope, repo_root=repo).build(mep_ifc)
        result = IfcAabbMepPairFilter().filter_pairs(graph)
        # Fixture has IfcSystem members without tessellatable geometry.
        self.assertEqual(result.status, "unavailable")
        self.assertIn("AABB", result.reason)


if __name__ == "__main__":
    unittest.main()
