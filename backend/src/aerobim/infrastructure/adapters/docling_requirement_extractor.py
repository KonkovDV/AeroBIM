# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

from pathlib import Path

from aerobim.domain.models import (
    ComparisonOperator,
    ParsedRequirement,
    RequirementSource,
    RuleScope,
)

_OPERATOR_ALIASES = {
    "=": ComparisonOperator.EQUALS,
    "==": ComparisonOperator.EQUALS,
    "eq": ComparisonOperator.EQUALS,
    ">=": ComparisonOperator.GREATER_OR_EQUAL,
    "gte": ComparisonOperator.GREATER_OR_EQUAL,
    "<=": ComparisonOperator.LESS_OR_EQUAL,
    "lte": ComparisonOperator.LESS_OR_EQUAL,
    "exists": ComparisonOperator.EXISTS,
}

_RULE_SCOPE_ALIASES = {
    RuleScope.IFC_PROPERTY.value: RuleScope.IFC_PROPERTY,
    RuleScope.IFC_QUANTITY.value: RuleScope.IFC_QUANTITY,
    RuleScope.DRAWING_ANNOTATION.value: RuleScope.DRAWING_ANNOTATION,
    "property": RuleScope.IFC_PROPERTY,
    "quantity": RuleScope.IFC_QUANTITY,
    "drawing": RuleScope.DRAWING_ANNOTATION,
}


class StructuredRequirementExtractor:
    def extract(self, source: RequirementSource) -> list[ParsedRequirement]:
        raw_text = source.text.strip()
        if not raw_text and source.path is not None:
            raw_text = self._load_text(source.path)

        requirements: list[ParsedRequirement] = []
        for line_number, line in enumerate(raw_text.splitlines(), start=1):
            normalized = line.strip()
            if not normalized or normalized.startswith("#"):
                continue

            parts = [part.strip() for part in normalized.split("|")]
            if self._looks_like_extended_row(parts):
                requirements.append(self._parse_extended_row(parts, source))
                continue

            if len(parts) < 5:
                raise ValueError(
                    "Malformed requirement at line "
                    f"{line_number}: expected at least 5 pipe-separated columns"
                )

            rule_id, ifc_entity, property_set, property_name, expected_value, *rest = parts
            requirements.append(
                ParsedRequirement(
                    rule_id=rule_id,
                    ifc_entity=ifc_entity.upper(),
                    rule_scope=RuleScope.IFC_PROPERTY,
                    property_set=property_set or None,
                    property_name=property_name or None,
                    operator=ComparisonOperator.EQUALS,
                    expected_value=expected_value or None,
                    source=str(source.path) if source.path else source.source_kind.value,
                    source_kind=source.source_kind,
                    evidence_text=normalized,
                    instructions=rest[0] if rest else None,
                )
            )

        return requirements

    def _looks_like_extended_row(self, parts: list[str]) -> bool:
        return len(parts) >= 8 and parts[1].strip().lower() in _RULE_SCOPE_ALIASES

    def _parse_extended_row(
        self,
        parts: list[str],
        source: RequirementSource,
    ) -> ParsedRequirement:
        if len(parts) < 8:
            raise ValueError("Extended requirement rows require at least 8 pipe-separated columns")

        (
            rule_id,
            scope_token,
            ifc_entity,
            target_ref,
            property_set,
            property_name,
            operator_token,
            expected_value,
            *rest,
        ) = parts
        unit = rest[0] if rest else None
        evidence_text = rest[1] if len(rest) > 1 else None
        instructions = rest[2] if len(rest) > 2 else None

        return ParsedRequirement(
            rule_id=rule_id,
            ifc_entity=ifc_entity.upper() or None,
            rule_scope=_RULE_SCOPE_ALIASES[scope_token.lower()],
            target_ref=target_ref or None,
            property_set=property_set or None,
            property_name=property_name or None,
            operator=self._normalize_operator(operator_token),
            expected_value=expected_value or None,
            unit=unit or None,
            source=str(source.path) if source.path else source.source_kind.value,
            source_kind=source.source_kind,
            evidence_text=evidence_text or None,
            instructions=instructions or None,
        )

    def _normalize_operator(self, token: str) -> ComparisonOperator:
        normalized = token.strip().lower()
        operator = _OPERATOR_ALIASES.get(normalized)
        if operator is None:
            raise ValueError(f"Unsupported comparison operator: {token}")
        return operator

    def _load_text(self, source_path: Path) -> str:
        if not source_path.exists():
            raise FileNotFoundError(source_path)

        if source_path.suffix.lower() in {".txt", ".md", ".csv"}:
            return source_path.read_text(encoding="utf-8")

        try:
            from docling.document_converter import DocumentConverter
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Docling is required to extract non-text requirement sources"
            ) from exc

        converter = DocumentConverter()
        result = converter.convert(str(source_path))
        return result.document.export_to_markdown()


DoclingRequirementExtractor = StructuredRequirementExtractor
