"""Evidence-bounded advisory outputs."""

from __future__ import annotations

import unittest

from aerobim.domain.llm_advisory import (
    LlmDataPolicy,
    LlmEvidenceContract,
    LlmRequest,
    MockLlmProvider,
)


class LlmEvidenceBoundedTests(unittest.TestCase):
    def test_evidence_bounded_output(self) -> None:
        provider = MockLlmProvider(provider="qwen", model="qwen-mock")
        refs = ("finding:9", "calc:2")
        response = provider.generate(
            LlmRequest(
                request_id="eb-1",
                evidence_refs=refs,
                deterministic_findings=({"rule_id": "AEROBIM-QTY"},),
                data_policy=LlmDataPolicy(allow_synthetic_public=True),
            )
        )
        self.assertTrue(set(response.evidence_refs).issubset(set(refs) | {"deterministic"}))
        contract = LlmEvidenceContract()
        self.assertTrue(contract.require_evidence_refs)
        self.assertFalse(contract.allow_verdict_mutation)
        if contract.require_evidence_refs:
            self.assertTrue(response.evidence_refs)

    def test_schema_validation(self) -> None:
        provider = MockLlmProvider(provider="kimi", model="kimi-mock")
        response = provider.generate(LlmRequest(request_id="eb-2", evidence_refs=("e:1",)))
        self.assertTrue(response.schema_valid)
        self.assertEqual(response.status, "advisory")
        self.assertIsNone(response.confidence)

    def test_secret_not_logged(self) -> None:
        from aerobim.domain.llm_advisory import LlmAuditRecord

        record = LlmAuditRecord(
            request_id="sec-1",
            provider="kimi",
            model="kimi-mock",
            latency_ms=1.0,
            status="advisory",
            token_usage={"prompt_tokens": 10},
        )
        blob = str(record)
        self.assertNotIn("sk-", blob)
        self.assertNotIn("API_KEY", blob)


if __name__ == "__main__":
    unittest.main()
