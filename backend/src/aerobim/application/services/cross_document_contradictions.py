"""Cross-document contradiction detection (extracted from AnalyzeProjectPackageUseCase).

Compares requirements originating from different sources for the same
(entity, property) pair and classifies conflicts with a configured ε-band
so that unit-encoding differences do not produce false positives.
"""

from __future__ import annotations

from collections.abc import Sequence

from aerobim.domain.models import (
    ComparisonOperator,
    ConflictKind,
    FindingCategory,
    ParsedRequirement,
    Severity,
    ToleranceConfig,
    ValidationIssue,
)
from aerobim.domain.quantity import (
    QuantityValue,
    looks_like_numeric_token,
    normalize_unit_token,
    parse_localized_number,
    parse_quantity,
    si_compare,
)

_CROSS_DOC_UNIT_TO_SI_FACTOR: dict[str, tuple[str, float]] = {
    "m": ("m", 1.0),
    "м": ("m", 1.0),
    "mm": ("m", 0.001),
    "мм": ("m", 0.001),
    "cm": ("m", 0.01),
    "см": ("m", 0.01),
    "ft": ("m", 0.3048),
    "feet": ("m", 0.3048),
    "foot": ("m", 0.3048),
    "in": ("m", 0.0254),
    "inch": ("m", 0.0254),
    "inches": ("m", 0.0254),
    "m2": ("m2", 1.0),
    "м2": ("m2", 1.0),
    "m²": ("m2", 1.0),
    "м²": ("m2", 1.0),
    "sqm": ("m2", 1.0),
    "sq.m": ("m2", 1.0),
    "m3": ("m3", 1.0),
    "м3": ("m3", 1.0),
    "m³": ("m3", 1.0),
    "м³": ("m3", 1.0),
}


def to_float(raw: str) -> float | None:
    return parse_localized_number(raw)


