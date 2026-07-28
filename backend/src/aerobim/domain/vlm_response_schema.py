"""Declared JSON Schema + fail-closed validator for the §4 VLM observations response.

Constrained-decoding posture (arXiv:2606.09395; OpenAI/Kimi structured outputs,
2025): the advisory VLM contract is a **strict** JSON Schema. The kimi-k3 tier is
constrained at decode time via ``response_format`` (``strict: True``); tiers that
cannot be constrained (self-hosted vLLM ``json_object``) still need a **post-hoc,
fail-closed** structural gate. This module is the single source of truth for that
schema plus a dependency-free validator, so the contract is explicit and testable.

Separation of concerns (do not confuse with ``vlm_grounding``):
- THIS guard = strict STRUCTURAL conformance of the whole response (a gate).
- ``ground_vlm_region_observations`` = tolerant, per-observation VALUE processing
  that drops (not fail-whole) individual bad entries and recomputes normalized
  values deterministically. The guard never widens what grounding accepts and,
  like everything in the advisory contour, never touches ``summary.passed``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aerobim.domain.vlm_cache import content_sha256

# §4 rich region-observation schema (strict). ``normalized_value`` may be echoed
# by the model but grounding IGNORES it (we recompute deterministically). This is
# the canonical declaration; infrastructure re-binds it for ``response_format``.
OBSERVATIONS_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "sheet_id": {"type": "string"},
        "region_id": {"type": "string"},
        "readable": {"type": "boolean"},
        "unreadable_reason": {"type": ["string", "null"]},
        "observations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": [
                            "text",
                            "dimension",
                            "designation",
                            "table_row",
                            "stamp_field",
                        ],
                    },
                    "raw_value": {"type": "string"},
                    "normalized_value": {"type": ["string", "null"]},
                    "bbox_rel": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "confidence": {"type": "number"},
                    "evidence_note": {"type": "string"},
                },
                "required": ["kind", "raw_value", "bbox_rel", "confidence"],
            },
        },
    },
    "required": ["readable", "observations"],
}


def observations_response_schema_hash() -> str:
    """Stable hash of the declared observations schema (cache/act provenance)."""
    return content_sha256(OBSERVATIONS_RESPONSE_SCHEMA)


@dataclass(frozen=True)
class SchemaValidation:
    """Outcome of validating a response against the declared schema."""

    conformant: bool
    violations: tuple[str, ...] = ()


def _type_ok(value: object, type_name: str) -> bool:
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "number":
        # JSON number excludes bool (bool is an int subclass in Python).
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "null":
        return value is None
    return False


def _validate(value: object, schema: dict[str, Any], path: str, out: list[str]) -> None:
    """Append a violation string for each deviation (bounded JSON Schema subset)."""
    declared = schema.get("type")
    if declared is not None:
        names = declared if isinstance(declared, list) else [declared]
        if not any(_type_ok(value, name) for name in names):
            out.append(f"{path}: expected type {declared}, got {type(value).__name__}")
            return  # cannot descend into a value of the wrong shape
    enum = schema.get("enum")
    if enum is not None and value not in enum:
        out.append(f"{path}: {value!r} not in enum {enum}")
    if isinstance(value, dict):
        props: dict[str, Any] = schema.get("properties", {})
        for required in schema.get("required", []):
            if required not in value:
                out.append(f"{path}: missing required '{required}'")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    out.append(f"{path}: additional property '{key}' not allowed")
        for key, subschema in props.items():
            if key in value:
                _validate(value[key], subschema, f"{path}.{key}", out)
    elif isinstance(value, list):
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")
        if min_items is not None and len(value) < min_items:
            out.append(f"{path}: array shorter than minItems {min_items}")
        if max_items is not None and len(value) > max_items:
            out.append(f"{path}: array longer than maxItems {max_items}")
        items = schema.get("items")
        if isinstance(items, dict):
            for index, item in enumerate(value):
                _validate(item, items, f"{path}[{index}]", out)


def validate_observations_response(raw: object) -> SchemaValidation:
    """Fail-closed structural validation against ``OBSERVATIONS_RESPONSE_SCHEMA``.

    Returns every violation (not just the first) with a JSON path, so callers can
    log a faithful reason. Conformant means the whole response matches the strict
    contract; it does NOT assert per-value semantics (bbox range, kind allow-list,
    calibrated confidence) — those stay in ``vlm_grounding`` (drop-not-whole).
    """
    violations: list[str] = []
    _validate(raw, OBSERVATIONS_RESPONSE_SCHEMA, "$", violations)
    return SchemaValidation(conformant=not violations, violations=tuple(violations))


__all__ = [
    "OBSERVATIONS_RESPONSE_SCHEMA",
    "SchemaValidation",
    "observations_response_schema_hash",
    "validate_observations_response",
]
