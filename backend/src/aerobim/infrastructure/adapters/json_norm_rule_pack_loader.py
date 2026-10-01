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
    approval_status_from_pack,
)
from aerobim.domain.norm_pack_hash import compute_norm_pack_content_hash
from aerobim.domain.norm_rule_eligibility import (
    parse_expert_confirmation_journal,
    parse_rase_roles,
)
from aerobim.domain.quantity import parse_quantity

# Re-export for tests / callers that historically imported from the loader.
__all__ = ["JsonNormRulePackLoader", "compute_norm_pack_content_hash"]

_MAX_PACK_BYTES = 2 * 1024 * 1024
_MAX_RULES = 500
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_HEX64_RE = re.compile(r"^[a-fA-F0-9]{64}$")
_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0.0", "2.0.0"})
_SYNTHETIC_CLAIM_LABELS = frozenset({"synthetic", "fixture", "template", "not-customer-evidence"})
_STATUS_ALIASES = {
    "synthetic-template": RulePackStatus.SYNTHETIC_TEMPLATE,
    "synthetic": RulePackStatus.SYNTHETIC_TEMPLATE,
    "draft": RulePackStatus.DRAFT,
    "approved": RulePackStatus.APPROVED,
    "customer_approved": RulePackStatus.APPROVED,
    "retired": RulePackStatus.RETIRED,
    "expired": RulePackStatus.EXPIRED,
    "inapplicable": RulePackStatus.INAPPLICABLE,
    "expert_required": RulePackStatus.EXPERT_REQUIRED,
    "expert-required": RulePackStatus.EXPERT_REQUIRED,
}

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
_CRITICALITY_VALUES = frozenset({"critical", "warning", "info"})


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
        if schema_version not in _SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError(
                f"Unsupported norm rule pack schema_version {schema_version!r}; "
                f"expected one of {sorted(_SUPPORTED_SCHEMA_VERSIONS)}"
            )
        is_v2 = schema_version.startswith("2.")

        pack_id = self._required_identifier(payload, "pack_id")
        version = self._required_string(payload, "version", max_length=64)
        title = self._required_string(payload, "title", max_length=256)
        typology = self._required_string(payload, "typology", max_length=128)
        status = self._parse_status(payload.get("status"))
        disciplines = self._parse_disciplines(payload.get("disciplines"))
        claim_labels = self._parse_claim_labels(payload.get("claim_labels"), status)
        jurisdiction = self._optional_string(
            payload.get("jurisdiction"), "jurisdiction", max_length=128
        )
        norm_edition = self._optional_string(
            payload.get("norm_edition") or payload.get("edition"),
            "norm_edition",
            max_length=128,
        )
        norm_edition_date = self._optional_string(
            payload.get("norm_edition_date"), "norm_edition_date", max_length=64
        )
        if is_v2:
            if not norm_edition:
                raise ValueError("schema 2.0.0 packs require non-empty norm_edition")
            if not norm_edition_date:
                raise ValueError("schema 2.0.0 packs require non-empty norm_edition_date")

        content_hash = compute_norm_pack_content_hash(payload)
        declared_hash = self._parse_declared_hash(payload)
        if declared_hash is not None and declared_hash.lower() != content_hash.lower():
            raise ValueError(
                "pack_hash/source_hash mismatch vs recomputed content hash — "
                "sign-off blocked (immutable pack integrity)"
            )

        approval_meta = self._parse_approval(payload.get("approval"), status, payload)
        pack_approval_status = approval_status_from_pack(status)
        # Only customer_approved/approved packs are sign-off capable.
        advisory_only = status is not RulePackStatus.APPROVED
        if advisory_only and pack_approval_status == "customer_approved":
            raise ValueError("draft/synthetic packs cannot stamp customer_approved approval_status")
        if pack_approval_status == "customer_approved" and not approval_meta["approval_ref"]:
            raise ValueError(
                "customer_approved norm rule packs require a non-empty approval_ref "
                "(approval.scope_reference, pack-level approval_ref, or customer_approval_ref)"
            )
        if status is RulePackStatus.APPROVED:
            if not jurisdiction:
                raise ValueError("approved/customer_approved packs require non-empty jurisdiction")
            if not declared_hash:
                raise ValueError(
                    "approved/customer_approved packs require pack_hash or source_hash"
                )
            for index, rule in enumerate(payload.get("rules") or []):
                if not isinstance(rule, dict):
                    continue
                clause = rule.get("clause_number") or rule.get("norm_clause") or rule.get("clause")
                if not (isinstance(clause, str) and clause.strip()):
                    raise ValueError(
                        f"rules[{index}] must include clause_number/norm_clause/clause "
                        "when pack is approved"
                    )

        rules = self._parse_rules(
            payload.get("rules"),
            pack_path,
            pack_id,
            version,
            status,
            schema_version=schema_version,
            approval_reference=approval_meta["approval_ref"],
            approval_status=pack_approval_status,
        )

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
            approval_reference=approval_meta["approval_ref"],
            jurisdiction=jurisdiction,
            claim_labels=claim_labels,
            pack_hash=(
                (declared_hash or content_hash)
                if status is RulePackStatus.APPROVED
                else declared_hash
            ),
            document_title=approval_meta["document_title"],
            document_edition=approval_meta["document_edition"],
            effective_date=approval_meta["effective_date"],
            approval_date=approval_meta["approval_date"],
            advisory_only=advisory_only,
            schema_version=schema_version,
            norm_edition=norm_edition,
            norm_edition_date=norm_edition_date,
            customer_approval_ref=approval_meta["approval_ref"],
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
        key = str(raw).strip().lower().replace("_", "-") if raw is not None else ""
        aliases = {
            **{k.replace("_", "-"): v for k, v in _STATUS_ALIASES.items()},
            "customer-approved": RulePackStatus.APPROVED,
            "expert-required": RulePackStatus.EXPERT_REQUIRED,
        }
        # Also accept underscore forms via original map.
        raw_key = str(raw).strip().lower() if raw is not None else ""
        if raw_key in _STATUS_ALIASES:
            return _STATUS_ALIASES[raw_key]
        if key in aliases:
            return aliases[key]
        try:
            return RulePackStatus(str(raw))
        except ValueError as exc:
            allowed = ", ".join(sorted({*RulePackStatus._value2member_map_, *_STATUS_ALIASES}))
            raise ValueError(
                f"Unsupported norm rule pack status {raw!r}; expected one of {allowed}"
            ) from exc

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

    def _parse_claim_labels(self, raw: object, status: RulePackStatus) -> tuple[str, ...]:
        if raw is None:
            labels: tuple[str, ...] = ()
        elif not isinstance(raw, list):
            raise ValueError("claim_labels must be an array when provided")
        else:
            values: list[str] = []
            for index, value in enumerate(raw):
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"claim_labels[{index}] must be a non-empty string")
                label = value.strip().lower()
                if label in values:
                    raise ValueError(f"Duplicate claim_labels entry: {label}")
                values.append(label)
            labels = tuple(values)

        synthetic_marked = bool(_SYNTHETIC_CLAIM_LABELS.intersection(labels))
        if synthetic_marked and status is RulePackStatus.APPROVED:
            raise ValueError(
                "synthetic/fixture claim_labels cannot claim customer_approved/approved "
                "(RT-002 remains open until signed customer pack)"
            )
        if status in {
            RulePackStatus.SYNTHETIC_TEMPLATE,
            RulePackStatus.DRAFT,
            RulePackStatus.EXPIRED,
            RulePackStatus.INAPPLICABLE,
            RulePackStatus.EXPERT_REQUIRED,
            RulePackStatus.RETIRED,
        }:
            if not labels:
                return ("synthetic", "not-customer-evidence")
            if not synthetic_marked and "draft" not in labels:
                raise ValueError(
                    "draft/synthetic/non-approved packs must include synthetic, fixture, "
                    "template, not-customer-evidence, or draft in claim_labels"
                )
        return labels

    def _parse_declared_hash(self, payload: dict[str, Any]) -> str | None:
        pack_hash = self._optional_string(payload.get("pack_hash"), "pack_hash", max_length=64)
        source_hash = self._optional_string(
            payload.get("source_hash"), "source_hash", max_length=64
        )
        for field, value in (("pack_hash", pack_hash), ("source_hash", source_hash)):
            if value is not None and not _HEX64_RE.fullmatch(value):
                raise ValueError(f"{field} must be a 64-char hex SHA-256 digest")
        if pack_hash and source_hash and pack_hash.lower() != source_hash.lower():
            raise ValueError("pack_hash and source_hash disagree")
        return pack_hash or source_hash

    def _parse_approval(
        self,
        raw: object,
        status: RulePackStatus,
        payload: dict[str, Any],
    ) -> dict[str, str | None]:
        pack_level_ref = self._optional_string(
            payload.get("approval_ref") or payload.get("customer_approval_ref"),
            "approval_ref",
            max_length=512,
        )
        empty: dict[str, str | None] = {
            "approval_ref": None,
            "document_title": None,
            "document_edition": None,
            "effective_date": None,
            "approval_date": None,
        }
        if status is not RulePackStatus.APPROVED:
            if raw not in (None, {}):
                raise ValueError(
                    "Only status='approved'/'customer_approved' may carry approval metadata"
                )
            if pack_level_ref:
                raise ValueError(
                    "approval_ref/customer_approval_ref is only valid for customer_approved packs"
                )
            return empty
        # Reject approval-by-string-ref-only: full approval object is mandatory.
        if pack_level_ref and raw in (None, {}):
            raise ValueError(
                "approval_ref alone is not sufficient; approved packs require a full "
                "approval object (approved_by, approval_date, approval_status, "
                "document_title, document_edition, effective_date, scope_reference)"
            )
        if not isinstance(raw, dict):
            raise ValueError("Approved norm rule packs require an approval object")
        approved_by = self._required_string(raw, "approved_by", max_length=256)
        approval_date = self._optional_string(
            raw.get("approval_date"), "approval.approval_date", max_length=64
        ) or self._optional_string(raw.get("approved_at"), "approval.approved_at", max_length=64)
        if not approval_date:
            raise ValueError("approval.approval_date (or approved_at) is required")
        approval_status = self._required_string(raw, "approval_status", max_length=64)
        if approval_status not in {"approved", "customer_approved"}:
            raise ValueError("approval.approval_status must be 'approved' or 'customer_approved'")
        document_title = self._required_string(raw, "document_title", max_length=512)
        document_edition = self._required_string(raw, "document_edition", max_length=128)
        effective_date = self._required_string(raw, "effective_date", max_length=64)
        scope_reference = self._required_string(raw, "scope_reference", max_length=512)
        try:
            parsed_at = datetime.fromisoformat(approval_date.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("approval.approval_date must be an ISO 8601 datetime") from exc
        if parsed_at.tzinfo is None:
            raise ValueError("approval.approval_date must include an explicit timezone")
        approval_ref = pack_level_ref or scope_reference
        if not approval_ref or not str(approval_ref).strip():
            raise ValueError(
                "customer_approved packs require approval_ref "
                "(pack-level approval_ref/customer_approval_ref or approval.scope_reference)"
            )
        # Bind identity into the composite reference for audit trails.
        _ = (approved_by, document_title, document_edition, effective_date)
        return {
            "approval_ref": f"{approved_by}; {approval_date}; {approval_ref}",
            "document_title": document_title,
            "document_edition": document_edition,
            "effective_date": effective_date,
            "approval_date": approval_date,
        }

    def _parse_rules(
        self,
        raw: object,
        pack_path: Path,
        pack_id: str,
        version: str,
        status: RulePackStatus,
        *,
        schema_version: str,
        approval_reference: str | None,
        approval_status: str,
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
                schema_version=schema_version,
                approval_reference=approval_reference,
                approval_status=approval_status,
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
        schema_version: str,
        approval_reference: str | None,
        approval_status: str,
    ) -> ParsedRequirement:
        is_v2 = schema_version.startswith("2.")
        prefix = f"rules[{index}]."
        rule_id = self._required_identifier(payload, "rule_id", prefix=prefix)
        raw_scope = self._required_string(payload, "scope", prefix=prefix)
        scope = _SCOPE_ALIASES.get(raw_scope.lower())
        if scope is None:
            raise ValueError(f"{prefix}scope is unsupported: {raw_scope!r}")
        raw_operator = self._required_string(payload, "operator", prefix=prefix)
        operator = _OPERATOR_ALIASES.get(raw_operator.lower())
        if operator is None:
            raise ValueError(f"{prefix}operator is unsupported: {raw_operator!r}")

        ifc_entity = self._optional_string(payload.get("ifc_entity"), f"{prefix}ifc_entity")
        object_type = self._optional_string(payload.get("object_type"), f"{prefix}object_type")
        if object_type and not ifc_entity:
            ifc_entity = object_type
        if ifc_entity and not object_type:
            object_type = ifc_entity
        target_ref = self._optional_string(payload.get("target_ref"), f"{prefix}target_ref")
        property_set = self._optional_string(payload.get("property_set"), f"{prefix}property_set")
        property_name = self._optional_string(
            payload.get("property_name"), f"{prefix}property_name"
        )
        unit = self._optional_string(payload.get("unit"), f"{prefix}unit")
        norm_source = self._optional_string(
            payload.get("source") or payload.get("norm_source"),
            f"{prefix}source",
            max_length=256,
        )
        norm_edition = self._optional_string(
            payload.get("norm_edition"), f"{prefix}norm_edition", max_length=128
        )
        norm_clause = self._optional_string(
            payload.get("clause_number") or payload.get("norm_clause") or payload.get("clause"),
            f"{prefix}clause_number",
            max_length=128,
        )
        rule_approval_ref = self._optional_string(
            payload.get("customer_approval_ref") or payload.get("approval_ref"),
            f"{prefix}approval_ref",
            max_length=512,
        )
        discipline = self._optional_string(payload.get("discipline"), f"{prefix}discipline")
        stage = self._optional_string(payload.get("stage"), f"{prefix}stage")
        criticality = self._optional_string(
            payload.get("criticality") or payload.get("severity"),
            f"{prefix}criticality",
            max_length=32,
        )
        if criticality is not None and criticality not in _CRITICALITY_VALUES:
            raise ValueError(f"{prefix}criticality must be one of {sorted(_CRITICALITY_VALUES)}")

        evidence_required_raw = payload.get("evidence_required")
        evidence_required: bool | None
        if evidence_required_raw is None:
            evidence_required = None
        elif isinstance(evidence_required_raw, bool):
            evidence_required = evidence_required_raw
        else:
            raise ValueError(f"{prefix}evidence_required must be a boolean when provided")

        execution_mode_raw = self._optional_string(
            payload.get("execution_mode"), f"{prefix}execution_mode", max_length=32
        )
        execution_mode: str | None
        if execution_mode_raw is None:
            execution_mode = None
        elif execution_mode_raw in {"deterministic", "expert_required"}:
            execution_mode = execution_mode_raw
        else:
            raise ValueError(f"{prefix}execution_mode must be deterministic|expert_required")

        journal = parse_expert_confirmation_journal(
            payload.get("expert_confirmation_journal"),
            field=f"{prefix}expert_confirmation_journal",
        )
        rase = parse_rase_roles(
            payload.get("rase"),
            field=f"{prefix}rase",
            required=is_v2,
        )

        requirement_text = self._optional_string(
            payload.get("requirement_text"),
            f"{prefix}requirement_text",
            max_length=4000,
        )
        if requirement_text is None and rase is not None:
            requirement_text = rase.requirement

        if is_v2:
            if not requirement_text:
                raise ValueError(f"{prefix}requirement_text is required for schema 2.0.0")
            if not object_type:
                raise ValueError(f"{prefix}object_type is required for schema 2.0.0")
            if not discipline:
                raise ValueError(f"{prefix}discipline is required for schema 2.0.0")
            if not stage:
                raise ValueError(f"{prefix}stage is required for schema 2.0.0")
            if not criticality:
                raise ValueError(f"{prefix}criticality is required for schema 2.0.0")
            if evidence_required is None:
                raise ValueError(f"{prefix}evidence_required is required for schema 2.0.0")
            if execution_mode is None:
                raise ValueError(f"{prefix}execution_mode is required for schema 2.0.0")
            if not norm_source:
                raise ValueError(f"{prefix}source/norm_source is required for schema 2.0.0")
            if not norm_clause:
                raise ValueError(f"{prefix}clause_number is required for schema 2.0.0")
            if "expert_confirmation_journal" not in payload:
                raise ValueError(
                    f"{prefix}expert_confirmation_journal is required for schema 2.0.0 "
                    "(may be an empty array until an expert confirms)"
                )

        if scope in {RuleScope.IFC_PROPERTY, RuleScope.IFC_QUANTITY} and not ifc_entity:
            raise ValueError(f"{prefix}ifc_entity/object_type is required for {scope.value}")
        if scope is RuleScope.DRAWING_ANNOTATION and not target_ref:
            raise ValueError(
                f"{prefix}target_ref is required for drawing-annotation "
                "(use ALL to match any annotation of the measure)"
            )
        if not property_name:
            raise ValueError(f"{prefix}property_name is required")

        expected_raw = payload.get("expected_value")
        if operator is ComparisonOperator.EXISTS:
            expected_value = None if expected_raw is None else self._scalar_string(expected_raw)
        else:
            if expected_raw is None:
                raise ValueError(
                    f"{prefix}expected_value is required for operator {operator.value}"
                )
            expected_value = self._scalar_string(expected_raw)

        quantity = None
        if expected_value is not None and unit is not None:
            try:
                quantity = parse_quantity(float(expected_value.replace(",", ".")), unit)
            except ValueError:
                quantity = None

        evidence_text = self._optional_string(
            payload.get("evidence_text"), f"{prefix}evidence_text", max_length=2000
        )
        if evidence_text is None:
            evidence_text = requirement_text
        instructions = self._optional_string(
            payload.get("instructions"), f"{prefix}instructions", max_length=2000
        )
        # Pack manifest is the authority for approval_status; default synthetic.
        stamped_status = approval_status or "synthetic"
        if status is not RulePackStatus.APPROVED and stamped_status == "customer_approved":
            raise ValueError(f"{prefix}cannot claim customer_approved under draft/synthetic pack")
        stamped_ref = rule_approval_ref or approval_reference
        if stamped_status == "customer_approved" and not stamped_ref:
            raise ValueError(
                f"{prefix}customer_approved requires approval_ref "
                "(rule-level or pack approval metadata)"
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
            norm_source=norm_source,
            norm_edition=norm_edition,
            norm_clause=norm_clause,
            approval_status=stamped_status,  # type: ignore[arg-type]
            approval_ref=stamped_ref,
            requirement_text=requirement_text,
            object_type=object_type.upper() if object_type else None,
            discipline=discipline.upper() if discipline else None,
            stage=stage,
            criticality=criticality,
            evidence_required=evidence_required,
            execution_mode=execution_mode,  # type: ignore[arg-type]
            expert_confirmation_journal=journal,
            rase=rase,
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
        if isinstance(value, str | int | float) and not isinstance(value, complex):
            return str(value).strip()
        raise ValueError("expected_value must be a string, number, boolean, or null")
