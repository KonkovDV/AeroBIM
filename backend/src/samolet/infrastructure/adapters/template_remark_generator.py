from __future__ import annotations

from samolet.domain.models import ComparisonOperator, FindingCategory, GeneratedRemark, ValidationIssue


class TemplateRemarkGenerator:
    def generate(self, issue: ValidationIssue) -> GeneratedRemark:
        field_name = self._build_field_name(issue)
        expected_text = self._build_expected_text(issue)
        observed_text = self._build_observed_text(issue)
        location_text = self._build_location_text(issue)

        if issue.category is FindingCategory.DRAWING_VALIDATION:
            title = f"Замечание по чертежу: {issue.rule_id}"
            body = (
                f"Проблемная зона на чертеже {location_text}: показатель {field_name} имеет значение "
                f"{observed_text}, тогда как {expected_text}."
            )
            return GeneratedRemark(title=title, body=body)

        title = f"Замечание по модели: {issue.rule_id}"
        body = (
            f"Для {issue.ifc_entity or 'элемента'} {location_text} поле {field_name} имеет значение "
            f"{observed_text}, тогда как {expected_text}."
        )
        return GeneratedRemark(title=title, body=body)

    def _build_field_name(self, issue: ValidationIssue) -> str:
        if issue.property_set and issue.property_name:
            return f"{issue.property_set}.{issue.property_name}"
        if issue.property_name:
            return issue.property_name
        return issue.target_ref or issue.ifc_entity or "требование"

    def _build_expected_text(self, issue: ValidationIssue) -> str:
        unit_suffix = f" {issue.unit}" if issue.unit else ""
        if issue.operator is ComparisonOperator.GREATER_OR_EQUAL:
            return f"значение должно быть не менее {issue.expected_value}{unit_suffix}"
        if issue.operator is ComparisonOperator.LESS_OR_EQUAL:
            return f"значение должно быть не более {issue.expected_value}{unit_suffix}"
        if issue.operator is ComparisonOperator.EXISTS:
            return "поле должно присутствовать"
        return f"ожидалось значение {issue.expected_value}{unit_suffix}"

    def _build_observed_text(self, issue: ValidationIssue) -> str:
        if issue.observed_value is None:
            return "не найдено"
        unit_suffix = f" {issue.unit}" if issue.unit else ""
        return f"{issue.observed_value}{unit_suffix}"

    def _build_location_text(self, issue: ValidationIssue) -> str:
        if issue.problem_zone and issue.problem_zone.sheet_id:
            return issue.problem_zone.sheet_id
        if issue.target_ref:
            return issue.target_ref
        if issue.element_guid:
            return issue.element_guid
        return "без точной привязки"