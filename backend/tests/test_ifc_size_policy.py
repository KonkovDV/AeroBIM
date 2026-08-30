"""IFC analyze cap vs ingest envelope — four numbers, not one."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.core.security.upload_limits import (
    DEV_DEFAULT_UPLOAD_BYTES,
    SAMOLET_STATED_MODEL_BYTES,
)
from aerobim.domain.ifc_size_policy import (
    BACKEND_ROCKSDB,
    BAND_ANALYZE_BLOCKED_INGEST_OK,
    BAND_ANALYZE_DISK,
    BAND_ANALYZE_OK,
    BAND_OVER_INGEST,
    BSI_VALIDATE_UNCOMPRESSED_IFC_BYTES,
    PUBLIC_ANALYZE_CAP_DETAIL,
    PUBLIC_IFC_DISK_BACKEND_DETAIL,
    ROCKSDB_BACKEND_STATUS,
    SPF_RAM_MULTIPLIER_LITERATURE,
    IfcAnalyzeCapError,
    IfcDiskBackendError,
    classify_ifc_bytes,
    literature_spf_rss_bytes,
    raise_if_over_analyze_cap,
    size_policy_snapshot,
)
from aerobim.domain.ifc_streaming_design import streaming_design_snapshot


class IfcSizePolicyTests(unittest.TestCase):
    def test_analyze_ok_under_256_mib(self) -> None:
        decision = classify_ifc_bytes(DEV_DEFAULT_UPLOAD_BYTES)
        self.assertTrue(decision.analyze_allowed)
        self.assertEqual(decision.band, BAND_ANALYZE_OK)
        self.assertFalse(decision.raises_default_cap)

    def test_gap_band_over_spf_under_ingest_is_disk(self) -> None:
        size = DEV_DEFAULT_UPLOAD_BYTES + 1
        decision = classify_ifc_bytes(size)
        self.assertTrue(decision.analyze_allowed)
        self.assertTrue(decision.ingest_would_accept)
        self.assertEqual(decision.band, BAND_ANALYZE_DISK)
        self.assertEqual(decision.backend, BACKEND_ROCKSDB)
        self.assertEqual(decision.band, BAND_ANALYZE_BLOCKED_INGEST_OK)
        self.assertTrue(decision.over_bsi_uncompressed)

    def test_over_stated_ingest(self) -> None:
        decision = classify_ifc_bytes(SAMOLET_STATED_MODEL_BYTES + 1)
        self.assertEqual(decision.band, BAND_OVER_INGEST)
        self.assertFalse(decision.ingest_would_accept)

    def test_bsi_decimal_mb_is_not_mib(self) -> None:
        self.assertLess(BSI_VALIDATE_UNCOMPRESSED_IFC_BYTES, DEV_DEFAULT_UPLOAD_BYTES)
        mid = (BSI_VALIDATE_UNCOMPRESSED_IFC_BYTES + DEV_DEFAULT_UPLOAD_BYTES) // 2
        decision = classify_ifc_bytes(mid)
        self.assertTrue(decision.analyze_allowed)
        self.assertTrue(decision.over_bsi_uncompressed)

    def test_literature_multiplier_is_ten_and_not_a_measurement(self) -> None:
        self.assertEqual(SPF_RAM_MULTIPLIER_LITERATURE, 10)
        self.assertEqual(literature_spf_rss_bytes(256), 2560)
        snap = size_policy_snapshot()
        self.assertFalse(snap["raises_default_cap"])
        self.assertEqual(snap["rocksdb_backend"], ROCKSDB_BACKEND_STATUS)
        self.assertEqual(
            snap["bsi_validate_uncompressed_ifc_bytes"],
            BSI_VALIDATE_UNCOMPRESSED_IFC_BYTES,
        )
        self.assertTrue(snap["bsi_faq_heading_not_used_for_classification"])
        self.assertEqual(
            snap["literature_rss_at_ingest_cap_bytes"],
            SAMOLET_STATED_MODEL_BYTES * 10,
        )

    def test_raise_if_over_analyze_cap(self) -> None:
        with self.assertRaises(IfcAnalyzeCapError) as ctx:
            raise_if_over_analyze_cap(SAMOLET_STATED_MODEL_BYTES + 1)
        self.assertEqual(str(ctx.exception), PUBLIC_ANALYZE_CAP_DETAIL)
        self.assertEqual(ctx.exception.decision.band, BAND_OVER_INGEST)

    def test_open_ifc_model_refuses_over_ingest(self) -> None:
        from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_model

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "over.ifc"
            path.write_bytes(b"x" * 9)
            env = {"AEROBIM_MAX_IFC_BYTES": "8", "AEROBIM_MAX_MODEL_BYTES": "8"}
            with patch.dict(os.environ, env, clear=False):
                with self.assertRaises(IfcAnalyzeCapError):
                    open_ifc_model(path)

    def test_open_over_spf_cap_uses_rocksdb(self) -> None:
        from aerobim.infrastructure.adapters.ifc_file_open import (
            close_ifc_model,
            configure_ifc_parse_cache,
            ifc_engine_path,
            open_ifc_model,
            reset_ifc_parse_cache_for_tests,
            rocksdb_backend_available,
        )

        self.assertTrue(rocksdb_backend_available())
        repo = Path(__file__).resolve().parents[2]
        fixture = repo / "samples" / "ifc" / "wall-pset-ifc2x3.ifc"
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            configure_ifc_parse_cache(tmp)
            model = None
            walls: list[object] | None = None
            try:
                with patch.dict(os.environ, {"AEROBIM_MAX_IFC_BYTES": "1"}, clear=False):
                    model = open_ifc_model(fixture)
                    engine = ifc_engine_path(fixture)
                walls = list(model.by_type("IfcWall"))
                self.assertEqual(len(walls), 1)
                self.assertTrue(getattr(model, "storage", None) is not None)
                self.assertTrue(engine.is_dir())
                self.assertTrue((engine / "CURRENT").is_file())
            finally:
                walls = None
                if model is not None:
                    close_ifc_model(model)
                    model = None
                reset_ifc_parse_cache_for_tests()

    def test_streaming_snapshot_includes_size_policy(self) -> None:
        snap = streaming_design_snapshot()
        self.assertEqual(snap["rocksdb_backend"], ROCKSDB_BACKEND_STATUS)
        self.assertFalse(snap["raises_default_cap"])
        self.assertEqual(snap["spf_ram_multiplier_literature"], 10)
        self.assertIn("size_policy", snap)

    def test_rss_probe_opens_committed_fixture_and_refuses_docs_for_tmp(self) -> None:
        from aerobim.tools.measure_ifc_open_rss import measure_ifc_open_rss

        repo = Path(__file__).resolve().parents[2]
        fixture = repo / "samples" / "ifc" / "wall-pset-ifc2x3.ifc"
        payload = measure_ifc_open_rss(fixture, repo=repo)
        self.assertTrue(payload["opened"])
        self.assertTrue(payload["sample_in_git"])
        self.assertFalse(payload["raises_default_cap"])
        self.assertTrue(payload["tiny_fixture_rss_delta_is_import_noise"])
        self.assertEqual(payload["size_decision"]["band"], BAND_ANALYZE_OK)
        with tempfile.TemporaryDirectory() as tmp:
            over = Path(tmp) / "over.ifc"
            over.write_bytes(b"x" * 9)
            blocked = measure_ifc_open_rss(over, repo=repo, analyze_cap_bytes=8, ingest_cap_bytes=8)
        self.assertFalse(blocked["opened"])
        self.assertEqual(blocked["size_decision"]["band"], BAND_OVER_INGEST)
        self.assertFalse(blocked["sample_in_git"])

    def test_rss_probe_honors_env_spf_cap_via_disk(self) -> None:
        from aerobim.infrastructure.adapters.ifc_file_open import (
            configure_ifc_parse_cache,
            reset_ifc_parse_cache_for_tests,
        )
        from aerobim.tools.measure_ifc_open_rss import measure_ifc_open_rss

        repo = Path(__file__).resolve().parents[2]
        fixture = repo / "samples" / "ifc" / "wall-pset-ifc2x3.ifc"
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            configure_ifc_parse_cache(tmp)
            try:
                with patch.dict(os.environ, {"AEROBIM_MAX_IFC_BYTES": "8"}, clear=False):
                    payload = measure_ifc_open_rss(fixture, repo=repo)
            finally:
                reset_ifc_parse_cache_for_tests()
        self.assertTrue(payload["opened"])
        self.assertTrue(payload["analyze_cap_differs_from_git_default"])
        self.assertEqual(payload["size_decision"]["band"], BAND_ANALYZE_DISK)

    def test_analyze_cap_error_is_runtime_error(self) -> None:
        # HTTP maps this to 413 before the generic RuntimeError → 503 handler.
        self.assertTrue(issubclass(IfcAnalyzeCapError, RuntimeError))
        self.assertTrue(issubclass(IfcDiskBackendError, RuntimeError))

    def test_public_http_detail_matches_domain(self) -> None:
        from aerobim.presentation.http.errors import (
            public_ifc_analyze_cap_detail,
            public_ifc_disk_backend_detail,
        )

        self.assertEqual(public_ifc_analyze_cap_detail(), PUBLIC_ANALYZE_CAP_DETAIL)
        self.assertEqual(public_ifc_disk_backend_detail(), PUBLIC_IFC_DISK_BACKEND_DETAIL)
        from aerobim.presentation.http.errors import public_ifc_analyze_cap_body

        body = public_ifc_analyze_cap_body()
        self.assertEqual(body["message"], PUBLIC_ANALYZE_CAP_DETAIL)
        self.assertEqual(body["required_profile"], "samolet_pilot")
        self.assertFalse(body["rss_measured"])


if __name__ == "__main__":
    unittest.main()
