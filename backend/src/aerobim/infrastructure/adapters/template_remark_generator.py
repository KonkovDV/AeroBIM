from __future__ import annotations

from aerobim.domain.models import (
    ComparisonOperator,
    FindingCategory,
    GeneratedRemark,
    ValidationIssue,
)


class TemplateRemarkGenerator:
    """Deterministic remark templates for RU/EN product locales (TZ P0)."""

    def __init__(self, *, locale: str = "ru") -> None:
        normalized = (locale or "ru").strip().lower()
        self._locale = "en" if normalized.startswith("en") else "ru"

    def generate(self, issue: ValidationIssue) -> GeneratedRemark:
        if self._locale == "en":
            return self._generate_en(issue)
        return self._generate_ru(issue)

    def _generate_ru(self, issue: ValidationIssue) -> GeneratedRemark:
        field_name = self._build_field_name(issue)
        expected_text = self._build_expected_text_ru(issue)
        observed_text = self._build_observed_text(issue)
        location_text = self._build_location_text(issue)
        priority_hint = f" [приоритет {issue.priority}]" if issue.priority else ""

        if issue.category is FindingCategory.CROSS_DOCUMENT:
            title = f"Междокументное расхождение: {issue.rule_id}{priority_hint}"
            body = (
                f"{issue.message or 'Обнаружено противоречие между источниками.'} "
                f"Ожидание: {expected_text}. Факт: {observed_text}. "
                f"Привязка: {location_text}."
            )
            return GeneratedRemark(title=title, body=body)

        if issue.category is FindingCategory.DRAWING_VALIDATION:
            title = f"Замечание по чертежу: {issue.rule_id}{priority_hint}"
            body = (
                f"Проблемная зона на чертеже {location_text}: "
                f"показатель {field_name} имеет значение "
                f"{observed_text}, тогда как {expected_text}."
            )
            return GeneratedRemark(title=title, body=body)

        if issue.category is FindingCategory.SPATIAL:
            title = f"Пространственное замечание: {issue.rule_id}{priority_hint}"
            body = (
                f"{issue.message or 'Обнаружен пространственный конфликт.'} "
                f"Привязка: {location_text}."
            )
            return GeneratedRemark(title=title, body=body)

        title = f"Замечание по модели: {issue.rule_id}{priority_hint}"
        body = (
            f"Для {issue.ifc_entity or 'элемента'} {location_text} "
            f"поле {field_name} имеет значение "
            f"{observed_text}, тогда как {expected_text}."
        )
        return GeneratedRemark(title=title, body=body)

    def _generate_en(self, issue: ValidationIssue) -> GeneratedRemark:
        field_name = self._build_field_name(issue)
        expected_text = self._build_expected_text_en(issue)
        observed_text = self._build_observed_text(issue)
        location_text = self._build_location_text(issue)
        priority_hint = f" [priority {issue.priority}]" if issue.priority else ""

        if issue.category is FindingCategory.CROSS_DOCUMENT:
            title = f"Cross-document conflict: {issue.rule_id}{priority_hint}"
            body = (
                f"{issue.message or 'Contradiction detected between sources.'} "
                f"Expected: {expected_text}. Observed: {observed_text}. "
                f"Location: {location_text}."
            )
            return GeneratedRemark(title=title, body=body)

        if issue.category is FindingCategory.DRAWING_VALIDATION:
            title = f"Drawing remark: {issue.rule_id}{priority_hint}"
            body = (
                f"Problem zone on drawing {location_text}: "
                f"metric {field_name} is {observed_text}, but {expected_text}."
            )
            return GeneratedRemark(title=title, body=body)

        if issue.category is FindingCategory.SPATIAL:
            title = f"Spatial remark: {issue.rule_id}{priority_hint}"
            body = f"{issue.message or 'Spatial conflict detected.'} Location: {location_text}."
            return GeneratedRemark(title=title, body=body)

        title = f"Model remark: {issue.rule_id}{priority_hint}"
        body = (
            f"For {issue.ifc_entity or 'element'} {location_text}, "
            f"field {field_name} is {observed_text}, but {expected_text}."
        )
        return GeneratedRemark(title=title, body=body)

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
