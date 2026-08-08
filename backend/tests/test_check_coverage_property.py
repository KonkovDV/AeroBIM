"""WP-R4 / I-8: property-style guard — no_findings impossible without executed check."""

from __future__ import annotations

import random
import unittest

from aerobim.domain.check_coverage import (
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

_FAMILIES = tuple(FindingCategory)
_CAP_FIELDS = (
    "ifc_validation",
    "ifc_schema",
    "ids",
    "raster",
    "section_pairing",
    "clash",
    "mep_system_clash",
)
_STATES = tuple(CapabilityState)


def _rand_issue(source: str, family: FindingCategory) -> ValidationIssue:
    return ValidationIssue(
        rule_id="R",
        severity=Severity.ERROR,
        message="m",
        category=family,
        source_id=source,
        origin="deterministic",
    )


def _rand_caps(rng: random.Random) -> ReportCapabilities:
    kwargs: dict[str, CapabilityStatus] = {}
    for field in _CAP_FIELDS:
        if rng.random() < 0.55:
            state = rng.choice(_STATES)
            reason = "boom" if state is CapabilityState.FAILED else None
            kwargs[field] = CapabilityStatus(state, reason)
    return ReportCapabilities(**kwargs)


class CheckCoveragePropertyTests(unittest.TestCase):
    def test_i8_no_findings_only_when_checked_ok(self) -> None:
        rng = random.Random(20260808)
        for _ in range(200):
            sources = [f"src-{i}" for i in range(rng.randint(1, 4))]
            caps = _rand_caps(rng)
            scope: dict[FindingCategory, set[str]] | None
            if rng.random() < 0.5:
                scope = {
                    fam: set(rng.sample(sources, k=rng.randint(0, len(sources))))
                    for fam in _FAMILIES
                }
            else:
                scope = None
            issues: list[ValidationIssue] = []
            if rng.random() < 0.35:
                sid = rng.choice(sources)
                fam = rng.choice(_FAMILIES)
                issues.append(_rand_issue(sid, fam))
            cov = build_check_coverage(
                source_ids=sources, issues=issues, capabilities=caps, scope=scope
            )
            for row in cov.rows:
                for family, status in row.families:
                    op = operator_status_for(status)
                    if op == "no_findings":
                        self.assertIs(
                            status,
                            CoverageStatus.CHECKED_OK,
                            f"no_findings requires CHECKED_OK, got {status} for "
                            f"{row.source_id}/{family}",
                        )
                    if status is not CoverageStatus.CHECKED_OK:
                        self.assertNotEqual(
                            op,
                            "no_findings",
                            f"no_findings on non-OK status {status}",
                        )
                    if status is CoverageStatus.CHECKED_OK:
                        self.assertEqual(op, "no_findings")
                        self.assertEqual(presentation_status_for(status), "no_findings")

    def test_tz_gaps_are_always_not_checked(self) -> None:
        from aerobim.domain.check_coverage import tz_gap_rows_for_report

        rows = tz_gap_rows_for_report()
        self.assertEqual(len(rows), 4)
        for row in rows:
            self.assertEqual(row["status"], "not_checked")
            self.assertTrue(str(row.get("reason") or "").strip())
