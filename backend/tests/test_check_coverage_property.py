"""WP-R4 / I-8: Hypothesis property — no_findings impossible without executed check."""

from __future__ import annotations

import unittest

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from aerobim.domain.check_coverage import (
    PRESENTATION_STATES,
    CoverageStatus,
    build_check_coverage,
    operator_status_for,
    presentation_status_for,
)
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    ReportCapabilities,
    Severity,
    ValidationIssue,
)

_FAMILIES = list(FindingCategory)
_CAP_FIELDS = (
    "ifc_validation",
    "ifc_schema",
    "ids",
    "raster",
    "section_pairing",
    "clash",
    "mep_system_clash",
)
_STATES = list(CapabilityState)


def _issue(source: str, family: FindingCategory) -> ValidationIssue:
    return ValidationIssue(
        rule_id="R",
        severity=Severity.ERROR,
        message="m",
        category=family,
        source_id=source,
        origin="deterministic",
    )


@st.composite
def capability_statuses(draw: st.DrawFn) -> ReportCapabilities:
    kwargs: dict[str, CapabilityStatus] = {}
    for field in _CAP_FIELDS:
        if draw(st.booleans()):
            state = draw(st.sampled_from(_STATES))
            reason = "boom" if state is CapabilityState.FAILED else None
            kwargs[field] = CapabilityStatus(state, reason)
    return ReportCapabilities(**kwargs)


class CheckCoverageHypothesisTests(unittest.TestCase):
    @settings(
        deadline=None,
        max_examples=40,
        suppress_health_check=[
            HealthCheck.too_slow,
            HealthCheck.filter_too_much,
            HealthCheck.data_too_large,
        ],
    )
    @given(
        source_count=st.integers(min_value=1, max_value=4),
        caps=capability_statuses(),
        use_scope=st.booleans(),
        add_issue=st.booleans(),
        family_index=st.integers(min_value=0, max_value=len(_FAMILIES) - 1),
    )
    def test_i8_no_findings_only_when_checked_ok(
        self,
        source_count: int,
        caps: ReportCapabilities,
        use_scope: bool,
        add_issue: bool,
        family_index: int,
    ) -> None:
        sources = [f"src-{i}" for i in range(source_count)]
        scope: dict[FindingCategory, set[str]] | None
        if use_scope:
            scope = {
                fam: (set(sources) if (idx % 2 == 0) else set())
                for idx, fam in enumerate(_FAMILIES)
            }
        else:
            scope = None
        issues: list[ValidationIssue] = []
        if add_issue and sources:
            issues.append(_issue(sources[0], _FAMILIES[family_index]))
        cov = build_check_coverage(
            source_ids=sources, issues=issues, capabilities=caps, scope=scope
        )
        for row in cov.rows:
            for _family, status in row.families:
                op = operator_status_for(status)
                pres = presentation_status_for(status)
                if op == "findings":
                    self.assertNotIn(pres, PRESENTATION_STATES)
                if op == "no_findings":
                    self.assertIs(status, CoverageStatus.CHECKED_OK)
                if status is not CoverageStatus.CHECKED_OK:
                    self.assertNotEqual(op, "no_findings")
                if status is CoverageStatus.CHECKED_OK:
                    self.assertEqual(op, "no_findings")
                    self.assertEqual(pres, "no_findings")

    def test_findings_not_in_presentation_states_gap_set(self) -> None:
        self.assertNotIn("findings", PRESENTATION_STATES)
        self.assertEqual(presentation_status_for(CoverageStatus.CHECKED_FINDINGS), "findings")

    def test_tz_gaps_are_always_not_checked(self) -> None:
        from aerobim.domain.check_coverage import tz_gap_rows_for_report

        rows = tz_gap_rows_for_report()
        self.assertEqual(len(rows), 6)
        for row in rows:
            self.assertEqual(row["status"], "not_checked")
            self.assertTrue(str(row.get("reason") or "").strip())
