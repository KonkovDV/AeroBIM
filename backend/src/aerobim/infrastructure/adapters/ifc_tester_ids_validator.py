from __future__ import annotations

from pathlib import Path
from typing import Any

from aerobim.domain.models import FindingCategory, Severity, ValidationIssue


class IfcTesterIdsValidator:
    """IDS-to-IFC validation adapter using IfcTester (IfcOpenShell ecosystem).

    Loads an IDS XML file, validates it against an IFC model, and maps
    the structured IfcTester ``Results`` into domain ``ValidationIssue`` objects.
    """

    def validate(self, ids_path: Path, ifc_path: Path) -> list[ValidationIssue]:
        if not ids_path.exists():
            raise FileNotFoundError(f"IDS file not found: {ids_path}")
        if not ifc_path.exists():
            raise FileNotFoundError(f"IFC file not found: {ifc_path}")

        try:
            from ifctester import ids, reporter
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "ifcopenshell and ifctester are required for IDS validation"
            ) from exc

        specs = ids.open(str(ids_path))
        from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_model

        ifc_file = open_ifc_model(ifc_path)
        specs.validate(ifc_file)

        json_reporter = reporter.Json(specs)
        results = json_reporter.report()

        return self._map_results(results)

    def _map_results(self, results: dict[str, Any]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for spec in results.get("specifications", []):
            spec_name = spec.get("name", "Unknown Specification")
            spec_status = spec.get("status", True)

            if spec_status:
                continue

            requirements = spec.get("requirements") or []
            cardinality = str(spec.get("cardinality") or "").lower()

            # Prohibited specs fail when applicability matches; requirements[] may be empty.
            if not requirements and cardinality == "prohibited":
                total_applicable = int(spec.get("total_applicable") or 0)
                if total_applicable > 0:
                    applicable_entities = spec.get("applicable_entities") or []
                    if applicable_entities:
                        for entity in applicable_entities:
                            issues.append(
                                self._build_issue(
                                    spec_name=spec_name,
                                    facet_type="Specification",
                                    description="Prohibited specification applicability matched",
                                    entity_reason=(
                                        "Applicability must not match for prohibited specs"
                                    ),
                                    entity_element=entity.get("element"),
                                )
                            )
                    else:
                        issues.append(
                            self._build_issue(
                                spec_name=spec_name,
                                facet_type="Specification",
                                description="Prohibited specification applicability matched",
                                entity_reason=(
                                    f"{total_applicable} applicable entit"
                                    f"{'y' if total_applicable == 1 else 'ies'} matched"
                                ),
                                entity_element=None,
                            )
                        )
                continue

            for requirement in requirements:
                if requirement.get("status", True):
                    continue

                facet_type = requirement.get("facet_type", "")
                description = requirement.get("description", "")
                failed_entities = requirement.get("failed_entities") or []

                if failed_entities:
                    for entity in failed_entities:
                        issues.append(
                            self._build_issue(
                                spec_name=spec_name,
                                facet_type=facet_type,
                                description=description,
                                entity_reason=str(entity.get("reason", "")),
                                entity_element=entity.get("element"),
                            )
                        )
                else:
                    # Required spec with zero applicable entities reports status=false but no rows.
                    issues.append(
                        self._build_issue(
                            spec_name=spec_name,
                            facet_type=facet_type,
                            description=description,
                            entity_reason="Requirement not satisfied",
                            entity_element=None,
                        )
                    )

        return issues

    def _build_issue(
        self,
        *,
        spec_name: str,
        facet_type: str,
        description: str,
        entity_reason: str,
        entity_element: object,
    ) -> ValidationIssue:
        base_message = f"[IDS] {spec_name}: {facet_type}"
        if description:
            base_message = f"{base_message} — {description}"
        if entity_reason:
            base_message = f"{base_message} ({entity_reason})"

        return ValidationIssue(
            rule_id=f"IDS-{spec_name}",
            severity=Severity.ERROR,
            message=base_message,
            category=FindingCategory.IDS_VALIDATION,
            element_guid=self._extract_guid(entity_element),
        )

    def _extract_guid(self, element_repr: object) -> str | None:
        if not element_repr:
            return None

        global_id = getattr(element_repr, "GlobalId", None)
        if global_id is not None:
            return str(global_id) or None

        if not isinstance(element_repr, str):
            element_repr = str(element_repr)

        if "#" in element_repr:
            return element_repr.split("#")[0].strip() or None
        return element_repr or None
