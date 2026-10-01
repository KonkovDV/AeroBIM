"""Fail-closed tenant isolation for the advisory VLM cache (§5; RT 2026-07-28).

The advisory pipeline is a process singleton with no per-request identity, so a
persistent response cache must never be built without a trusted, deployment-
configured namespace — otherwise one tenant's stored answer could be replayed
for another. These are negative/boundary tests (a bypass attempt must fail
closed), not a proof that the cache is "secure" in general.
"""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _ready_settings(**over: object):
    """Dev-profile settings with advisory ready (open-data tier); replace() skips
    the SSRF boot gate so no network is touched."""
    from aerobim.core.config.settings import Settings

    base = replace(
        Settings.from_env(),
        vlm_enabled=True,
        vlm_api_base_url="https://127.0.0.1:9/v1",
        vlm_api_key="test-key",
    )
    return replace(base, **over)


class SafeCacheNamespaceTests(unittest.TestCase):
    def test_rejects_unsafe_and_empty(self) -> None:
        from aerobim.infrastructure.di.bootstrap import _safe_cache_namespace

        for bad in (None, "", "   ", ".", "..", "../evil", "a/b", "a\\b", "x" * 65, "тенант"):
            self.assertIsNone(_safe_cache_namespace(bad), bad)

    def test_accepts_trusted_scope(self) -> None:
        from aerobim.infrastructure.di.bootstrap import _safe_cache_namespace

        self.assertEqual(_safe_cache_namespace("tenant-a"), "tenant-a")
        self.assertEqual(_safe_cache_namespace(" tenant_a.1 "), "tenant_a.1")


class AdvisoryCacheTenantIsolationTests(unittest.TestCase):
    def _reader(self, settings: object) -> object:
        from aerobim.core.di.tokens import Tokens
        from aerobim.infrastructure.di.bootstrap import bootstrap_container

        pipeline = bootstrap_container(settings).resolve(Tokens.ADVISORY_VLM_PIPELINE)
        self.assertTrue(pipeline.ready)
        return pipeline._reader

    def test_cache_disabled_without_namespace(self) -> None:
        from aerobim.infrastructure.adapters.caching_vlm_reader import CachingVlmReader

        reader = self._reader(_ready_settings(vlm_cache_dir="var/kimi-cache"))
        # Fail-closed: a cache dir without a tenant scope must NOT build a store.
        self.assertNotIsInstance(reader, CachingVlmReader)

    def test_cache_enabled_and_physically_scoped_with_namespace(self) -> None:
        from aerobim.infrastructure.adapters.caching_vlm_reader import (
            CachingVlmReader,
            FilesystemVlmResponseStore,
        )

        reader = self._reader(
            _ready_settings(vlm_cache_dir="var/kimi-cache", vlm_cache_namespace="tenant-a")
        )
        self.assertIsInstance(reader, CachingVlmReader)
        store = reader._store
        self.assertIsInstance(store, FilesystemVlmResponseStore)
        self.assertIn("tenant-a", str(store._root))

    def test_two_tenants_get_distinct_store_roots(self) -> None:
        a = self._reader(
            _ready_settings(vlm_cache_dir="var/kimi-cache", vlm_cache_namespace="tenant-a")
        )
        b = self._reader(
            _ready_settings(vlm_cache_dir="var/kimi-cache", vlm_cache_namespace="tenant-b")
        )
        self.assertNotEqual(str(a._store._root), str(b._store._root))

    def test_path_unsafe_namespace_fails_closed(self) -> None:
        from aerobim.infrastructure.adapters.caching_vlm_reader import CachingVlmReader

        for bad in ("../evil", "a/b", "..", "x" * 65, "тенант"):
            reader = self._reader(
                _ready_settings(vlm_cache_dir="var/kimi-cache", vlm_cache_namespace=bad)
            )
            self.assertNotIsInstance(reader, CachingVlmReader, bad)

    def test_cache_scoped_by_project(self) -> None:
        from aerobim.infrastructure.adapters.caching_vlm_reader import CachingVlmReader

        reader = self._reader(
            _ready_settings(
                vlm_cache_dir="var/kimi-cache",
                vlm_cache_namespace="tenant-a",
                vlm_cache_project="proj-x",
            )
        )
        self.assertIsInstance(reader, CachingVlmReader)
        root = str(reader._store._root)
        self.assertIn("tenant-a", root)
        self.assertIn("proj-x", root)

    def test_invalid_project_fails_closed(self) -> None:
        from aerobim.infrastructure.adapters.caching_vlm_reader import CachingVlmReader

        reader = self._reader(
            _ready_settings(
                vlm_cache_dir="var/kimi-cache",
                vlm_cache_namespace="tenant-a",
                vlm_cache_project="../evil",
            )
        )
        # A configured-but-path-unsafe project must not silently drop to tenant scope.
        self.assertNotIsInstance(reader, CachingVlmReader)


if __name__ == "__main__":
    unittest.main()
