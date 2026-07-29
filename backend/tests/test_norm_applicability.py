"""Norm-rule applicability matcher: fail-safe scope + exception decision (P3).

APPLICABLE only when the context provably matches and no exception can apply; UNKNOWN on
insufficient context (never a silent apply/skip); NOT_APPLICABLE is not 'passed'.
Verdict-neutral.
"""

from __future__ import annotations

import json
import unittest

from aerobim.domain.norm_applicability import (
    ApplicabilityException,
    ApplicabilityStatus,
    ProjectContext,
    RuleApplicability,
    evaluate_applicability,
)

_RESIDENTIAL_AR = RuleApplicability(building_types=("residential",), disciplines=("AR",))


class NormApplicabilityTests(unittest.TestCase):
    def test_applicable_when_context_matches(self) -> None:
        result = evaluate_applicability(
            _RESIDENTIAL_AR, ProjectContext(building_type="residential", discipline="AR")
        )
        self.assertEqual(result.status, ApplicabilityStatus.APPLICABLE)
        self.assertTrue(result.should_evaluate())

    def test_not_applicable_on_known_mismatch(self) -> None:
        result = evaluate_applicability(
            _RESIDENTIAL_AR, ProjectContext(building_type="commercial", discipline="AR")
        )
        self.assertEqual(result.status, ApplicabilityStatus.NOT_APPLICABLE)
        self.assertFalse(result.should_evaluate())

    def test_unknown_when_constrained_context_missing(self) -> None:
        result = evaluate_applicability(_RESIDENTIAL_AR, ProjectContext(discipline="AR"))
        self.assertEqual(result.status, ApplicabilityStatus.UNKNOWN)
        self.assertFalse(result.should_evaluate())

    def test_excluded_when_exception_matches(self) -> None:
        applicability = RuleApplicability(
            building_types=("residential",),
            exceptions=(ApplicabilityException(stages=("PD",), reason="not required at PD"),),
        )
        result = evaluate_applicability(
            applicability, ProjectContext(building_type="residential", stage="PD")
        )
        self.assertEqual(result.status, ApplicabilityStatus.EXCLUDED)
        self.assertIn("not required at PD", result.reasons)

    def test_applicable_when_exception_known_mismatch(self) -> None:
        applicability = RuleApplicability(
            building_types=("residential",),
            exceptions=(ApplicabilityException(stages=("PD",)),),
        )
        result = evaluate_applicability(
            applicability, ProjectContext(building_type="residential", stage="RD")
        )
        self.assertEqual(result.status, ApplicabilityStatus.APPLICABLE)

    def test_unknown_when_exception_indeterminate(self) -> None:
        # Base matches, but the exception's stage is unknown -> cannot rule it out -> UNKNOWN.
        applicability = RuleApplicability(
            building_types=("residential",),
            exceptions=(ApplicabilityException(stages=("PD",)),),
        )
        result = evaluate_applicability(applicability, ProjectContext(building_type="residential"))
        self.assertEqual(result.status, ApplicabilityStatus.UNKNOWN)

    def test_unconstrained_scope_is_applicable(self) -> None:
        result = evaluate_applicability(RuleApplicability(), ProjectContext())
        self.assertEqual(result.status, ApplicabilityStatus.APPLICABLE)

    def test_to_dict_verdict_neutral(self) -> None:
        record = evaluate_applicability(
            _RESIDENTIAL_AR, ProjectContext(building_type="commercial")
        ).to_dict()
        json.dumps(record)
        self.assertNotIn('"passed"', json.dumps(record))
        self.assertEqual(record["status"], "not_applicable")
        self.assertIn("not 'passed'", record["note"])


if __name__ == "__main__":
    unittest.main()
