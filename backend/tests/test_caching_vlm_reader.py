"""§2.1 CachingVlmReader + FilesystemVlmResponseStore — replay + integrity tests."""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path

from aerobim.domain.vlm_cache import InMemoryVlmResponseStore, build_cache_entry, vlm_cache_key
from aerobim.domain.vlm_normalize import NORMALIZER_VERSION
from aerobim.infrastructure.adapters.caching_vlm_reader import (
    CachingVlmReader,
    FilesystemVlmResponseStore,
)
from aerobim.infrastructure.adapters.vlm_advisory_client import VlmReadResult

_CONTENT = {"readable": True, "observations": []}


class _CountingReader:
    def __init__(self) -> None:
        self.calls = 0

    def read_region(
        self, image_bytes: bytes, *, media_type: str, sheet_id: str, region_id: str, prompt: str
    ) -> VlmReadResult:
        self.calls += 1
        return VlmReadResult(content=_CONTENT, usage={}, determinism_basis="live")


def _read(reader: CachingVlmReader, image: bytes = b"img") -> VlmReadResult:
    return reader.read_region(
        image, media_type="image/png", sheet_id="AR-01", region_id="stamp", prompt="p"
    )


class CachingVlmReaderTests(unittest.TestCase):
    def test_miss_then_hit_avoids_second_call(self) -> None:
        inner = _CountingReader()
        reader = CachingVlmReader(inner, InMemoryVlmResponseStore(), model="kimi-k3")
        first = _read(reader)
        second = _read(reader)
        self.assertEqual(inner.calls, 1)  # second served from cache
        self.assertEqual(second.determinism_basis, "vlm_cache_replay")
        self.assertEqual(first.content, second.content)

    def test_different_image_is_a_miss(self) -> None:
        inner = _CountingReader()
        reader = CachingVlmReader(inner, InMemoryVlmResponseStore(), model="kimi-k3")
        _read(reader, b"img-a")
        _read(reader, b"img-b")
        self.assertEqual(inner.calls, 2)

    def test_effective_region_prompt_participates_in_cache_key(self) -> None:
        """json_object prompt rewrite must change the cache identity."""

        class _ExpandingReader:
            def __init__(self) -> None:
                self.calls = 0

            def effective_region_prompt(self, prompt: str) -> str:
                return f"{prompt}::expanded"

            def read_region(
                self,
                image_bytes: bytes,
                *,
                media_type: str,
                sheet_id: str,
                region_id: str,
                prompt: str,
            ) -> VlmReadResult:
                self.calls += 1
                return VlmReadResult(
                    content={"readable": True, "observations": [], "n": self.calls},
                    usage={},
                    determinism_basis="live",
                )

        inner = _ExpandingReader()
        store = InMemoryVlmResponseStore()
        reader = CachingVlmReader(inner, store, model="gpt://folder/qwen")
        first = _read(reader)
        # Mutate expansion contract → must miss even if caller prompt unchanged.
        inner.effective_region_prompt = lambda prompt: f"{prompt}::expanded-v2"  # type: ignore[method-assign]
        second = _read(reader)
        self.assertEqual(inner.calls, 2)
        self.assertNotEqual(first.content.get("n"), second.content.get("n"))

    def test_tampered_entry_fails_closed_to_miss(self) -> None:
        inner = _CountingReader()
        store = InMemoryVlmResponseStore()
        key = vlm_cache_key(
            image_bytes=b"img", prompt="p", model="kimi-k3", normalizer_version=NORMALIZER_VERSION
        )
        store.put(key, {"content": {"x": 1}, "content_sha256": "wrong-hash"})
        reader = CachingVlmReader(inner, store, model="kimi-k3")
        result = _read(reader)
        self.assertEqual(inner.calls, 1)  # corrupt entry ignored → underlying called
        self.assertEqual(result.content, _CONTENT)

    def test_request_mismatch_fails_closed_to_miss(self) -> None:
        # Golden hash valid, but the stored entry was produced for a DIFFERENT image
        # (second integrity layer): must be treated as a miss, not replayed.
        inner = _CountingReader()
        store = InMemoryVlmResponseStore()
        key = vlm_cache_key(
            image_bytes=b"img", prompt="p", model="kimi-k3", normalizer_version=NORMALIZER_VERSION
        )
        store.put(
            key,
            build_cache_entry(
                image_bytes=b"DIFFERENT", prompt="p", model="kimi-k3", content={"ok": True}
            ),
        )
        reader = CachingVlmReader(inner, store, model="kimi-k3")
        result = _read(reader)  # image_bytes=b"img" -> entry_matches_request False
        self.assertEqual(inner.calls, 1)
        self.assertEqual(result.content, _CONTENT)

    def test_stored_entry_records_provenance(self) -> None:
        inner = _CountingReader()
        store = InMemoryVlmResponseStore()
        reader = CachingVlmReader(
            inner, store, model="kimi-k3", endpoint="https://x/v1", request_schema_hash="sh"
        )
        _read(reader)
        key = vlm_cache_key(
            image_bytes=b"img",
            prompt="p",
            model="kimi-k3",
            request_schema_hash="sh",
            normalizer_version=NORMALIZER_VERSION,
        )
        entry = store.get(key)
        assert entry is not None
        self.assertEqual(entry["provenance"]["endpoint"], "https://x/v1")
        self.assertEqual(entry["provenance"]["request_schema_hash"], "sh")
        self.assertIn("normalizer_version", entry["provenance"])

    def test_reasoning_effort_change_avoids_stale_replay(self) -> None:
        # Config change (low->high) with same image/prompt/model must NOT replay
        # the stale cached answer — different key.
        store = InMemoryVlmResponseStore()
        inner = _CountingReader()
        _read(CachingVlmReader(inner, store, model="kimi-k3", reasoning_effort="low"))
        self.assertEqual(inner.calls, 1)
        _read(CachingVlmReader(inner, store, model="kimi-k3", reasoning_effort="high"))
        self.assertEqual(inner.calls, 2)

    def test_namespace_isolation_no_cross_tenant_replay(self) -> None:
        store = InMemoryVlmResponseStore()
        inner = _CountingReader()
        _read(CachingVlmReader(inner, store, model="kimi-k3", cache_namespace="tenant-a"))
        self.assertEqual(inner.calls, 1)
        _read(CachingVlmReader(inner, store, model="kimi-k3", cache_namespace="tenant-b"))
        self.assertEqual(inner.calls, 2)  # different tenant -> no shared cache

    def test_project_isolation_no_cross_project_replay(self) -> None:
        store = InMemoryVlmResponseStore()
        inner = _CountingReader()
        _read(
            CachingVlmReader(
                inner, store, model="kimi-k3", cache_namespace="t1", cache_project="p1"
            )
        )
        self.assertEqual(inner.calls, 1)
        _read(
            CachingVlmReader(
                inner, store, model="kimi-k3", cache_namespace="t1", cache_project="p2"
            )
        )
        self.assertEqual(inner.calls, 2)  # same tenant, different project -> no shared cache

    def test_stored_entry_records_metrics(self) -> None:
        store = InMemoryVlmResponseStore()
        inner = _CountingReader()
        reader = CachingVlmReader(inner, store, model="kimi-k3", reasoning_effort="low")
        _read(reader)
        key = vlm_cache_key(
            image_bytes=b"img",
            prompt="p",
            model="kimi-k3",
            reasoning_effort="low",
            normalizer_version=NORMALIZER_VERSION,
        )
        entry = store.get(key)
        assert entry is not None
        self.assertEqual(entry["cache_format_version"], "2")
        self.assertEqual(entry["reasoning_effort"], "low")
        self.assertIn("latency_ms", entry["metrics"])
        self.assertIn("recorded_at", entry["metrics"])

    def test_filesystem_store_enables_cross_instance_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemVlmResponseStore(Path(tmp))
            inner1 = _CountingReader()
            _read(CachingVlmReader(inner1, store, model="kimi-k3"))
            self.assertEqual(inner1.calls, 1)
            # A fresh reader + fresh store over the same dir replays without a call.
            inner2 = _CountingReader()
            fresh = CachingVlmReader(inner2, FilesystemVlmResponseStore(Path(tmp)), model="kimi-k3")
            result = _read(fresh)
            self.assertEqual(inner2.calls, 0)
            self.assertEqual(result.determinism_basis, "vlm_cache_replay")


