"""Exchange contract: required keys stay, and a decision does not pass the pack."""

from __future__ import annotations

import unittest

from aerobim.domain.exchange_contract import (
    DECISION_REQUIRED,
    FINDING_REQUIRED,
    contract_gaps,
    decision_exchange,
    finding_exchange,
)
from aerobim.domain.finding_lifecycle import ReviewAction
from aerobim.domain.models import Severity, ValidationIssue


class ExchangeContractTests(unittest.TestCase):
    def test_required_keys_are_frozen(self) -> None:
        self.assertEqual(
            FINDING_REQUIRED,
            frozenset(
                {
                    "schema_version",
                    "finding_id",
                    "rule_id",
                    "severity",
                    "origin",
                    "evidence_refs",
                    "message",
                    "writes_summary_passed",
                }
            ),
        )
        self.assertEqual(
            DECISION_REQUIRED,
            frozenset(
                {
                    "schema_version",
                    "finding_id",
                    "action",
                    "actor",
                    "note",
                    "writes_summary_passed",
                }
            ),
        )

    def test_finding_carries_every_required_key(self) -> None:
        issue = ValidationIssue(
            rule_id="R1",
            severity=Severity.ERROR,
            message="wall",
            finding_id="f-1",
            evidence_refs=("sheet:1",),
            origin="deterministic",
        )
        record = finding_exchange(issue)
        self.assertEqual(contract_gaps(record, FINDING_REQUIRED), frozenset())
        self.assertFalse(record["writes_summary_passed"])
        broken = dict(record)
        del broken["evidence_refs"]
        self.assertEqual(contract_gaps(broken, FINDING_REQUIRED), frozenset({"evidence_refs"}))

    def test_empty_evidence_and_bare_refusal_are_rejected(self) -> None:
        bare = ValidationIssue(
            rule_id="R1",
            severity=Severity.ERROR,
            message="wall",
            finding_id="f-1",
        )
        with self.assertRaises(ValueError):
            finding_exchange(bare)
        with self.assertRaises(ValueError):
            decision_exchange(
                finding_id="f-1",
                action=ReviewAction.FALSE_POSITIVE,
                actor="reviewer",
            )
        kept = decision_exchange(
            finding_id="f-1",
            action=ReviewAction.FALSE_POSITIVE,
            actor="reviewer",
            note="not this wall",
        )
        self.assertFalse(kept["writes_summary_passed"])
        self.assertEqual(contract_gaps(kept, DECISION_REQUIRED), frozenset())
