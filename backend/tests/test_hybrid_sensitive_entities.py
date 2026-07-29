"""Hybrid AI P2: local sensitive-entity detection + fail-closed mask-rule derivation.

Проверяет целевой шаг «локальное обнаружение чувствительных сущностей»: детект видов,
SECRET -> remove (не отправляется даже токенизированным), известная сущность ->
tokenize, чистый скаляр -> remove по умолчанию (fail-closed), не-скаляр -> remove,
и round-trip с PrivacyGuard без утечки сырых значений. Детектор не хранит сырые данные.
"""

from __future__ import annotations

import json
import unittest

from aerobim.domain.hybrid import (
    EntityKind,
    PrivacyGuard,
    detect_entities,
    scan_payload,
    suggest_mask_rules,
)

_GID = "3n8vP2aQ9zXcVbNmLkJhG0"  # 22 base64-ish chars (IfcGloballyUniqueId shape)
_SECRET = "sk-abcdef0123456789xyz"


class SensitiveEntityDetectorTests(unittest.TestCase):
    def test_detect_common_kinds(self) -> None:
        self.assertIn(EntityKind.SECRET, detect_entities(_SECRET))
        self.assertIn(EntityKind.EMAIL, detect_entities("expert@example.com"))
        self.assertIn(EntityKind.IP, detect_entities("10.0.0.5"))
        self.assertIn(EntityKind.GLOBAL_ID, detect_entities(_GID))
        self.assertIn(EntityKind.COORDINATE, detect_entities("123.45678"))
        self.assertIn(EntityKind.FILE_PATH, detect_entities(r"C:\customer\proj\rev3.ifc"))

    def test_empty_text_has_no_entities(self) -> None:
        self.assertEqual(detect_entities(""), ())
        self.assertEqual(detect_entities("check wall thickness"), ())

    def test_secret_field_is_removed_not_tokenized(self) -> None:
        rules = suggest_mask_rules({"api_key": _SECRET})
        self.assertEqual(rules["api_key"], "remove")  # секрет никогда не выпускаем

    def test_known_entity_field_is_tokenized(self) -> None:
        rules = suggest_mask_rules({"gid": _GID})
        self.assertEqual(rules["gid"], "tokenize:global_id")

    def test_clean_scalar_failclosed_by_default_but_keepable(self) -> None:
        payload = {"question": "check wall thickness"}
        self.assertEqual(suggest_mask_rules(payload)["question"], "remove")
        self.assertEqual(suggest_mask_rules(payload, keep_clean_scalars=True)["question"], "keep")

    def test_non_scalar_is_removed(self) -> None:
        rules = suggest_mask_rules({"meta": {"nested": "x"}, "items": [1, 2]})
        self.assertEqual(rules["meta"], "remove")
        self.assertEqual(rules["items"], "remove")

    def test_detector_does_not_store_raw_values(self) -> None:
        findings = scan_payload({"api_key": _SECRET, "gid": _GID})
        # Находки содержат только вид+поле, не сырое значение.
        self.assertNotIn(_SECRET, repr(findings))
        self.assertNotIn(_GID, repr(findings))
        self.assertTrue(any(f.field == "api_key" for f in findings))

    def test_round_trip_with_privacy_guard_has_no_raw_leak(self) -> None:
        payload = {
            "question": "check wall thickness",
            "gid": _GID,
            "api_key": _SECRET,
            "coord": "123.45678",
        }
        rules = suggest_mask_rules(payload, keep_clean_scalars=True)
        guard = PrivacyGuard(tenant_salt="deploy-salt")
        masked = guard.mask_payload(payload, tenant_id="tenant-a", rules=rules).masked
        blob = json.dumps(masked)
        self.assertNotIn(_GID, blob)  # tokenized
        self.assertNotIn(_SECRET, blob)  # removed
        self.assertNotIn("123.45678", blob)  # tokenized
        self.assertEqual(masked["question"], "check wall thickness")  # utility kept


if __name__ == "__main__":
    unittest.main()
