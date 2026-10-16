"""RocksDB large-file path reconciles instance counts against the SPF source."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.infrastructure.adapters import ifc_file_open as mod

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "samples" / "ifc" / "clash-two-overlapping-boxes.ifc"


@unittest.skipUnless(mod.rocksdb_backend_available(), "IfcOpenShell build without RocksDB")
class RocksDbReconcileTests(unittest.TestCase):
    def setUp(self) -> None:
        mod.reset_ifc_parse_cache_for_tests()
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(mod.reset_ifc_parse_cache_for_tests)
        self.root = Path(self._tmp.name)
        mod.configure_ifc_parse_cache(self.root / "cache")
        self.src = self.root / "model.ifc"
        self.src.write_bytes(FIXTURE.read_bytes())
        env = patch.dict(os.environ, {"AEROBIM_MAX_IFC_BYTES": "1"}, clear=False)
        env.start()
        self.addCleanup(env.stop)

    def _rdb(self) -> Path:
        stat = self.src.resolve().stat()
        return mod._rdb_cache_dir(self.src.resolve(), stat.st_mtime_ns, stat.st_size)

    def test_conversion_writes_matching_marker(self) -> None:
        model = mod.open_ifc_model(self.src)
        try:
            self.assertIsNotNone(getattr(model, "storage", None))
        finally:
            mod.close_ifc_model(model)
        marker = json.loads(mod._rdb_reconcile_marker(self._rdb()).read_text(encoding="utf-8"))
        expected = mod._count_spf_instances(self.src)
        self.assertTrue(marker["reconciled"])
        self.assertEqual(marker["spf_instances"], expected)
        self.assertEqual(marker["rocksdb_instances"], expected)

    def test_lost_instances_discard_store_and_raise(self) -> None:
        real = mod._count_spf_instances
        with patch.object(mod, "_count_spf_instances", side_effect=lambda p: real(p) + 1):
            with self.assertRaises(mod.IfcRocksDbReconcileError) as ctx:
                mod.open_ifc_model(self.src)
        self.assertEqual(ctx.exception.spf_instances, ctx.exception.rocksdb_instances + 1)
        self.assertIn("lost instances", str(ctx.exception))
        self.assertFalse(self._rdb().exists())
        self.assertFalse(mod._rdb_reconcile_marker(self._rdb()).exists())

    def test_store_without_marker_is_rebuilt(self) -> None:
        model = mod.open_ifc_model(self.src)
        mod.close_ifc_model(model)
        # Drop the last Python handle so RocksDB releases its LOCK before rebuild.
        del model
        mod.reset_ifc_parse_cache_for_tests()
        mod.configure_ifc_parse_cache(self.root / "cache")
        mod._rdb_reconcile_marker(self._rdb()).unlink()
        self.assertFalse(mod._rdb_ready(self._rdb()))
        model = mod.open_ifc_model(self.src)
        mod.close_ifc_model(model)
        self.assertTrue(mod._rdb_ready(self._rdb()))
        self.assertEqual(mod.ifc_parse_cache_stats()["rocksdb_converts"], 1)

    def test_marker_with_mismatch_is_not_ready(self) -> None:
        rdb = self.root / "fake-rdb"
        rdb.mkdir()
        (rdb / "CURRENT").write_text("x", encoding="utf-8")
        mod._rdb_reconcile_marker(rdb).write_text(
            json.dumps({"reconciled": True, "spf_instances": 3, "rocksdb_instances": 2}),
            encoding="utf-8",
        )
        self.assertFalse(mod._rdb_ready(rdb))


if __name__ == "__main__":
    unittest.main()
