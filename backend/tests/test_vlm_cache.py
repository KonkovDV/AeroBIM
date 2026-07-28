"""§2.1 deterministic VLM cache — key stability + golden-hash integrity tests."""

from __future__ import annotations

import unittest

from aerobim.domain.vlm_cache import (
    InMemoryVlmResponseStore,
    build_cache_entry,
    content_sha256,
    entry_content_if_intact,
    entry_matches_request,
    vlm_cache_key,
)


class VlmCacheKeyTests(unittest.TestCase):
    def test_key_is_stable_for_same_inputs(self) -> None:
        a = vlm_cache_key(image_bytes=b"img", prompt="p", model="kimi-k3")
        b = vlm_cache_key(image_bytes=b"img", prompt="p", model="kimi-k3")
        self.assertEqual(a, b)

    def test_key_changes_with_image_prompt_or_model(self) -> None:
        base = vlm_cache_key(image_bytes=b"img", prompt="p", model="kimi-k3")
        self.assertNotEqual(base, vlm_cache_key(image_bytes=b"IMG", prompt="p", model="kimi-k3"))
        self.assertNotEqual(base, vlm_cache_key(image_bytes=b"img", prompt="P", model="kimi-k3"))
        self.assertNotEqual(base, vlm_cache_key(image_bytes=b"img", prompt="p", model="kimi-vl"))

    def test_key_discriminates_new_scopes(self) -> None:
        # Config/isolation scope must change the key (no stale replay, no cross-tenant).
        base = vlm_cache_key(image_bytes=b"img", prompt="p", model="kimi-k3")
        for kwargs in (
            {"namespace": "tenant-a"},
            {"project": "proj-a"},
            {"reasoning_effort": "high"},
            {"request_schema_hash": "schema-9"},
            {"normalizer_version": "9.9.9"},
        ):
            self.assertNotEqual(
                base,
                vlm_cache_key(image_bytes=b"img", prompt="p", model="kimi-k3", **kwargs),
                kwargs,
            )


class ContentHashTests(unittest.TestCase):
    def test_hash_stable_across_key_ordering(self) -> None:
        self.assertEqual(content_sha256({"a": 1, "b": 2}), content_sha256({"b": 2, "a": 1}))

    def test_hash_differs_on_value_change(self) -> None:
        self.assertNotEqual(content_sha256({"a": 1}), content_sha256({"a": 2}))


class CacheEntryTests(unittest.TestCase):
    def test_roundtrip_intact(self) -> None:
        content = {"readable": True, "observations": []}
        entry = build_cache_entry(image_bytes=b"img", prompt="p", model="kimi-k3", content=content)
        self.assertEqual(entry_content_if_intact(entry), content)
        self.assertEqual(entry["model"], "kimi-k3")

    def test_tampered_content_fails_closed(self) -> None:
        entry = build_cache_entry(image_bytes=b"img", prompt="p", model="kimi-k3", content={"x": 1})
        entry["content"] = {"x": 999}  # golden hash no longer matches
        self.assertIsNone(entry_content_if_intact(entry))

    def test_malformed_entry_fails_closed(self) -> None:
        self.assertIsNone(entry_content_if_intact("not-a-dict"))
        self.assertIsNone(entry_content_if_intact({"content": {"x": 1}}))  # no hash
        self.assertIsNone(entry_content_if_intact({"content_sha256": "z"}))  # no content

    def test_reproducibility_split_and_provenance(self) -> None:
        entry = build_cache_entry(
            image_bytes=b"img",
            prompt="p",
            model="kimi-k3",
            content={"x": 1},
            provenance={"endpoint": "https://x/v1", "request_schema_hash": "abc", "empty": ""},
        )
        self.assertEqual(entry["reproducibility"]["replay_reproducibility"], "guaranteed")
        self.assertIn("unverified", entry["reproducibility"]["model_determinism"])
        self.assertEqual(entry["provenance"]["endpoint"], "https://x/v1")
        self.assertNotIn("empty", entry["provenance"])  # blank values dropped

    def test_entry_matches_request_second_layer(self) -> None:
        entry = build_cache_entry(image_bytes=b"img", prompt="p", model="kimi-k3", content={"x": 1})
        self.assertTrue(
            entry_matches_request(entry, image_bytes=b"img", prompt="p", model="kimi-k3")
        )
        self.assertFalse(
            entry_matches_request(entry, image_bytes=b"OTHER", prompt="p", model="kimi-k3")
        )
        self.assertFalse(
            entry_matches_request(entry, image_bytes=b"img", prompt="p", model="kimi-vl")
        )
        self.assertFalse(entry_matches_request("nope", image_bytes=b"img", prompt="p", model="m"))

    def test_entry_records_metrics_and_format(self) -> None:
        entry = build_cache_entry(
            image_bytes=b"img",
            prompt="p",
            model="kimi-k3",
            content={"x": 1},
            usage={"prompt_tokens": 10},
            latency_ms=12.5,
            recorded_at="2026-07-28T00:00:00+00:00",
            namespace="t1",
            reasoning_effort="high",
        )
        self.assertEqual(entry["cache_format_version"], "2")
        self.assertEqual(entry["namespace"], "t1")
        self.assertEqual(entry["reasoning_effort"], "high")
        self.assertEqual(entry["metrics"]["usage"]["prompt_tokens"], 10)
        self.assertEqual(entry["metrics"]["latency_ms"], 12.5)
        self.assertIn("recorded_at", entry["metrics"])
        # Golden hash still covers content only (timestamp/usage don't break it).
        self.assertEqual(entry_content_if_intact(entry), {"x": 1})


class InMemoryStoreTests(unittest.TestCase):
    def test_put_get(self) -> None:
        store = InMemoryVlmResponseStore()
        self.assertIsNone(store.get("k"))
        store.put("k", {"content": {"x": 1}})
        self.assertEqual(store.get("k"), {"content": {"x": 1}})


if __name__ == "__main__":
    unittest.main()