class FilesystemVlmResponseStoreTests(unittest.TestCase):
    def test_put_get_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemVlmResponseStore(Path(tmp))
            key = "a" * 64  # sha256-hex shape (the only accepted key form)
            self.assertIsNone(store.get("b" * 64))
            store.put(key, {"content": {"a": 1}, "content_sha256": "h"})
            self.assertEqual(store.get(key), {"content": {"a": 1}, "content_sha256": "h"})

    def test_corrupt_file_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = "c" * 64
            (root / f"{key}.json").write_text("{not-json", encoding="utf-8")
            self.assertIsNone(FilesystemVlmResponseStore(root).get(key))

    def test_unsafe_key_fails_closed(self) -> None:
        # §5.11: a key must be sha256 hex; traversal / non-hex / wrong length must
        # never touch the filesystem (get miss, put no-op).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = FilesystemVlmResponseStore(root)
            for bad in ("../escape", "k1", "A" * 64, "a" * 63, "a" * 65, "a/b", ".."):
                store.put(bad, {"content": {"a": 1}, "content_sha256": "h"})
                self.assertIsNone(store.get(bad), bad)
            self.assertEqual(list(root.glob("*.json")), [])  # nothing written

    def test_ttl_expiry_is_a_miss_and_deletes(self) -> None:
        # §5.10: an entry older than the TTL is a miss and is deleted on read.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = "a" * 64
            store = FilesystemVlmResponseStore(root, ttl_seconds=1.0)
            store.put(key, {"content": {"a": 1}, "content_sha256": "h"})
            path = root / f"{key}.json"
            self.assertTrue(path.exists())
            past = time.time() - 3600
            os.utime(path, (past, past))  # backdate beyond the TTL
            self.assertIsNone(store.get(key))
            self.assertFalse(path.exists())  # explicit deletion policy

    def test_symlink_target_is_refused(self) -> None:
        # §5.11: a planted symlink at the target must never be followed.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = "b" * 64
            real = root / "real.json"
            real.write_text('{"content": {"x": 1}, "content_sha256": "h"}', encoding="utf-8")
            link = root / f"{key}.json"
            try:
                os.symlink(real, link)
            except (OSError, NotImplementedError, AttributeError):
                self.skipTest("symlinks not supported in this environment")
            self.assertIsNone(FilesystemVlmResponseStore(root).get(key))


if __name__ == "__main__":
    unittest.main()
