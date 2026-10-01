"""Unit tests for Yandex auth / think-off on VlmAdvisoryClient (no network)."""

from __future__ import annotations

import json
import unittest

from aerobim.infrastructure.adapters.vlm_advisory_client import (
    VlmAdvisoryClient,
    profile_for,
    yandex_studio_vlm_profile,
)


class YandexVlmClientTests(unittest.TestCase):
    def test_profile_for_gpt_uri(self) -> None:
        profile = profile_for("gpt://folder/qwen3.6-35b-a3b")
        self.assertEqual(profile.determinism_basis, "vendor_think_off")
        self.assertTrue(profile.send_temperature)
        self.assertEqual(profile.response_format.get("type"), "json_object")

    def test_yandex_headers_and_think_off(self) -> None:
        captured: dict[str, object] = {}

        def transport(url: str, headers: dict[str, str], body: bytes) -> bytes:
            captured["url"] = url
            captured["headers"] = headers
            captured["body"] = json.loads(body.decode("utf-8"))
            return json.dumps(
                {
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {
                                "content": json.dumps(
                                    {
                                        "readable": True,
                                        "observations": [
                                            {
                                                "kind": "dimension",
                                                "raw_value": "150 mm",
                                                "bbox_rel": [0.1, 0.1, 0.4, 0.3],
                                                "confidence": 0.8,
                                            }
                                        ],
                                    }
                                )
                            },
                        }
                    ],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                }
            ).encode("utf-8")

        client = VlmAdvisoryClient(
            base_url="https://llm.api.cloud.yandex.net/v1",
            api_key="secret-key",
            model="gpt://b1gtest/qwen3.6-35b-a3b",
            profile=yandex_studio_vlm_profile("gpt://b1gtest/qwen3.6-35b-a3b"),
            auth_scheme="Api-Key",
            folder_id="b1gtest",
            transport=transport,
        )
        result = client.read_region(
            b"\x89PNG",
            media_type="image/png",
            sheet_id="S1",
            region_id="r1",
            prompt="read dimensions",
        )
        headers = captured["headers"]
        assert isinstance(headers, dict)
        self.assertEqual(headers["Authorization"], "Api-Key secret-key")
        self.assertEqual(headers["x-folder-id"], "b1gtest")
        self.assertEqual(headers["x-data-logging-enabled"], "false")
        body = captured["body"]
        assert isinstance(body, dict)
        self.assertEqual(body["chat_template_kwargs"], {"enable_thinking": False})
        self.assertNotIn("tools", body)
        self.assertEqual(body.get("temperature"), 0)
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertTrue(result.content.get("readable"))
        self.assertEqual(result.determinism_basis, "vendor_think_off")


if __name__ == "__main__":
    unittest.main()
