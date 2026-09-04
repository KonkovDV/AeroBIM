"""samolet_pilot / production hard-disable external advisory LLM egress."""

from __future__ import annotations

import os
import unittest
from unittest import mock

from aerobim.core.config.settings import Settings


class PilotProfileBlocksExternalLlmEgressTests(unittest.TestCase):
    def test_pilot_profile_blocks_external_llm_egress(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "AEROBIM_ENV": "development",
                "AEROBIM_SIGNOFF_PROFILE": "samolet_pilot",
                "AEROBIM_LLM_ADVISORY_ENABLED": "true",
                "AEROBIM_LLM_BASE_URL": "https://llm.api.cloud.yandex.net/v1",
                "AEROBIM_LLM_MODEL": "gpt://folder/model",
                "AEROBIM_LLM_MODEL_REVISION": "1",
                "AEROBIM_LLM_BUDGET_LEDGER": "var/llm-budget-test.jsonl",
            },
            clear=False,
        ):
            os.environ.pop("AEROBIM_LLM_LOCAL_ENABLED", None)
            settings = Settings.from_env()
            self.assertTrue(settings.llm_advisory_enabled)
            self.assertFalse(
                settings.llm_local_ready(),
                "samolet_pilot must hard-disable external advisory egress",
            )
            self.assertTrue(settings.customer_pack_llm_egress_denied)
            self.assertEqual(settings.llm_allowed_hosts, ())

    def test_pilot_allow_without_consent_ref_fails_closed(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "AEROBIM_ENV": "development",
                "AEROBIM_SIGNOFF_PROFILE": "samolet_pilot",
                "AEROBIM_CUSTOMER_PACK_LLM_EGRESS": "allow",
            },
            clear=False,
        ):
            os.environ.pop("AEROBIM_CUSTOMER_PACK_LLM_EGRESS_CONSENT_REF", None)
            with self.assertRaisesRegex(RuntimeError, "CONSENT_REF"):
                Settings.from_env()

    def test_pilot_allow_with_consent_ref_keeps_hosts(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "AEROBIM_ENV": "development",
                "AEROBIM_SIGNOFF_PROFILE": "samolet_pilot",
                "AEROBIM_CUSTOMER_PACK_LLM_EGRESS": "allow",
                "AEROBIM_CUSTOMER_PACK_LLM_EGRESS_CONSENT_REF": "letter-oa-2026-09",
            },
            clear=False,
        ):
            settings = Settings.from_env()
            self.assertFalse(settings.customer_pack_llm_egress_denied)
            self.assertIn("llm.api.cloud.yandex.net", settings.llm_allowed_hosts)

    def test_explicit_none_host_token_empties_allowlist(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "AEROBIM_ENV": "development",
                "AEROBIM_SIGNOFF_PROFILE": "development",
                "AEROBIM_LLM_ALLOWED_HOSTS": "none",
                "AEROBIM_CUSTOMER_PACK_LLM_EGRESS": "allow",
            },
            clear=False,
        ):
            os.environ.pop("AEROBIM_LLM_BASE_URL", None)
            os.environ.pop("AEROBIM_VLM_API_BASE_URL", None)
            settings = Settings.from_env()
            self.assertEqual(settings.llm_allowed_hosts, ())

    def test_development_deny_preset_is_not_llm_ready(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "AEROBIM_ENV": "development",
                "AEROBIM_SIGNOFF_PROFILE": "development",
                "AEROBIM_CUSTOMER_PACK_LLM_EGRESS": "deny",
                "AEROBIM_LLM_ADVISORY_ENABLED": "true",
                "AEROBIM_LLM_BASE_URL": "http://127.0.0.1:8000/v1",
                "AEROBIM_LLM_MODEL_REVISION": "1",
                "AEROBIM_LLM_BUDGET_LEDGER": "var/llm-budget-test.jsonl",
            },
            clear=False,
        ):
            settings = Settings.from_env()
            self.assertTrue(settings.customer_pack_llm_egress_denied)
            self.assertEqual(settings.llm_allowed_hosts, ())
            self.assertFalse(settings.llm_local_ready())

    def test_pilot_profile_blocks_kimi_alias_vlm(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "AEROBIM_ENV": "development",
                "AEROBIM_SIGNOFF_PROFILE": "samolet_pilot",
                "AEROBIM_KIMI_K3_ENABLED": "true",
            },
            clear=False,
        ):
            os.environ.pop("AEROBIM_VLM_ENABLED", None)
            os.environ.pop("AEROBIM_KIMI_API_BASE_URL", None)
            os.environ.pop("AEROBIM_VLM_API_BASE_URL", None)
            settings = Settings.from_env()
            self.assertTrue(settings.vlm_enabled)
            self.assertFalse(
                settings.vlm_advisory_ready(),
                "samolet_pilot must hard-disable Kimi/VLM egress",
            )

    def test_advisory_env_preferred_over_deprecated_local(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "AEROBIM_ENV": "development",
                "AEROBIM_SIGNOFF_PROFILE": "development",
                "AEROBIM_LLM_ADVISORY_ENABLED": "false",
                "AEROBIM_LLM_LOCAL_ENABLED": "true",
            },
            clear=False,
        ):
            settings = Settings.from_env()
            self.assertFalse(settings.llm_local_enabled)

    def test_deprecated_local_alias_still_works_when_advisory_unset(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "AEROBIM_ENV": "development",
                "AEROBIM_SIGNOFF_PROFILE": "development",
                "AEROBIM_LLM_LOCAL_ENABLED": "false",
            },
            clear=False,
        ):
            os.environ.pop("AEROBIM_LLM_ADVISORY_ENABLED", None)
            settings = Settings.from_env()
            self.assertFalse(settings.llm_local_enabled)
            self.assertFalse(settings.llm_advisory_enabled)

    def test_deprecated_local_alias_emits_warning_on_boot(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "AEROBIM_ENV": "development",
                "AEROBIM_SIGNOFF_PROFILE": "development",
                "AEROBIM_LLM_LOCAL_ENABLED": "false",
            },
            clear=False,
        ):
            os.environ.pop("AEROBIM_LLM_ADVISORY_ENABLED", None)
            with self.assertLogs("aerobim.core.config.settings", level="WARNING") as cm:
                Settings.from_env()
            self.assertTrue(
                any("AEROBIM_LLM_LOCAL_ENABLED is deprecated" in line for line in cm.output),
                cm.output,
            )
            self.assertTrue(any("2026-09-21" in line for line in cm.output), cm.output)


if __name__ == "__main__":
    unittest.main()
