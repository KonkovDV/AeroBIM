from __future__ import annotations

from pathlib import Path

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
            import ifcopenshell
            from ifctester import ids, reporter
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "ifcopenshell and ifctester are required for IDS validation"
            ) from exc

        specs = ids.open(str(ids_path))
        ifc_file = ifcopenshell.open(str(ifc_path))
        specs.validate(ifc_file)

        json_reporter = reporter.Json(specs)
        results = json_reporter.report()

        return self._map_results(results)

    def _map_results(self, results: dict) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for spec in results.get("specifications", []):
            spec_name = spec.get("name", "Unknown Specification")
            spec_status = spec.get("status", True)

            if spec_status:
                continue

            for requirement in spec.get("requirements", []):
                if requirement.get("status", True):
                    continue

                facet_type = requirement.get("facet_type", "")
                description = requirement.get("description", "")
                base_message = f"[IDS] {spec_name}: {facet_type}"
                if description:
                    base_message = f"{base_message} — {description}"

                for entity in requirement.get("failed_entities", []):
                    entity_reason = entity.get("reason", "")
                    entity_element = entity.get("element", "")
                    element_guid = self._extract_guid(entity_element)

                    message = base_message
                    if entity_reason:
                        message = f"{message} ({entity_reason})"

                    issues.append(
                        ValidationIssue(
                            rule_id=f"IDS-{spec_name}",
                            severity=Severity.ERROR,
                            message=message,
                            category=FindingCategory.IDS_VALIDATION,
                            element_guid=element_guid,
                        )
                    )

        return issues

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
