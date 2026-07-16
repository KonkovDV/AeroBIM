"""Deterministic RequirementSource/ParsedRequirement → IDS 1.0 XML draft."""

from __future__ import annotations

from collections.abc import Sequence
from xml.sax.saxutils import escape

from aerobim.domain.models import ParsedRequirement, RequirementSource, RuleScope
from aerobim.domain.norm_assist import IdsCompileDraft
from aerobim.domain.ports import RequirementExtractor


class DeterministicRequirementToIdsCompiler:
    """Compile structured requirements into IDS XML without LLM.

    Advisory-only: output must be human-reviewed before use as ``ids_path``.
    """

    def __init__(self, requirement_extractor: RequirementExtractor | None = None) -> None:
        self._extractor = requirement_extractor

    def compile(self, source: RequirementSource) -> IdsCompileDraft:
        if self._extractor is None:
            return IdsCompileDraft(
                suggested_ids_xml="",
                rationale="RequirementExtractor not configured for IDS compile",
                source_requirement_count=0,
                confidence=0.0,
            )
        requirements = self._extractor.extract(source)
        return self.compile_requirements(requirements)

    def compile_requirements(self, requirements: Sequence[ParsedRequirement]) -> IdsCompileDraft:
        usable = [
            req
            for req in requirements
            if req.rule_scope in {RuleScope.IFC_PROPERTY, RuleScope.IFC_QUANTITY}
            and req.ifc_entity
            and req.property_name
        ]
        if not usable:
            return IdsCompileDraft(
                suggested_ids_xml="",
                rationale="No IFC property/quantity requirements available for IDS compile",
                source_requirement_count=0,
                confidence=0.0,
            )

        specs: list[str] = []
        for req in usable:
            entity = escape((req.ifc_entity or "IFCWALL").upper())
            pset = escape(req.property_set or "Pset_WallCommon")
            base = escape(req.property_name or "")
            value = escape(req.expected_value or "")
            name = escape(req.rule_id)
            specs.append(
                f"""        <specification name="{name}" ifcVersion="IFC2X3 IFC4 IFC4X3_ADD2">
            <applicability minOccurs="0" maxOccurs="unbounded">
                <entity>
                    <name>
                        <simpleValue>{entity}</simpleValue>
                    </name>
                </entity>
            </applicability>
            <requirements>
                <property cardinality="required">
                    <propertySet>
                        <simpleValue>{pset}</simpleValue>
                    </propertySet>
                    <baseName>
                        <simpleValue>{base}</simpleValue>
                    </baseName>
                    <value>
                        <simpleValue>{value}</simpleValue>
                    </value>
                </property>
            </requirements>
        </specification>"""
            )

        xml = (
            "<?xml version='1.0' encoding='utf-8'?>\n"
            '<ids xmlns="http://standards.buildingsmart.org/IDS" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:schemaLocation="http://standards.buildingsmart.org/IDS '
            'http://standards.buildingsmart.org/IDS/1.0/ids.xsd">\n'
            "    <info>\n"
            "        <title>AeroBIM deterministic draft IDS</title>\n"
            "    </info>\n"
            "    <specifications>\n" + "\n".join(specs) + "\n    </specifications>\n</ids>\n"
        )
        return IdsCompileDraft(
            suggested_ids_xml=xml,
            rationale=(
                f"Compiled {len(usable)} IFC property/quantity rule(s) into IDS 1.0 XML. "
                "Advisory only — human review required before sign-off use."
            ),
            source_requirement_count=len(usable),
            advisory_only=True,
            confidence=0.55,
        )
