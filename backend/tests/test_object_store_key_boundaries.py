from __future__ import annotations

import unittest

from aerobim.core.security.object_key import normalize_object_key
from aerobim.infrastructure.adapters.local_object_store import LocalObjectStore
from aerobim.infrastructure.adapters.s3_object_store import S3ObjectStore


class ObjectStoreKeyBoundaryTests(unittest.TestCase):
    def test_normalizer_rejects_cross_platform_ambiguous_keys(self) -> None:
        keys = (
            "../outside",
            "tenant/../../outside",
            "/absolute",
            "C:/outside",
            "tenant\\..\\outside",
            "tenant/file.txt:secret",
            "tenant/NUL.txt",
            "tenant//file",
        )
        for key in keys:
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    normalize_object_key(key)

    def test_local_and_s3_stores_share_the_same_key_boundary(self) -> None:
        local = LocalObjectStore.__new__(LocalObjectStore)
        s3 = S3ObjectStore(bucket="bucket", region="test", prefix="aerobim")
        for key in ("../outside", "tenant/../../outside", "tenant/file.txt:secret"):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    local._normalise_key(key)
                with self.assertRaises(ValueError):
                    s3._qualify_key(key)

    def test_valid_key_is_canonical_and_prefix_is_idempotent(self) -> None:
        self.assertEqual(
            normalize_object_key(r" tenants\acme\uploads\model.ifc "),
            "tenants/acme/uploads/model.ifc",
        )
        s3 = S3ObjectStore(bucket="bucket", region="test", prefix="aerobim")
        self.assertEqual(
            s3._qualify_key("aerobim/tenants/acme/model.ifc"),
            "aerobim/tenants/acme/model.ifc",
        )
        self.assertEqual(
            s3._qualify_key("tenants/acme/model.ifc"),
            "aerobim/tenants/acme/model.ifc",
        )

    def test_component_limit_is_measured_in_utf8_bytes(self) -> None:
        self.assertEqual(normalize_object_key("a" * 255), "a" * 255)
        with self.assertRaisesRegex(ValueError, "component.*UTF-8 byte"):
            normalize_object_key("é" * 128)
        with self.assertRaisesRegex(ValueError, "component.*UTF-8 byte"):
            normalize_object_key("😀" * 64)

    def test_total_key_limit_is_measured_in_utf8_bytes(self) -> None:
        component = "a" * 255
        key_at_limit = "/".join([component] * 4)
        self.assertEqual(normalize_object_key(key_at_limit), key_at_limit)
        with self.assertRaisesRegex(ValueError, "key exceeds.*UTF-8 byte"):
            normalize_object_key(key_at_limit + "/b")

    def test_unpaired_surrogate_is_rejected_as_non_utf8(self) -> None:
        with self.assertRaisesRegex(ValueError, "valid UTF-8"):
            normalize_object_key("tenant/\ud800/file.ifc")


if __name__ == "__main__":
    unittest.main()
