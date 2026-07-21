"""Advisory AI tool registry tests."""

from __future__ import annotations

import unittest

from aerobim.domain.ai_tool_registry import (
    DEFAULT_ADVISORY_TOOL_REGISTRY,
    advisory_trace_record,
    lookup_advisory_tool,
)


class AdvisoryToolRegistryTests(unittest.TestCase):
    def test_all_tools_cannot_change_verdict(self) -> None:
        for contract in DEFAULT_ADVISORY_TOOL_REGISTRY:
            self.assertFalse(contract.can_change_verdict)

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