class CrossDocumentContradictionDetector:
    """Deterministic cross-document conflict detector with ε-tolerance."""

    def __init__(self, tolerance: ToleranceConfig, severity: Severity) -> None:
        self._tolerance = tolerance
        self._severity = severity

    def detect(
        self,
        requirements: Sequence[ParsedRequirement],
    ) -> list[ValidationIssue]:
        """Compare requirements from different sources for the same (entity, property).

        When two sources specify conflicting expected values for the same
        IFC entity + property pair, emit a CROSS_DOCUMENT issue.  Numeric
        values are compared with a configured ε-band so that rounding
        differences (e.g. 3.0 m vs 3000 mm) do not produce false positives.
        The severity of emitted issues is controlled by the configured severity
        (``AEROBIM_CROSS_DOC_SEVERITY``).  The ``conflict_kind`` field classifies
        the nature of the conflict for downstream policy filtering.
        """
        issues: list[ValidationIssue] = []
        keyed: dict[tuple[str, str, str, str], list[ParsedRequirement]] = {}

        for req in requirements:
            if not req.ifc_entity or not req.property_name:
                continue
            key = (
                req.ifc_entity.upper(),
                self._normalize_pset(req.property_set),
                req.property_name.lower(),
                (req.target_ref or "").strip(),
            )
            keyed.setdefault(key, []).append(req)

        for (entity, property_set, prop, _target), reqs in keyed.items():
            if len(reqs) < 2:
                continue
            seen: list[ParsedRequirement] = []
            for req in reqs:
                if req.expected_value is None:
                    continue
                for prev_req in seen:
                    if self._same_document(prev_req, req):
                        continue
                    interval = self._interval_compatibility(prev_req, req)
                    if interval is True:
                        continue
                    soft = False
                    hard = False
                    if interval is False:
                        hard = True
                    else:
                        soft = self.values_soft_conflict(
                            prev_req.expected_value,
                            prev_req.unit,
                            req.expected_value,
                            req.unit,
                            quantity_a=prev_req.quantity,
                            quantity_b=req.quantity,
                        )
                        hard = self.values_conflict(
                            prev_req.expected_value,
                            prev_req.unit,
                            req.expected_value,
                            req.unit,
                            quantity_a=prev_req.quantity,
                            quantity_b=req.quantity,
                        )
                    if not soft and not hard:
                        continue
                    prev_val = (prev_req.expected_value or "").strip()
                    val = (req.expected_value or "").strip()
                    property_label = (
                        f"{entity}.{property_set}.{prop}" if property_set else f"{entity}.{prop}"
                    )
                    if soft and not hard:
                        conflict_kind = ConflictKind.SOFT_CONFLICT_WITHIN_TOLERANCE
                        severity = Severity.INFO
                    else:
                        conflict_kind = self.classify_conflict_kind(
                            prev_req.expected_value,
                            prev_req.unit,
                            req.expected_value,
                            req.unit,
                            quantity_a=prev_req.quantity,
                            quantity_b=req.quantity,
                        )
                        if interval is False and conflict_kind not in {
                            ConflictKind.UNIT_MISMATCH,
                            ConflictKind.UNPARSED_NUMERIC,
                        }:
                            conflict_kind = ConflictKind.HARD_CONFLICT
                        severity = self._severity
                    if conflict_kind is ConflictKind.UNPARSED_NUMERIC:
                        message = (
                            f"Unparsed numeric token in cross-document pair: {property_label} "
                            f"'{prev_val}' (from {prev_req.source_kind.value}) vs "
                            f"'{val}' (from {req.source_kind.value}). "
                            "Not classified as mapping ambiguity."
                        )
                    else:
                        message = (
                            f"Cross-document contradiction: {property_label} "
                            f"expects '{prev_val}' (from {prev_req.source_kind.value}) "
                            f"but '{val}' (from {req.source_kind.value})"
                        )
                    match_method = "entity+pset+prop" if property_set else "entity+prop"
                    if (req.target_ref or prev_req.target_ref or "").strip():
                        match_method = f"{match_method}+target_ref"
                    issues.append(
                        ValidationIssue(
                            rule_id=f"CROSS-DOC-{entity}-{prop}",
                            severity=severity,
                            message=message,
                            ifc_entity=entity,
                            category=FindingCategory.CROSS_DOCUMENT,
                            property_set=prev_req.property_set or req.property_set,
                            property_name=prop,
                            expected_value=prev_val,
                            observed_value=val,
                            conflict_kind=conflict_kind,
                            origin="deterministic",
                            match_method=match_method,
                            target_ref=(req.target_ref or prev_req.target_ref),
                            source_id=(
                                f"cross-doc:{self._document_identity(prev_req)}"
                                f"|{self._document_identity(req)}"
                            ),
                            evidence_modality="cross-document",
                            evidence_refs=(
                                f"cross-doc@{prev_req.source_kind.value}#{property_label}",
                                f"cross-doc@{req.source_kind.value}#{property_label}",
                            ),
                        )
                    )
                seen.append(req)

        issues.extend(self.detect_ambiguous_property_set_alignments(requirements))
        return issues

    def detect_ambiguous_property_set_alignments(
        self,
        requirements: Sequence[ParsedRequirement],
    ) -> list[ValidationIssue]:
        """Escalate same entity+property across sources when Psets differ.

        Exact-key comparison already handles identical (entity, pset, prop).
        Silent non-pairing of FireRating across Pset_WallCommon vs Pset_FireSafety
        must not look like agreement — emit AMBIGUOUS_MAPPING for HITL.
        """
        by_entity_prop: dict[tuple[str, str, str], list[ParsedRequirement]] = {}
        for req in requirements:
            if not req.ifc_entity or not req.property_name or req.expected_value is None:
                continue
            key = (
                req.ifc_entity.upper(),
                req.property_name.lower(),
                (req.target_ref or "").strip(),
            )
            by_entity_prop.setdefault(key, []).append(req)

        issues: list[ValidationIssue] = []
        for (entity, prop, _target), reqs in by_entity_prop.items():
            identities = {self._document_identity(req) for req in reqs}
            if len(identities) < 2:
                continue
            psets = {self._normalize_pset(req.property_set) for req in reqs}
            if len(psets) < 2:
                continue
            labeled = sorted(pset or "<none>" for pset in psets)
            sample = reqs[0]
            other = next(
                req
                for req in reqs
                if self._document_identity(req) != self._document_identity(sample)
            )
            issues.append(
                ValidationIssue(
                    rule_id=f"CROSS-DOC-AMBIGUOUS-{entity}-{prop}",
                    severity=Severity.ERROR,
                    message=(
                        f"Unresolved cross-document alignment: {entity}.{prop} appears under "
                        f"divergent property sets {labeled} across "
                        f"{sample.source_kind.value} and {other.source_kind.value}. "
                        "Do not treat as agreement — escalate to HITL."
                    ),
                    ifc_entity=entity,
                    category=FindingCategory.CROSS_DOCUMENT,
                    property_set=sample.property_set or other.property_set,
                    property_name=prop,
                    expected_value=sample.expected_value,
                    observed_value=other.expected_value,
                    conflict_kind=ConflictKind.AMBIGUOUS_MAPPING,
                    source_id=f"cross-doc:{sample.source_kind.value}|{other.source_kind.value}",
                    evidence_modality="cross-document",
                    confidence=0.0,
                    origin="deterministic",
                    match_method="entity+prop(divergent-pset)",
                    evidence_refs=(
                        f"cross-doc@{sample.source_kind.value}#{entity}.{prop}",
                        f"cross-doc@{other.source_kind.value}#{entity}.{prop}",
                    ),
                )
            )
        return issues

    @staticmethod
    def _normalize_pset(property_set: str | None) -> str:
        return (property_set or "").strip().lower()

    @staticmethod
    def _document_identity(req: ParsedRequirement) -> str:
        """Concrete document, not merely the source_kind class.

        Empty ``source`` does not collapse two records of the same kind into one
        document — that would hide two drawings of one type.
        """
        source = (req.source or "").strip()
        if source:
            return f"{req.source_kind.value}:{source}"
        return f"{req.source_kind.value}:anon:{req.rule_id}"

    def _same_document(self, left: ParsedRequirement, right: ParsedRequirement) -> bool:
        return self._document_identity(left) == self._document_identity(right)

    def _interval_compatibility(
        self,
        left: ParsedRequirement,
        right: ParsedRequirement,
    ) -> bool | None:
        """Compare gte/lte/eq as intervals in SI space.

        Returns True when the allowed sets intersect, False when they are
        disjoint, None when the pair is a plain equality (use SI compare).
        """
        interval_ops = {
            ComparisonOperator.GREATER_OR_EQUAL,
            ComparisonOperator.LESS_OR_EQUAL,
            ComparisonOperator.EQUALS,
        }
        if left.operator not in interval_ops or right.operator not in interval_ops:
            return None
        if (
            left.operator is ComparisonOperator.EQUALS
            and right.operator is ComparisonOperator.EQUALS
        ):
            return None
        q_left = self.resolve_quantity(left.expected_value, left.unit, left.quantity)
        q_right = self.resolve_quantity(right.expected_value, right.unit, right.quantity)
        if (
            q_left is not None
            and q_right is not None
            and q_left.dimension
            and q_right.dimension
            and q_left.dimension != q_right.dimension
        ):
            return False
        left_si = q_left.si_value if q_left is not None else None
        right_si = q_right.si_value if q_right is not None else None
        if left_si is None or right_si is None:
            return None
        low = float("-inf")
        high = float("inf")
        for operator, value in ((left.operator, left_si), (right.operator, right_si)):
            if operator is ComparisonOperator.EQUALS:
                low = max(low, value)
                high = min(high, value)
            elif operator is ComparisonOperator.GREATER_OR_EQUAL:
                low = max(low, value)
            else:
                high = min(high, value)
        eps = self._tolerance.epsilon_for_quantities(q_left, q_right)
        return low <= high + eps

    def resolve_quantity(
        self,
        value: str | None,
        unit: str | None,
        quantity: QuantityValue | None,
    ) -> QuantityValue | None:
        if quantity is not None and quantity.si_value is not None:
            return quantity
        if value is None:
            return None
        numeric = to_float(value.strip())
        if numeric is None:
            return None
        return parse_quantity(numeric, unit or "")

    def classify_conflict_kind(
        self,
        value_a: str | None,
        unit_a: str | None,
        value_b: str | None,
        unit_b: str | None,
        *,
        quantity_a: QuantityValue | None = None,
        quantity_b: QuantityValue | None = None,
    ) -> ConflictKind:
        """Classify a detected cross-document conflict into a ``ConflictKind``.

        Decision order:
        0. UNPARSED_NUMERIC — token looks numeric but grouping/separators
           are ambiguous (fail-closed; not mapping ambiguity).
        1. UNIT_MISMATCH — incompatible or inconsistent unit encoding
           (including dimension mismatch, e.g. m vs m2).
        2. SOFT_CONFLICT_WITHIN_TOLERANCE — SI values agree within ε.
           Fail-closed guard: never claim HARD on equal / in-band values
           even if a caller skipped ``values_conflict``.
        3. HARD_CONFLICT — values differ after full SI normalisation.
        4. AMBIGUOUS_MAPPING — non-numeric values with no unit context.
        """
        if value_a is None or value_b is None:
            return ConflictKind.AMBIGUOUS_MAPPING
        if (looks_like_numeric_token(value_a) and parse_localized_number(value_a) is None) or (
            looks_like_numeric_token(value_b) and parse_localized_number(value_b) is None
        ):
            return ConflictKind.UNPARSED_NUMERIC

        q_a = self.resolve_quantity(value_a, unit_a, quantity_a)
        q_b = self.resolve_quantity(value_b, unit_b, quantity_b)

        if (
            q_a is not None
            and q_b is not None
            and q_a.si_value is not None
            and q_b.si_value is not None
        ):
            if q_a.ucum_code and q_b.ucum_code:
                if q_a.dimension != q_b.dimension:
                    return ConflictKind.UNIT_MISMATCH
                eps = self._tolerance.epsilon_for_quantities(q_a, q_b)
                if si_compare(q_a, q_b, epsilon=eps):
                    return ConflictKind.SOFT_CONFLICT_WITHIN_TOLERANCE
                return ConflictKind.HARD_CONFLICT
            if unit_a and unit_b and normalize_unit_token(unit_a) != normalize_unit_token(unit_b):
                return ConflictKind.UNIT_MISMATCH
            eps = self._tolerance.epsilon_for_quantities(q_a, q_b)
            if si_compare(q_a, q_b, epsilon=eps):
                return ConflictKind.SOFT_CONFLICT_WITHIN_TOLERANCE
            return ConflictKind.HARD_CONFLICT

        a_num = to_float(value_a.strip())
        b_num = to_float(value_b.strip())
        if a_num is not None and b_num is not None:
            parsed_a = parse_quantity(a_num, unit_a or "")
            parsed_b = parse_quantity(b_num, unit_b or "")
            if not (parsed_a.ucum_code and parsed_b.ucum_code):
                unit_a_norm = normalize_unit_token(unit_a)
                unit_b_norm = normalize_unit_token(unit_b)
                if (
                    parsed_a.ucum_code
                    or parsed_b.ucum_code
                    or (unit_a_norm and unit_b_norm and unit_a_norm != unit_b_norm)
                ):
                    return ConflictKind.UNIT_MISMATCH
                return ConflictKind.AMBIGUOUS_MAPPING
            if parsed_a.dimension != parsed_b.dimension:
                return ConflictKind.UNIT_MISMATCH
            eps = self._tolerance.epsilon_for_quantities(parsed_a, parsed_b)
            if si_compare(parsed_a, parsed_b, epsilon=eps):
                return ConflictKind.SOFT_CONFLICT_WITHIN_TOLERANCE
            return ConflictKind.HARD_CONFLICT

        # Non-numeric / uncalibrated strings: do not pretend hard SI conflict.
        return ConflictKind.AMBIGUOUS_MAPPING

    def values_soft_conflict(
        self,
        value_a: str | None,
        unit_a: str | None,
        value_b: str | None,
        unit_b: str | None,
        *,
        quantity_a: QuantityValue | None = None,
        quantity_b: QuantityValue | None = None,
    ) -> bool:
        """True when same-unit numeric strings differ but stay within ε."""
        if value_a is None or value_b is None:
            return False
        a_str = value_a.strip()
        b_str = value_b.strip()
        if a_str.lower() == b_str.lower():
            return False
        # Unit-normalized equivalence (1 m vs 1000 mm) is not a soft conflict.
        unit_a_norm = normalize_unit_token(unit_a)
        unit_b_norm = normalize_unit_token(unit_b)
        if unit_a_norm and unit_b_norm and unit_a_norm != unit_b_norm:
            return False
        if self.values_conflict(
            value_a,
            unit_a,
            value_b,
            unit_b,
            quantity_a=quantity_a,
            quantity_b=quantity_b,
        ):
            return False

        a_num = to_float(a_str)
        b_num = to_float(b_str)
        if a_num is None or b_num is None:
            return False
        parsed_a = parse_quantity(a_num, unit_a or "")
        parsed_b = parse_quantity(b_num, unit_b or "")
        if not (parsed_a.ucum_code and parsed_b.ucum_code):
            return False
        return a_num != b_num

    def values_conflict(
        self,
        value_a: str | None,
        unit_a: str | None,
        value_b: str | None,
        unit_b: str | None,
        *,
        quantity_a: QuantityValue | None = None,
        quantity_b: QuantityValue | None = None,
    ) -> bool:
        """Return True when two expected values are materially different.

        Numeric pairs are compared with ε-tolerance from ``ToleranceConfig``;
        non-numeric pairs use case-insensitive string comparison.
        """
        if value_a is None or value_b is None:
            return False
        a_str = value_a.strip()
        b_str = value_b.strip()

        q_a = self.resolve_quantity(value_a, unit_a, quantity_a)
        q_b = self.resolve_quantity(value_b, unit_b, quantity_b)
        if (
            q_a is not None
            and q_b is not None
            and q_a.si_value is not None
            and q_b.si_value is not None
            and q_a.ucum_code
            and q_b.ucum_code
        ):
            if q_a.dimension != q_b.dimension:
                return True
            eps = self._tolerance.epsilon_for_quantities(q_a, q_b)
            return not si_compare(q_a, q_b, epsilon=eps)

        a_num = to_float(a_str)
        b_num = to_float(b_str)
        if a_num is not None and b_num is not None:
            parsed_a = parse_quantity(a_num, unit_a or "")
            parsed_b = parse_quantity(b_num, unit_b or "")
            if parsed_a.ucum_code and parsed_b.ucum_code:
                if parsed_a.dimension != parsed_b.dimension:
                    return True
                eps = self._tolerance.epsilon_for_quantities(parsed_a, parsed_b)
                return not si_compare(parsed_a, parsed_b, epsilon=eps)
            unit_a_norm = normalize_unit_token(unit_a)
            unit_b_norm = normalize_unit_token(unit_b)
            if (
                parsed_a.ucum_code
                or parsed_b.ucum_code
                or (unit_a_norm and unit_b_norm and unit_a_norm != unit_b_norm)
            ):
                return True
            return False

        return a_str.lower() != b_str.lower()

    def normalize_numeric_value(
        self,
        value: float,
        unit: str | None,
    ) -> tuple[float, str] | None:
        if unit is None:
            return None
        normalized = _CROSS_DOC_UNIT_TO_SI_FACTOR.get(normalize_unit_token(unit))
        if normalized is None:
            return None
        canonical_unit, factor = normalized
        return value * factor, canonical_unit


CrossDocConsistencyChecker = CrossDocumentContradictionDetector
