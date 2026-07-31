"""Advisory ON/OFF must not mutate deterministic verdict fields."""

from __future__ import annotations

import copy
import unittest

from aerobim.domain.llm_advisory import LlmDataPolicy, LlmRequest, MockLlmProvider


class LlmAdvisoryInvarianceTests(unittest.TestCase):
    def test_advisory_invariance(self) -> None:
        deterministic = {
            "summary": {"passed": False, "outcome": "review_required"},
            "findings": [{"rule_id": "AEROBIM-CROSS-DOC", "severity": "warning"}],
        }
        before = copy.deepcopy(deterministic)
        provider = MockLlmProvider(provider="kimi", model="kimi-mock")
        request = LlmRequest(
            request_id="inv-1",
            deterministic_findings=tuple(deterministic["findings"]),
            evidence_refs=("f:1",),
            data_policy=LlmDataPolicy(allow_synthetic_public=True),
        )
        response = provider.generate(request)
        self.assertEqual(response.status, "advisory")
        # Mock cannot and must not rewrite the deterministic summary.
        self.assertEqual(deterministic, before)
        self.assertFalse(getattr(response, "affects_summary_passed", False))

    def test_provider_contract(self) -> None:
        for name in ("kimi", "qwen", "gemma"):
            provider = MockLlmProvider(provider=name, model=f"{name}-mock")
            response = provider.generate(
                LlmRequest(request_id=f"c-{name}", evidence_refs=("e:1",))
            )
            self.assertEqual(response.provider, name)
            self.assertTrue(response.schema_valid)
            self.assertEqual(response.status, "advisory")

    def test_external_egress_policy(self) -> None:
        provider = MockLlmProvider(provider="qwen", model="qwen-mock")
        response = provider.generate(
            LlmRequest(
                request_id="deny",
                data_policy=LlmDataPolicy(
                    allow_customer_data=False,
                    allow_synthetic_public=False,
                ),
            )
        )
        self.assertEqual(response.status, "blocked_by_policy")


if __name__ == "__main__":
    unittest.main()
