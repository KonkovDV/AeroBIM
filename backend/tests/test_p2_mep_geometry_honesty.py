"""P2-02 geometry honesty deepen — edge provenance + claim guardrails."""

from __future__ import annotations

import inspect
import unittest
from pathlib import Path

from aerobim.application.services.mep_scope_probe import MepScopeProbe
from aerobim.domain.mep import (
    MepClashMatrix,
    MepClearanceClass,
    MepClearanceRule,
    MepSystemGraph,
    MepSystemNode,
    edge_kind_for_pair,
    evaluate_matrix_against_graph,
    evaluate_system_pair,
    mep_finding_to_issue,
)

REPO = Path(__file__).resolve().parents[2]
MEP_IFC = REPO / "samples" / "mep" / "hvac-sprinkler-systems.ifc"
VERIFIED_SCOPE = REPO / "samples" / "mep" / "federated-scope-verified-fixture.json"
MATRIX = REPO / "samples" / "mep" / "clearance-matrix-template.json"


def _sample_matrix(*, with_exception: bool = False) -> MepClashMatrix:
    exceptions = ("sleeve",) if with_exception else ()
    return MepClashMatrix(
        scope_memo_ref="SYNTHETIC-SCOPE",
        synthetic=True,
        claim_boundary="unit-test only",
        rules=(
            MepClearanceRule(
                system_a="HVAC-SUPPLY",
                system_b="SPRINKLER",
                allowed_intersection=False,
                clearance_class=MepClearanceClass.HARD,
                min_clearance_m=0.05,
                priority=10,
                exception_kinds=exceptions,
            ),
        ),
    )


class GeometryHonestyDeepenTests(unittest.TestCase):
    def test_edge_kind_prefers_connects_over_co_presence(self) -> None:
        graph = MepSystemGraph(
            nodes=(
                MepSystemNode("HVAC-SUPPLY", "HVAC", ("a",), "OV"),
                MepSystemNode("SPRINKLER", "FIRE", ("b",), "PT"),
            ),
            edges=(("HVAC-SUPPLY", "SPRINKLER"),),
            edge_kinds=(("HVAC-SUPPLY", "SPRINKLER", "connects"),),
        )
        self.assertEqual(edge_kind_for_pair(graph, "SPRINKLER", "HVAC-SUPPLY"), "connects")

    def test_issue_stamps_edge_basis_and_geometry_not_verified(self) -> None:
        finding = evaluate_system_pair(
            system_a=MepSystemNode("HVAC-SUPPLY", "HVAC", ("a",), "OV"),
            system_b=MepSystemNode("SPRINKLER", "FIRE", ("b",), "PT"),
            matrix=_sample_matrix(),
            intersecting=True,
            edge_basis="co_presence",
        )
        assert finding is not None
        self.assertEqual(finding.verdict, "forbidden")
        self.assertEqual(finding.edge_basis, "co_presence")
        issue = mep_finding_to_issue(
            finding,
            matrix_synthetic=True,
            geometry_verified=False,
        )
        self.assertEqual(issue.rule_id, "AEROBIM-MEP-TEMPLATE")
        self.assertIn("edge_basis:co_presence", issue.evidence_refs)
        self.assertIn("claim_boundary:geometry_NOT_VERIFIED", issue.evidence_refs)
        self.assertNotEqual(issue.rule_id, "AEROBIM-MEP-FORBIDDEN")

    def test_exception_kinds_stamped_not_validated(self) -> None:
        finding = evaluate_system_pair(
            system_a=MepSystemNode("HVAC-SUPPLY", "HVAC", ("a",), "OV"),
            system_b=MepSystemNode("SPRINKLER", "FIRE", ("b",), "PT"),
            matrix=_sample_matrix(with_exception=True),
            intersecting=True,
            edge_basis="co_presence",
        )
        assert finding is not None
        self.assertEqual(finding.verdict, "forbidden")
        self.assertIn("sleeve", finding.exception_kinds)
        self.assertIn("NOT geometry-validated", finding.message)
        issue = mep_finding_to_issue(finding, matrix_synthetic=True, geometry_verified=False)
        self.assertIn("exception_kinds:sleeve", issue.evidence_refs)
        self.assertIn("claim_boundary:exceptions_NOT_VERIFIED", issue.evidence_refs)

    def test_analyze_probe_hardcodes_geometry_verified_false(self) -> None:
        source = inspect.getsource(MepScopeProbe.evaluate_clearance_matrix)
        self.assertIn("geometry_verified=False", source)
        self.assertNotIn("geometry_verified=True", source)

    def test_federated_graph_exposes_edge_kinds_co_presence(self) -> None:
        if not MEP_IFC.exists() or not VERIFIED_SCOPE.exists():
            self.skipTest("MEP fixture missing")
        try:
            import ifcopenshell  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("ifcopenshell not installed")

        from aerobim.domain.mep import load_federated_mep_scope, load_mep_clearance_matrix
        from aerobim.infrastructure.adapters.federated_ifc_mep_system_graph import (
            FederatedIfcMepSystemGraphProvider,
        )

        scope = load_federated_mep_scope(VERIFIED_SCOPE)
        graph = FederatedIfcMepSystemGraphProvider(scope, repo_root=REPO).build(MEP_IFC)
        self.assertTrue(graph.edge_kinds)
        self.assertTrue(all(kind in {"co_presence", "connects"} for *_p, kind in graph.edge_kinds))
        self.assertTrue(any(kind == "co_presence" for *_p, kind in graph.edge_kinds))

        if MATRIX.exists():
            matrix = load_mep_clearance_matrix(MATRIX)
            findings = evaluate_matrix_against_graph(graph, matrix)
            self.assertTrue(findings)
            for finding in findings:
                self.assertIn(finding.edge_basis, {"co_presence", "connects", "unknown"})
                issue = mep_finding_to_issue(
                    finding,
                    matrix_synthetic=True,
                    geometry_verified=False,
                )
                self.assertNotEqual(issue.rule_id, "AEROBIM-MEP-FORBIDDEN")
                self.assertTrue(any(ref.startswith("edge_basis:") for ref in issue.evidence_refs))


if __name__ == "__main__":
    unittest.main()
