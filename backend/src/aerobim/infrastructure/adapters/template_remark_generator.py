from __future__ import annotations

from aerobim.domain.models import (
    ComparisonOperator,
    FindingCategory,
    GeneratedRemark,
    ValidationIssue,
)


class TemplateRemarkGenerator:
    """Deterministic remark templates for RU/EN product locales (TZ P0).

    Samolet answer 2.1.5 (2026-08-25): essence (one sentence) + bound norm/STO
    clause (never invented) + location detail (axis / storey / sheet / element).
    """

    def __init__(self, *, locale: str = "ru") -> None:
        normalized = (locale or "ru").strip().lower()
        self._locale = "en" if normalized.startswith("en") else "ru"

    def generate(self, issue: ValidationIssue) -> GeneratedRemark:
        if self._locale == "en":
            return self._generate_en(issue)
        return self._generate_ru(issue)

    def _generate_ru(self, issue: ValidationIssue) -> GeneratedRemark:
        essence = self._build_essence_ru(issue)
        priority_hint = f" [приоритет {issue.priority}]" if issue.priority else ""
        title = f"{self._category_marker_ru(issue)}: {essence}{priority_hint}"
        body = self._compose_body_ru(issue, essence=essence)
        return GeneratedRemark(title=title, body=body)

    def _generate_en(self, issue: ValidationIssue) -> GeneratedRemark:
        essence = self._build_essence_en(issue)
        priority_hint = f" [priority {issue.priority}]" if issue.priority else ""
        title = f"{self._category_marker_en(issue)}: {essence}{priority_hint}"
        body = self._compose_body_en(issue, essence=essence)
        return GeneratedRemark(title=title, body=body)

    def _category_marker_ru(self, issue: ValidationIssue) -> str:
        if issue.category is FindingCategory.CROSS_DOCUMENT:
            return "Междокументное расхождение"
        if issue.category is FindingCategory.DRAWING_VALIDATION:
            return "Замечание по чертежу"
        if issue.category is FindingCategory.SPATIAL:
            return "Пространственное замечание"
        return "Замечание по модели"

    def _category_marker_en(self, issue: ValidationIssue) -> str:
        if issue.category is FindingCategory.CROSS_DOCUMENT:
            return "Cross-document conflict"
        if issue.category is FindingCategory.DRAWING_VALIDATION:
            return "Drawing remark"
        if issue.category is FindingCategory.SPATIAL:
            return "Spatial remark"
        return "Model remark"

    def _first_sentence(self, text: str) -> str:
        stripped = text.strip()
        if not stripped:
            return ""
        head, sep, _rest = stripped.partition(". ")
        if sep:
            return head.rstrip(".")
        return stripped.rstrip(".")

    def _build_essence_ru(self, issue: ValidationIssue) -> str:
        message = self._first_sentence(issue.message or "")
        if message:
            return message
        if issue.category is FindingCategory.CROSS_DOCUMENT:
            return "Обнаружено противоречие между источниками"
        if issue.category is FindingCategory.SPATIAL:
            return "Обнаружен пространственный конфликт"
        return f"Расхождение по {self._build_field_name(issue)}"

    def _build_essence_en(self, issue: ValidationIssue) -> str:
        message = self._first_sentence(issue.message or "")
        if message:
            return message
        if issue.category is FindingCategory.CROSS_DOCUMENT:
            return "Contradiction detected between sources"
        if issue.category is FindingCategory.SPATIAL:
            return "Spatial conflict detected"
        return f"Mismatch on {self._build_field_name(issue)}"

    def _norm_line(self, issue: ValidationIssue) -> str:
        parts: list[str] = []
        if issue.norm_source and issue.norm_source.strip():
            parts.append(issue.norm_source.strip())
        if issue.norm_clause and issue.norm_clause.strip():
            parts.append(issue.norm_clause.strip())
        if parts:
            return " ".join(parts)
        if self._locale == "en":
            return "no bound clause (not invented)"
        return "пункт нормы не привязан"

    def _location_line(self, issue: ValidationIssue) -> str:
        bits: list[str] = []
        zone = issue.problem_zone
        if zone and zone.sheet_id:
            label = "sheet" if self._locale == "en" else "лист"
            bits.append(f"{label} {zone.sheet_id}")
        if issue.target_ref:
            bits.append(issue.target_ref)
        guid = issue.element_guid or (zone.element_guid if zone else None)
        if guid:
            bits.append(f"GUID {guid}")
        if bits:
            return "; ".join(bits)
        return "no precise location" if self._locale == "en" else "без точной привязки"

    def _detail_ru(self, issue: ValidationIssue) -> str:
        field_name = self._build_field_name(issue)
        expected_text = self._build_expected_text_ru(issue)
        observed_text = self._build_observed_text(issue)
        location_text = self._build_location_text(issue)

        if issue.category is FindingCategory.CROSS_DOCUMENT:
            return (
                f"{issue.message or 'Обнаружено противоречие между источниками.'} "
                f"Ожидание: {expected_text}. Факт: {observed_text}. "
                f"Привязка: {location_text}."
            )
        if issue.category is FindingCategory.DRAWING_VALIDATION:
            return (
                f"Проблемная зона на чертеже {location_text}: "
                f"показатель {field_name} имеет значение "
                f"{observed_text}, тогда как {expected_text}."
            )
        if issue.category is FindingCategory.SPATIAL:
            return (
                f"{issue.message or 'Обнаружен пространственный конфликт.'} "
                f"Привязка: {location_text}."
            )
        return (
            f"Для {issue.ifc_entity or 'элемента'} {location_text} "
            f"поле {field_name} имеет значение "
            f"{observed_text}, тогда как {expected_text}."
        )

    def _detail_en(self, issue: ValidationIssue) -> str:
        field_name = self._build_field_name(issue)
        expected_text = self._build_expected_text_en(issue)
        observed_text = self._build_observed_text(issue)
        location_text = self._build_location_text(issue)

        if issue.category is FindingCategory.CROSS_DOCUMENT:
            return (
                f"{issue.message or 'Contradiction detected between sources.'} "
                f"Expected: {expected_text}. Observed: {observed_text}. "
                f"Location: {location_text}."
            )
        if issue.category is FindingCategory.DRAWING_VALIDATION:
            return (
                f"Problem zone on drawing {location_text}: "
                f"metric {field_name} is {observed_text}, but {expected_text}."
            )
        if issue.category is FindingCategory.SPATIAL:
            return f"{issue.message or 'Spatial conflict detected.'} Location: {location_text}."
        return (
            f"For {issue.ifc_entity or 'element'} {location_text}, "
            f"field {field_name} is {observed_text}, but {expected_text}."
        )

    def _compose_body_ru(self, issue: ValidationIssue, *, essence: str) -> str:
        return (
            f"Суть: {essence}. "
            f"Норма/СТО: {self._norm_line(issue)}. "
            f"Локация: {self._location_line(issue)}. "
            f"Развёрнуто: {self._detail_ru(issue)}"
        )

    def _compose_body_en(self, issue: ValidationIssue, *, essence: str) -> str:
        return (
            f"Essence: {essence}. "
            f"Norm/STO: {self._norm_line(issue)}. "
            f"Location: {self._location_line(issue)}. "
            f"Detail: {self._detail_en(issue)}"
        )

    def _build_field_name(self, issue: ValidationIssue) -> str:
        if issue.property_set and issue.property_name:
            return f"{issue.property_set}.{issue.property_name}"
        if issue.property_name:
            return issue.property_name
        return (
            issue.target_ref
            or issue.ifc_entity
            or ("requirement" if self._locale == "en" else "требование")
        )

    def _build_expected_text_ru(self, issue: ValidationIssue) -> str:
        unit_suffix = f" {issue.unit}" if issue.unit else ""
        if issue.operator is ComparisonOperator.GREATER_OR_EQUAL:
            return f"значение должно быть не менее {issue.expected_value}{unit_suffix}"
        if issue.operator is ComparisonOperator.LESS_OR_EQUAL:
            return f"значение должно быть не более {issue.expected_value}{unit_suffix}"
        if issue.operator is ComparisonOperator.EXISTS:
            return "поле должно присутствовать"
        return f"ожидалось значение {issue.expected_value}{unit_suffix}"

    def _build_expected_text_en(self, issue: ValidationIssue) -> str:
        unit_suffix = f" {issue.unit}" if issue.unit else ""
        if issue.operator is ComparisonOperator.GREATER_OR_EQUAL:
            return f"value must be at least {issue.expected_value}{unit_suffix}"
        if issue.operator is ComparisonOperator.LESS_OR_EQUAL:
            return f"value must be at most {issue.expected_value}{unit_suffix}"
        if issue.operator is ComparisonOperator.EXISTS:
            return "the field must be present"
        return f"expected value {issue.expected_value}{unit_suffix}"

    def _build_observed_text(self, issue: ValidationIssue) -> str:
        if issue.observed_value is None:
            return "not found" if self._locale == "en" else "не найдено"
        unit_suffix = f" {issue.unit}" if issue.unit else ""
        return f"{issue.observed_value}{unit_suffix}"

    def _build_location_text(self, issue: ValidationIssue) -> str:
        if issue.problem_zone and issue.problem_zone.sheet_id:
            return issue.problem_zone.sheet_id
        if issue.target_ref:
            return issue.target_ref
        if issue.element_guid:
            return issue.element_guid
        return "no precise location" if self._locale == "en" else "без точной привязки"
