"""Constrained-decoding guard: strict JSON-schema validation of the §4 response.

The guard is a STRUCTURAL gate (fail-closed on whole-response deviation), distinct
from ``vlm_grounding`` which is tolerant per-observation (drop-not-whole). It never
touches a verdict. Tests pin the declared contract and the SSOT hash relationship.
"""

from __future__ import annotations

import unittest

from aerobim.domain.vlm_response_schema import (
    observations_response_schema_hash,
    validate_observations_response,
)


def _valid() -> dict:
    return {
        "sheet_id": "AR-01",
        "region_id": "stamp",
        "readable": True,
        "unreadable_reason": None,
        "observations": [
            {
                "kind": "dimension",
                "raw_value": "200",
                "normalized_value": None,
                "bbox_rel": [0.1, 0.1, 0.2, 0.2],
                "confidence": 0.9,
                "evidence_note": "",
            }
        ],
    }


class ObservationsSchemaGuardTests(unittest.TestCase):
    def test_valid_response_is_conformant(self) -> None:
        result = validate_observations_response(_valid())
        self.assertTrue(result.conformant, result.violations)
        self.assertEqual(result.violations, ())

    def test_minimal_required_only_is_conformant(self) -> None:
        # Only the required keys (readable + observations, and per-obs required).
        raw = {
            "readable": True,
            "observations": [
                {
                    "kind": "text",
                    "raw_value": "x",
                    "bbox_rel": [0.0, 0.0, 1.0, 1.0],
                    "confidence": 0.5,
                }
            ],
        }
        self.assertTrue(validate_observations_response(raw).conformant)

    def test_not_an_object_fails_closed(self) -> None:
        result = validate_observations_response("not-an-object")
        self.assertFalse(result.conformant)
        self.assertTrue(any("expected type" in v for v in result.violations))

    def test_missing_required_top_level(self) -> None:
        result = validate_observations_response({"observations": []})
        self.assertFalse(result.conformant)
        self.assertTrue(any("missing required 'readable'" in v for v in result.violations))

    def test_observations_must_be_array(self) -> None:
        result = validate_observations_response({"readable": True, "observations": "x"})
        self.assertFalse(result.conformant)
        self.assertTrue(any("observations: expected type" in v for v in result.violations))

    def test_additional_top_level_property_rejected(self) -> None:
        # A smuggled authority key is a schema violation (complements grounding's
        # control_fields_ignored observability).
        raw = _valid()
        raw["verdict"] = "PASS"
        result = validate_observations_response(raw)
        self.assertFalse(result.conformant)
        self.assertTrue(any("additional property 'verdict'" in v for v in result.violations))

    def test_observation_missing_required(self) -> None:
        raw = _valid()
        del raw["observations"][0]["confidence"]
        result = validate_observations_response(raw)
        self.assertFalse(result.conformant)
        self.assertTrue(
            any("observations[0]: missing required 'confidence'" in v for v in result.violations)
        )

    def test_observation_bad_kind_enum(self) -> None:
        raw = _valid()
        raw["observations"][0]["kind"] = "counting"
        result = validate_observations_response(raw)
        self.assertFalse(result.conformant)
        self.assertTrue(any("not in enum" in v for v in result.violations))

    def test_bbox_wrong_arity(self) -> None:
        raw = _valid()
        raw["observations"][0]["bbox_rel"] = [0.1, 0.1, 0.2]  # 3, needs 4
        result = validate_observations_response(raw)
        self.assertFalse(result.conformant)
        self.assertTrue(any("minItems 4" in v for v in result.violations))

    def test_observation_additional_property_rejected(self) -> None:
        raw = _valid()
        raw["observations"][0]["passed"] = True
        result = validate_observations_response(raw)
        self.assertFalse(result.conformant)
        self.assertTrue(any("additional property 'passed'" in v for v in result.violations))

    def test_bool_is_not_a_number(self) -> None:
        raw = _valid()
        raw["observations"][0]["confidence"] = True  # bool must not pass as number
        result = validate_observations_response(raw)
        self.assertFalse(result.conformant)
        self.assertTrue(any("confidence: expected type" in v for v in result.violations))

    def test_null_unreadable_reason_allowed_by_union(self) -> None:
        raw = _valid()
        raw["unreadable_reason"] = None
        self.assertTrue(validate_observations_response(raw).conformant)
        raw["unreadable_reason"] = "cropped"
        self.assertTrue(validate_observations_response(raw).conformant)

    def test_schema_hash_matches_client_ssot(self) -> None:
        # The infrastructure client must re-bind the SAME domain schema (single
        # source of truth) — hashes must be identical.
        from aerobim.infrastructure.adapters.vlm_advisory_client import (
            observations_schema_hash,
        )

        self.assertEqual(observations_response_schema_hash(), observations_schema_hash())


if __name__ == "__main__":
    unittest.main()
