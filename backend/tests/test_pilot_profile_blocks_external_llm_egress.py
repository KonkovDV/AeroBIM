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
