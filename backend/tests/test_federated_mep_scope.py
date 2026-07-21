"""Federated MEP scope manifest loader tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.mep import FederatedMepScope, load_federated_mep_scope


class FederatedMepScopeTests(unittest.TestCase):
    def test_template_scope_is_not_verified(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        template = repo / "samples" / "mep" / "federated-scope-template.json"
        if not template.exists():
            self.skipTest("template missing")
        scope = load_federated_mep_scope(template)
        self.assertIsInstance(scope, FederatedMepScope)
        self.assertEqual(scope.status, "NOT_VERIFIED")
        self.assertFalse(scope.verified)
        self.assertFalse(scope.allows_federated_graph)
        self.assertEqual(scope.federated_ifc_paths, ())

    def test_verified_scope_requires_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scope.json"
            path.write_text(
                json.dumps({"schema_version": "1.0.0", "status": "VERIFIED"}),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_federated_mep_scope(path)

    def test_verified_without_signoff_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scope.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "status": "VERIFIED",
                        "federated_ifc_paths": ["hvac.ifc"],
                        "scope_memo_ref": "memo-001",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_federated_mep_scope(path)

    def test_verified_scope_with_signoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scope.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "status": "VERIFIED",
                        "federated_ifc_paths": ["hvac.ifc", "sprinkler.ifc"],
                        "scope_memo_ref": "memo-001",
                        "expert_signoff": {
                            "signed_by": "expert@example.com",
                            "signed_at": "2026-07-21T00:00:00Z",
                        },
                    }
                ),
                encoding="utf-8",
            )
            scope = load_federated_mep_scope(path)
            self.assertTrue(scope.verified)
            self.assertTrue(scope.allows_federated_graph)
            self.assertEqual(len(scope.federated_ifc_paths), 2)

    def test_eng_fixture_allows_graph_not_verified(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        fixture = repo / "samples" / "mep" / "federated-scope-verified-fixture.json"
        if not fixture.exists():
            self.skipTest("eng fixture missing")
        scope = load_federated_mep_scope(fixture)
        self.assertEqual(scope.status, "ENG_FIXTURE")
        self.assertFalse(scope.verified)
        self.assertTrue(scope.eng_fixture)
        self.assertTrue(scope.allows_federated_graph)


if __name__ == "__main__":
    unittest.main()
