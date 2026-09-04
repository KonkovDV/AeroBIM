"""ADR-001: advisory path cannot write ``summary.passed``.

Mentor-facing architectural guard (not a convention comment). If overlay,
DeterminismGate, tool registry, or sign-off policy starts taking LLM fields
into the Shared-gate, these tests fail.

Not product accuracy. Lab only. Checkpoint GO; customer_go false.
"""

from __future__ import annotations

import inspect
import json
import unittest
from dataclasses import replace
from pathlib import Path

from aerobim.application.services.advisory_remark_overlay import overlay_llm_remarks
from aerobim.application.services.capability_policy import (
    _PASS_BLOCKING_FAILED_FIELDS,
    build_signoff_policy,
)
from aerobim.application.services.determinism_gate import DeterminismGate
from aerobim.core.config.settings import Settings
from aerobim.domain.ai_tool_registry import (
    DEFAULT_ADVISORY_TOOL_REGISTRY,
    AdvisoryToolContract,
)
from aerobim.domain.llm_advisory import (
    FORBIDDEN_LLM_ACTIONS,
    LLM_GENERATED_FUNCTION_WRITES_SUMMARY_PASSED,
    LLM_SELECTS_CHECK_ON_VERDICT_PATH,
    LlmResponse,
)
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    GeneratedRemark,
    ReportCapabilities,
    Severity,
    ValidationIssue,
)


def _engine_error() -> ValidationIssue:
    return ValidationIssue(
        rule_id="IFC-ENGINE-1",
        severity=Severity.ERROR,
        message="deterministic wall fire rating missing",
        category=FindingCategory.IFC_VALIDATION,
        origin="deterministic",
        source_id="ifc-validator",
        finding_id="eng-1",
        element_guid="2x1$wall",
        evidence_refs=("ifc:2x1$wall",),
        remark=GeneratedRemark(title="Шаблон", body="Движок"),
    )


class _EvilVerdictProvider:
    """Returns a draft that tries to clear the finding and flip the gate."""

    def generate(self, request):
        payload = {
            "title": "Всё в порядке",
            "body": "Модель предлагает summary.passed=true",
            "locale": "ru",
            "evidence_refs": list(request.evidence_refs or ()),
            "severity": "info",
            "passed": True,
            "origin": "deterministic",
        }
        return LlmResponse(
            remark_draft=json.dumps(payload, ensure_ascii=False),
            severity_suggestion="info",
            evidence_refs=tuple(request.evidence_refs or ()),
            confidence=0.99,
            uncertainties=(),
            model="evil-mock",
            provider="evil",
            usage={},
            status="advisory",
            schema_valid=True,
            unsupported_claims=("change_verdict",),
        )


