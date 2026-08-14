from __future__ import annotations

from pathlib import Path
from typing import Any

from aerobim.domain.ids_schema_gate import (
    RULE_IFC_VERSION,
    RULE_SKIPPED,
    collect_schema_mismatches,
    parse_ids_specification_versions,
    parse_ifc_file_schema,
    skipped_spec_fail_closed_rule_id,
)
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue


class IfcTesterIdsValidator:
    """IDS-to-IFC validation adapter using IfcTester (IfcOpenShell ecosystem).

    Loads an IDS XML file, validates it against an IFC model, and maps
    the structured IfcTester ``Results`` into domain ``ValidationIssue`` objects.

    IfcTester treats ``ifcVersion`` as metadata (BSI case 0101). This adapter
    additionally fail-closes schema mismatch and skipped specs so a clean
    reporter status cannot hide an un-run check.
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

        ids_xml = ids_path.read_text(encoding="utf-8", errors="replace")
        header = ifc_path.read_bytes()[: 64 * 1024].decode("utf-8", errors="replace")
        model_schema = parse_ifc_file_schema(header)
        our_mismatches = collect_schema_mismatches(
            model_schema=model_schema,
            specs=parse_ids_specification_versions(ids_xml),
        )

        specs = ids.open(str(ids_path))
        from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_model

        ifc_file = open_ifc_model(ifc_path)
        specs.validate(ifc_file)

        json_reporter = reporter.Json(specs)
        results = json_reporter.report()

        mapped = self._map_results(results)
        independent_names = {mismatch.spec_name for mismatch in our_mismatches}
        issues = [
            issue
            for issue in mapped
            if not (
                issue.rule_id == RULE_IFC_VERSION
                and self._spec_name_from_issue(issue) in independent_names
            )
        ]
        for mismatch in our_mismatches:
            issues.append(
                self._schema_mismatch_issue(
                    mismatch.spec_name,
                    mismatch.model_schema,
                    mismatch.ids_versions,
                )
            )
        return issues

    @staticmethod
    def _spec_name_from_issue(issue: ValidationIssue) -> str:
        message = issue.message
        if message.startswith("[IDS] "):
            return message[6:].split(":", 1)[0].strip()
        return message

    def _schema_mismatch_issue(
        self,
        spec_name: str,
        model_schema: str,
        ids_versions: tuple[str, ...],
    ) -> ValidationIssue:
        allowed = ",".join(ids_versions) if ids_versions else "(none)"
        observed = model_schema or "(missing FILE_SCHEMA)"
        return ValidationIssue(
            rule_id=RULE_IFC_VERSION,
            severity=Severity.ERROR,
            message=(
                f"[IDS] {spec_name}: FILE_SCHEMA {observed} is not in IDS "
                f"ifcVersion [{allowed}] (AeroBIM fail-closed; IfcTester does "
                "not treat version mismatch as a failure)"
            ),
            category=FindingCategory.IDS_VALIDATION,
            expected_value=allowed,
            observed_value=observed,
            origin="deterministic",
        )

    def _map_results(self, results: dict[str, Any]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for spec in results.get("specifications", []):
            spec_name = spec.get("name", "Unknown Specification")
            spec_status = spec.get("status", True)
            skip_rule = skipped_spec_fail_closed_rule_id(
                is_skipped=spec.get("is_skipped"),
                status=spec.get("status"),
                is_ifc_version=spec.get("is_ifc_version"),
            )
            if skip_rule is not None:
                if skip_rule == RULE_IFC_VERSION:
                    versions = spec.get("ifcVersion") or spec.get("ifc_version") or ()
                    if isinstance(versions, str):
                        version_tuple = tuple(versions.split())
                    elif isinstance(versions, (list, tuple)):
                        version_tuple = tuple(str(item) for item in versions)
                    else:
                        version_tuple = ()
                    issues.append(
                        self._schema_mismatch_issue(
                            spec_name,
                            "IfcTester.is_ifc_version=false",
                            version_tuple,
                        )
                    )
                else:
                    issues.append(
                        ValidationIssue(
                            rule_id=RULE_SKIPPED,
                            severity=Severity.ERROR,
                            message=(
                                f"[IDS] {spec_name}: specification was SKIPPED "
                                "(optional/zero-check or never executed); "
                                "AeroBIM fail-closed treats SKIPPED as FAILED"
                            ),
                            category=FindingCategory.IDS_VALIDATION,
                            origin="deterministic",
                        )
                    )
                continue

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
