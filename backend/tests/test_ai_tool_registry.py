"""Advisory AI tool registry tests."""

from __future__ import annotations

import unittest

from aerobim.domain.ai_tool_registry import (
    DEFAULT_ADVISORY_TOOL_REGISTRY,
    advisory_trace_record,
    allowed_agent_tool_names,
    lookup_advisory_tool,
)


class AdvisoryToolRegistryTests(unittest.TestCase):
    def test_all_tools_cannot_change_verdict(self) -> None:
        for contract in DEFAULT_ADVISORY_TOOL_REGISTRY:
            self.assertFalse(contract.can_change_verdict)

    def test_agent_allowlist_derived_from_registry(self) -> None:
        names = allowed_agent_tool_names()
        self.assertIn("detect_system_clash", names)
        self.assertIn("retrieve_norms", names)
        self.assertEqual(len(names), 8)

    def test_validate_invocation_rejects_tenant_outside_allowlist(self) -> None:
        from aerobim.domain.ai_tool_registry import AdvisoryToolContract

        contract = AdvisoryToolContract(
            name="ifc_kg_query",
            allowlist=frozenset({"tenant-a"}),
            json_schema_id="aerobim.ifc_kg_query.v1",
            timeout_seconds=10.0,
            max_steps=5,
            evidence_required=True,
        )
        with self.assertRaises(ValueError):
            contract.validate_invocation(tool_name="ifc_kg_query", tenant_id="tenant-b")
        contract.validate_invocation(tool_name="ifc_kg_query", tenant_id="tenant-a")

    def test_lookup_known_tool(self) -> None:
        contract = lookup_advisory_tool("ifc_kg_query")
        self.assertIsNotNone(contract)
        assert contract is not None
        self.assertEqual(contract.max_steps, 5)

    def test_trace_record_requires_evidence(self) -> None:
        with self.assertRaises(ValueError):
            advisory_trace_record(
                tool_name="ifc_kg_query",
                request_id="req-1",
                steps=1,
                evidence_refs=(),
                payload={},
            )

    def test_trace_record_within_max_steps(self) -> None:
        row = advisory_trace_record(
            tool_name="ifc_kg_query",
            request_id="req-1",
            steps=2,
            evidence_refs=("ev-1",),
            payload={"query": "duct"},
        )
        self.assertFalse(row["can_change_verdict"])
        self.assertEqual(row["tool_name"], "ifc_kg_query")


if __name__ == "__main__":
    unittest.main()