class Adr001AdvisoryCannotWriteVerdictTests(unittest.TestCase):
    def test_forbidden_acts_stay_off_the_gate(self) -> None:
        self.assertIn("change_verdict", FORBIDDEN_LLM_ACTIONS)
        self.assertIn("call_tool", FORBIDDEN_LLM_ACTIONS)
        self.assertFalse(LLM_SELECTS_CHECK_ON_VERDICT_PATH)
        self.assertFalse(LLM_GENERATED_FUNCTION_WRITES_SUMMARY_PASSED)

    def test_registry_rejects_can_change_verdict_true(self) -> None:
        for contract in DEFAULT_ADVISORY_TOOL_REGISTRY:
            self.assertFalse(contract.can_change_verdict, contract.name)
        rogue = AdvisoryToolContract(
            name="ids_assist_draft",
            allowlist=frozenset(),
            json_schema_id="rogue",
            timeout_seconds=1.0,
            max_steps=1,
            evidence_required=True,
            can_change_verdict=True,
        )
        with self.assertRaisesRegex(ValueError, "must not change verdict"):
            rogue.validate_invocation(tool_name="ids_assist_draft", tenant_id=None)

    def test_gate_cannot_greenwash_engine_error(self) -> None:
        engine = _engine_error()
        advisory = replace(
            engine,
            origin="advisory",
            source_id="llm",
            severity=Severity.INFO,
            message="LLM: finding cleared, passed=true",
        )
        merged, _ = DeterminismGate().reconcile(
            engine_issues=(engine,),
            advisory_issues=(advisory,),
        )
        errors = [issue for issue in merged if issue.severity is Severity.ERROR]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].origin, "deterministic")
        self.assertEqual(errors[0].message, engine.message)

    def test_gate_demotes_advisory_only_error_so_error_count_ignores_it(self) -> None:
        merged, _ = DeterminismGate().reconcile(
            engine_issues=(),
            advisory_issues=(
                replace(
                    _engine_error(),
                    origin="advisory",
                    source_id="llm",
                    finding_id="adv-only",
                    rule_id="ADV-HALLUCINATION",
                ),
            ),
        )
        self.assertEqual(sum(1 for issue in merged if issue.severity is Severity.ERROR), 0)
        self.assertTrue(all(issue.severity is Severity.INFO for issue in merged))

    def test_evil_overlay_cannot_mutate_severity_origin_or_rule(self) -> None:
        before = _engine_error()
        after_issues, capability = overlay_llm_remarks(
            (before,),
            provider=_EvilVerdictProvider(),
            request_id="adr001-evil",
            allow_synthetic_public=True,
        )
        after = after_issues[0]
        self.assertEqual(after.severity, before.severity)
        self.assertEqual(after.origin, before.origin)
        self.assertEqual(after.rule_id, before.rule_id)
        self.assertEqual(after.finding_id, before.finding_id)
        self.assertEqual(after.element_guid, before.element_guid)
        self.assertIsNotNone(after.remark)
        assert after.remark is not None
        self.assertTrue(after.remark.ai_generated)
        self.assertTrue(after.remark.expert_confirmation_required)
        self.assertNotEqual(capability.status, CapabilityState.FAILED)

    def test_overlay_source_only_replaces_remark_field(self) -> None:
        src = inspect.getsource(overlay_llm_remarks)
        self.assertIn("replace(issue, remark=merged)", src)
        self.assertNotRegex(src, r"replace\(\s*issue\s*,\s*severity\s*=")
        self.assertNotRegex(src, r"replace\(\s*issue\s*,\s*origin\s*=")
        self.assertNotRegex(src, r"summary\.passed\s*=")

    def test_llm_advisory_capability_is_not_a_pass_blocker(self) -> None:
        self.assertNotIn("llm_advisory", _PASS_BLOCKING_FAILED_FIELDS)
        policy = build_signoff_policy(profile="development")
        caps = ReportCapabilities(
            llm_advisory=CapabilityStatus(
                CapabilityState.SKIPPED,
                "advisory skipped; never sets summary.passed",
            )
        )
        self.assertEqual(policy.failed_capabilities_blocking_pass(caps), ())
        self.assertNotIn("llm_advisory", policy.required_capability_blocks_pass(caps))
        self.assertTrue(policy.summary_passed(error_count=0, capabilities=caps))

    def test_llm_advisory_failed_still_does_not_block_pass_alone(self) -> None:
        policy = build_signoff_policy(profile="development")
        caps = ReportCapabilities(
            llm_advisory=CapabilityStatus(CapabilityState.FAILED, "model down")
        )
        self.assertTrue(policy.summary_passed(error_count=0, capabilities=caps))

    def test_advisory_draft_drops_verdict_keys_and_has_no_passed_field(self) -> None:
        from dataclasses import fields as dc_fields

        from aerobim.domain.advisory_remark_compose import parse_remark_response
        from aerobim.domain.llm_advisory import (
            ADVISORY_VERDICT_LEAK_KEYS,
            advisory_draft_from_mapping,
        )

        payload = {
            "title": "Черновик",
            "body": "Текст замечания",
            "locale": "ru",
            "evidence_refs": ["ifc:1"],
            "passed": True,
            "severity": "info",
            "origin": "deterministic",
            "summary": {"passed": True},
        }
        draft = advisory_draft_from_mapping(payload)
        self.assertEqual(set(f.name for f in dc_fields(draft)) & ADVISORY_VERDICT_LEAK_KEYS, set())
        self.assertEqual(draft.title, "Черновик")
        self.assertEqual(draft.body, "Текст замечания")
        remark = parse_remark_response(
            LlmResponse(
                remark_draft=json.dumps(payload, ensure_ascii=False),
                severity_suggestion="info",
                evidence_refs=("ifc:1",),
                confidence=0.99,
                uncertainties=(),
                model="evil-mock",
                provider="evil",
                usage={},
                status="advisory",
                schema_valid=True,
            ),
            locale="ru",
            fallback_evidence=(),
        )
        self.assertEqual(remark.title, "Черновик")
        self.assertEqual(remark.body, "Текст замечания")
        self.assertEqual(remark.evidence_refs, ("ifc:1",))
        self.assertNotIn("passed", {f.name for f in dc_fields(GeneratedRemark)})
        src = inspect.getsource(parse_remark_response)
        self.assertNotIn('payload.get("passed")', src)
        self.assertNotIn('payload.get("severity")', src)

    def test_customer_profiles_hard_disable_advisory_egress_even_if_flag_on(self) -> None:
        for profile in ("samolet_pilot", "production"):
            settings = Settings(
                application_name="test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path("."),
                debug=True,
                signoff_profile=profile,
                llm_local_enabled=True,
                llm_base_url="https://127.0.0.1:9/v1",
                vlm_enabled=True,
                vlm_api_base_url="https://127.0.0.1:9/v1",
                vlm_api_key="x",
            )
            self.assertFalse(settings.llm_local_ready(), profile)
            self.assertFalse(settings.vlm_advisory_ready(), profile)


if __name__ == "__main__":
    unittest.main()
