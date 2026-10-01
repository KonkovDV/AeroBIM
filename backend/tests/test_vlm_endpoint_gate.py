"""Unit tests for VLM endpoint / model refuse gate (RT-20260811-02/03)."""

from __future__ import annotations

import unittest

from aerobim.core.config.vlm_endpoint_gate import (
    endpoint_looks_like_yandex,
    refuse_yandex_kimi_default_model,
)


class EndpointLooksLikeYandexTests(unittest.TestCase):
    def test_exact_allowed_yandex_hosts(self) -> None:
        for url in (
            "https://llm.api.cloud.yandex.net/v1",
            "https://ai.api.cloud.yandex.net/v1",
        ):
            with self.subTest(url=url):
                self.assertTrue(endpoint_looks_like_yandex(url))

    def test_substring_not_yandex_is_false(self) -> None:
        self.assertFalse(endpoint_looks_like_yandex("https://not-yandex.evil/v1"))
        self.assertFalse(endpoint_looks_like_yandex("https://yandex.attacker.example/v1"))

    def test_unknown_host_without_provider(self) -> None:
        self.assertFalse(endpoint_looks_like_yandex("https://cdn.example-cdn.net/v1"))

    def test_provider_yandex_unknown_host_or_ip(self) -> None:
        self.assertTrue(
            endpoint_looks_like_yandex("https://cdn.example-cdn.net/v1", provider="yandex")
        )
        self.assertTrue(endpoint_looks_like_yandex("https://1.2.3.4/v1", provider="yandex"))
        self.assertTrue(endpoint_looks_like_yandex(None, provider="yandex-ai-studio"))
        self.assertTrue(endpoint_looks_like_yandex("", provider="yandex"))

    def test_non_yandex_markers_win_over_provider(self) -> None:
        self.assertFalse(
            endpoint_looks_like_yandex("https://api.moonshot.cn/v1", provider="yandex")
        )
        self.assertFalse(endpoint_looks_like_yandex("https://localhost:8080/v1", provider="yandex"))

    def test_malformed_and_empty(self) -> None:
        self.assertFalse(endpoint_looks_like_yandex("not a url"))
        self.assertFalse(endpoint_looks_like_yandex(None))


class RefuseYandexKimiDefaultTests(unittest.TestCase):
    def test_refuses_kimi_on_exact_yandex(self) -> None:
        reason = refuse_yandex_kimi_default_model(
            base_url="https://llm.api.cloud.yandex.net/v1",
            model="kimi-k3",
            provider="yandex",
        )
        self.assertIsNotNone(reason)
        self.assertIn("Yandex Studio", reason or "")

    def test_refuses_empty_model_on_yandex_provider_ip(self) -> None:
        self.assertIsNotNone(
            refuse_yandex_kimi_default_model(
                base_url="https://1.2.3.4/v1",
                model="",
                provider="yandex",
            )
        )

    def test_allows_qwen_on_yandex(self) -> None:
        self.assertIsNone(
            refuse_yandex_kimi_default_model(
                base_url="https://llm.api.cloud.yandex.net/v1",
                model="gpt://folder/qwen3.6-35b-a3b",
                provider="yandex",
            )
        )

    def test_substring_host_does_not_refuse_without_provider(self) -> None:
        self.assertIsNone(
            refuse_yandex_kimi_default_model(
                base_url="https://not-yandex.evil/v1",
                model="kimi-k3",
                provider=None,
            )
        )

    def test_moonshot_keeps_kimi_even_if_provider_says_yandex(self) -> None:
        self.assertIsNone(
            refuse_yandex_kimi_default_model(
                base_url="https://api.moonshot.cn/v1",
                model="kimi-k3",
                provider="yandex",
            )
        )


if __name__ == "__main__":
    unittest.main()
