"""Strict JSON loader for customer-approved or explicitly non-approved rule packs."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from aerobim.domain.models import (
    ComparisonOperator,
    NormRulePack,
    ParsedRequirement,
    RulePackStatus,
    RuleScope,
    SourceKind,
)
from aerobim.domain.quantity import parse_quantity

_MAX_PACK_BYTES = 2 * 1024 * 1024
_MAX_RULES = 500
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

_OPERATOR_ALIASES = {
    "eq": ComparisonOperator.EQUALS,
    "=": ComparisonOperator.EQUALS,
    "equals": ComparisonOperator.EQUALS,
    "gte": ComparisonOperator.GREATER_OR_EQUAL,
    ">=": ComparisonOperator.GREATER_OR_EQUAL,
    "lte": ComparisonOperator.LESS_OR_EQUAL,
    "<=": ComparisonOperator.LESS_OR_EQUAL,
    "exists": ComparisonOperator.EXISTS,
}
_SCOPE_ALIASES = {
    "ifc-property": RuleScope.IFC_PROPERTY,
    "ifc-quantity": RuleScope.IFC_QUANTITY,
    "drawing-annotation": RuleScope.DRAWING_ANNOTATION,
}


class JsonNormRulePackLoader:
    """Load a bounded, versioned JSON pack without granting it approval implicitly."""

    def load(self, pack_path: Path) -> NormRulePack:
        payload_bytes = self._read_source(pack_path)
        try:
            payload = json.loads(payload_bytes.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid UTF-8 JSON rule pack: {pack_path}") from exc
        if not isinstance(payload, dict):
            raise ValueError("Norm rule pack root must be a JSON object")

        schema_version = self._required_string(payload, "schema_version")
        if schema_version != "1.0.0":
            raise ValueError(
                f"Unsupported norm rule pack schema_version {schema_version!r}; expected '1.0.0'"
            )

        pack_id = self._required_identifier(payload, "pack_id")
        version = self._required_string(payload, "version", max_length=64)
        title = self._required_string(payload, "title", max_length=256)
        typology = self._required_string(payload, "typology", max_length=128)
        status = self._parse_status(payload.get("status"))
        disciplines = self._parse_disciplines(payload.get("disciplines"))
        approval_reference = self._parse_approval(payload.get("approval"), status)
        rules = self._parse_rules(payload.get("rules"), pack_path, pack_id, version, status)

        return NormRulePack(
            pack_id=pack_id,
            version=version,
            title=title,
            typology=typology,
            disciplines=disciplines,
            status=status,
            rules=rules,
            source_path=pack_path,
            sha256=hashlib.sha256(payload_bytes).hexdigest(),
            approval_reference=approval_reference,
        )

    def _read_source(self, pack_path: Path) -> bytes:
        if pack_path.is_symlink():
            raise ValueError(f"Symlinked norm rule packs are not accepted: {pack_path}")
        if not pack_path.exists():
            raise FileNotFoundError(pack_path)
        if not pack_path.is_file():
            raise ValueError(f"Norm rule pack path is not a regular file: {pack_path}")
        if pack_path.suffix.lower() != ".json":
            raise ValueError("Norm rule packs must use the .json extension")
        size = pack_path.stat().st_size
        if size > _MAX_PACK_BYTES:
            raise ValueError(
                f"Norm rule pack exceeds {_MAX_PACK_BYTES} byte limit: {pack_path} ({size} bytes)"
            )
        return pack_path.read_bytes()

    def _parse_status(self, raw: object) -> RulePackStatus:
        try:
            return RulePackStatus(str(raw))
        except ValueError as exc:
            allowed = ", ".join(status.value for status in RulePackStatus)
            raise ValueError(f"Unsupported norm rule pack status {raw!r}; expected one of {allowed}") from exc

    def _parse_disciplines(self, raw: object) -> tuple[str, ...]:
        if not isinstance(raw, list) or not raw:
            raise ValueError("Norm rule pack disciplines must be a non-empty array")
        values: list[str] = []
        for index, value in enumerate(raw):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"disciplines[{index}] must be a non-empty string")
            normalized = value.strip().upper()
            if normalized in values:
                raise ValueError(f"Duplicate discipline in norm rule pack: {normalized}")
            values.append(normalized)
        return tuple(values)

    def _parse_approval(self, raw: object, status: RulePackStatus) -> str | None:
        if status is not RulePackStatus.APPROVED:
            if raw not in (None, {}):
                raise ValueError("Only status='approved' may carry approval metadata")
            return None
        if not isinstance(raw, dict):
            raise ValueError("Approved norm rule packs require an approval object")
        approved_by = self._required_string(raw, "approved_by", max_length=256)
        approved_at = self._required_string(raw, "approved_at", max_length=64)
        scope_reference = self._required_string(raw, "scope_reference", max_length=512)
        try:
            parsed_at = datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("approval.approved_at must be an ISO 8601 datetime") from exc
        if parsed_at.tzinfo is None:
            raise ValueError("approval.approved_at must include an explicit timezone")
        return f"{approved_by}; {approved_at}; {scope_reference}"

    def _parse_rules(
        self,
        raw: object,
        pack_path: Path,
        pack_id: str,
        version: str,
        status: RulePackStatus,
    ) -> tuple[ParsedRequirement, ...]:
        if not isinstance(raw, list) or not raw:
            raise ValueError("Norm rule pack rules must be a non-empty array")
        if len(raw) > _MAX_RULES:
            raise ValueError(f"Norm rule pack has {len(raw)} rules; maximum is {_MAX_RULES}")

        rules: list[ParsedRequirement] = []
        seen_rule_ids: set[str] = set()
        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                raise ValueError(f"rules[{index}] must be a JSON object")
            rule = self._parse_rule(
                item,
                index=index,
                pack_path=pack_path,
                pack_id=pack_id,
                version=version,
                status=status,
            )
            if rule.rule_id in seen_rule_ids:
                raise ValueError(f"Duplicate rule_id in norm rule pack: {rule.rule_id}")
            seen_rule_ids.add(rule.rule_id)
            rules.append(rule)
        return tuple(rules)

    def _parse_rule(
        self,
        payload: dict[str, Any],
        *,
        index: int,
        pack_path: Path,
        pack_id: str,
        version: str,
        status: RulePackStatus,
    ) -> ParsedRequirement:
        rule_id = self._required_identifier(payload, "rule_id", prefix=f"rules[{index}].")
        raw_scope = self._required_string(payload, "scope", prefix=f"rules[{index}].")
        scope = _SCOPE_ALIASES.get(raw_scope.lower())
        if scope is None:
            raise ValueError(f"rules[{index}].scope is unsupported: {raw_scope!r}")
        raw_operator = self._required_string(payload, "operator", prefix=f"rules[{index}].")
        operator = _OPERATOR_ALIASES.get(raw_operator.lower())
        if operator is None:
            raise ValueError(f"rules[{index}].operator is unsupported: {raw_operator!r}")

        ifc_entity = self._optional_string(payload.get("ifc_entity"), f"rules[{index}].ifc_entity")
        target_ref = self._optional_string(payload.get("target_ref"), f"rules[{index}].target_ref")
        property_set = self._optional_string(
            payload.get("property_set"), f"rules[{index}].property_set"
        )
        property_name = self._optional_string(
            payload.get("property_name"), f"rules[{index}].property_name"
        )
        unit = self._optional_string(payload.get("unit"), f"rules[{index}].unit")

        if scope in {RuleScope.IFC_PROPERTY, RuleScope.IFC_QUANTITY} and not ifc_entity:
            raise ValueError(f"rules[{index}].ifc_entity is required for {scope.value}")
        if scope is RuleScope.DRAWING_ANNOTATION and not target_ref:
            raise ValueError(f"rules[{index}].target_ref is required for drawing-annotation")
        if not property_name:
            raise ValueError(f"rules[{index}].property_name is required")

        expected_raw = payload.get("expected_value")
        if operator is ComparisonOperator.EXISTS:
            expected_value = None if expected_raw is None else self._scalar_string(expected_raw)
        else:
            if expected_raw is None:
                raise ValueError(
                    f"rules[{index}].expected_value is required for operator {operator.value}"
                )
            expected_value = self._scalar_string(expected_raw)

        quantity = None
        if expected_value is not None and unit is not None:
            try:
                quantity = parse_quantity(float(expected_value.replace(",", ".")), unit)
            except ValueError:
                quantity = None

        evidence_text = self._optional_string(
            payload.get("evidence_text"), f"rules[{index}].evidence_text", max_length=2000
        )
        instructions = self._optional_string(
            payload.get("instructions"), f"rules[{index}].instructions", max_length=2000
        )
        source = f"{pack_path}#{pack_id}@{version}[{status.value}]"
        return ParsedRequirement(
            rule_id=rule_id,
            ifc_entity=ifc_entity.upper() if ifc_entity else None,
            rule_scope=scope,
            target_ref=target_ref,
            property_set=property_set,
            property_name=property_name,
            operator=operator,
            expected_value=expected_value,
            unit=unit,
            source=source,
            source_kind=SourceKind.STRUCTURED_TEXT,
            evidence_text=evidence_text or source,
            instructions=instructions,
            evidence_modality="norm-rule-pack",
            confidence=1.0,
            quantity=quantity,
        )

    def _required_identifier(
        self,
        payload: dict[str, Any],
        key: str,
        *,
        prefix: str = "",
    ) -> str:
        value = self._required_string(payload, key, prefix=prefix, max_length=128)
        if not _ID_RE.fullmatch(value):
            raise ValueError(f"{prefix}{key} contains unsupported characters: {value!r}")
        return value

    def _required_string(
        self,
        payload: dict[str, Any],
        key: str,
        *,
        prefix: str = "",
        max_length: int = 256,
    ) -> str:
        value = payload.get(key)
        parsed = self._optional_string(value, f"{prefix}{key}", max_length=max_length)
        if parsed is None:
            raise ValueError(f"{prefix}{key} must be a non-empty string")
        return parsed

    def _optional_string(
        self,
        value: object,
        field: str,
        *,
        max_length: int = 512,
    ) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string when provided")
        normalized = value.strip()
        if len(normalized) > max_length:
            raise ValueError(f"{field} exceeds {max_length} characters")
        return normalized

    def _scalar_string(self, value: object) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (str, int, float)) and not isinstance(value, complex):
            return str(value).strip()
        raise ValueError("expected_value must be a string, number, boolean, or null")
