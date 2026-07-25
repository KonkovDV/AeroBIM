"""H1.1 mutation-kill tests for domain/review_state_machine.py.

The transition matrix below is an independent oracle: it re-states the
RT-HYPER lifecycle contract from the module docstring by hand instead of
importing ``_ALLOWED_TRANSITIONS``, so table mutations cannot survive by
mutating both sides at once.

Survivor triage of the final cosmic-ray run (tests/mutation/review_state_machine.toml,
195 mutants = 21 non-viable syntax + 82 killed + 92 survived, 0 live gaps):

* 88x ``ReplaceBinaryOperator_BitOr_*`` on ``str | None`` annotations —
  never evaluated (``from __future__ import annotations``).
* 3x L120/L152 ``!=``/``==`` -> ``is not``/``is`` against state literals —
  equivalent in CPython: both operands are compile-time constants of the same
  module, hence the same interned object.
* 1x L141 ``*`` keyword-only marker mutant — calling-convention only.

Effective mutation score (equivalents excluded): 82/82 = 1.0 ≥ 0.85 target.
The first run's live gaps are killed by ``LatestHitlStateOrderTests`` below
(scan-order ``continue`` -> ``break`` and id-comparison operator mutants).
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass

from aerobim.domain.review_state_machine import (
    HITL_REVIEW_STATES,
    HitlTransitionError,
    assert_hitl_transition,
    latest_hitl_state,
    normalize_hitl_state,
)

# Independent re-statement of the lifecycle contract (do not import the table).
EXPECTED_ALLOWED: dict[str, set[str]] = {
    "escalated": {"opened", "superseded"},
    "opened": {"accepted", "rejected", "edited", "waived", "superseded"},
    "edited": {"accepted", "rejected", "waived", "opened", "superseded"},
    "accepted": {"superseded"},
    "rejected": {"opened", "superseded"},
    "waived": {"superseded"},
    "superseded": set(),
}

EXPECTED_EVENT_TO_STATE: dict[str, str] = {
    "drawing_region_escalated": "escalated",
    "escalated": "escalated",
    "opened": "opened",
    "triaged": "opened",
    "accepted": "accepted",
    "rejected": "rejected",
    "edited": "edited",
    "edited_remark": "edited",
    "waived": "waived",
    "superseded": "superseded",
}

# Valid actor/note payload per target state so matrix tests only probe transitions.
_ACTOR_NOTE: dict[str, dict[str, str]] = {
    "accepted": {"actor": "expert-1"},
    "rejected": {"actor": "expert-1", "note": "reason"},
    "edited": {"actor": "expert-1", "note": "diff"},
    "waived": {"actor": "expert-1", "note": "reason"},
    "opened": {},
    "escalated": {},
    "superseded": {},
}


class TransitionMatrixTests(unittest.TestCase):
    """Exhaustive matrix: every (current, target) pair checked both ways."""

    def test_full_transition_matrix(self) -> None:
        for current in sorted(HITL_REVIEW_STATES):
            for target in sorted(HITL_REVIEW_STATES):
                kwargs = _ACTOR_NOTE[target]
                with self.subTest(current=current, target=target):
                    if target in EXPECTED_ALLOWED[current]:
                        self.assertEqual(
                            assert_hitl_transition(current=current, event_type=target, **kwargs),
                            target,
                        )
                    else:
                        with self.assertRaises(HitlTransitionError):
                            assert_hitl_transition(current=current, event_type=target, **kwargs)

    def test_initial_state_only_escalated_or_opened(self) -> None:
        for target in sorted(HITL_REVIEW_STATES):
            kwargs = _ACTOR_NOTE[target]
            with self.subTest(target=target):
                if target in {"escalated", "opened"}:
                    self.assertEqual(
                        assert_hitl_transition(current=None, event_type=target, **kwargs),
                        target,
                    )
                else:
                    with self.assertRaises(HitlTransitionError):
                        assert_hitl_transition(current=None, event_type=target, **kwargs)

    def test_accepted_to_opened_is_forbidden_but_rejected_to_opened_allowed(self) -> None:
        with self.assertRaises(HitlTransitionError):
            assert_hitl_transition(current="accepted", event_type="opened")
        self.assertEqual(assert_hitl_transition(current="rejected", event_type="opened"), "opened")

    def test_legacy_event_type_current_state_is_normalized(self) -> None:
        # current="triaged" (legacy) must behave exactly like current="opened".
        self.assertEqual(
            assert_hitl_transition(current="triaged", event_type="accepted", actor="expert-1"),
            "accepted",
        )

    def test_unknown_current_state_fails_closed(self) -> None:
        with self.assertRaises(HitlTransitionError):
            assert_hitl_transition(current="nonsense", event_type="opened")


class EventNormalizationTests(unittest.TestCase):
    def test_every_legacy_event_maps_to_expected_state(self) -> None:
        for event_type, state in EXPECTED_EVENT_TO_STATE.items():
            with self.subTest(event_type=event_type):
                self.assertEqual(normalize_hitl_state(event_type), state)

    def test_unknown_event_type_raises(self) -> None:
        with self.assertRaises(HitlTransitionError):
            normalize_hitl_state("promoted")


class ActorRuleTests(unittest.TestCase):
    def test_expert_decisions_require_actor(self) -> None:
        for event_type in ("accepted", "rejected", "edited", "waived"):
            with self.subTest(event_type=event_type):
                with self.assertRaises(HitlTransitionError):
                    assert_hitl_transition(
                        current="opened",
                        event_type=event_type,
                        actor="   ",
                        note="reason",
                    )

    def test_rejected_waived_edited_require_note(self) -> None:
        for event_type in ("rejected", "waived", "edited"):
            with self.subTest(event_type=event_type):
                with self.assertRaises(HitlTransitionError):
                    assert_hitl_transition(
                        current="opened",
                        event_type=event_type,
                        actor="expert-1",
                        note="  ",
                    )

    def test_accepted_needs_no_note(self) -> None:
        self.assertEqual(
            assert_hitl_transition(current="opened", event_type="accepted", actor="x"),
            "accepted",
        )

    def test_system_actor_cannot_make_expert_decisions(self) -> None:
        for event_type in ("accepted", "rejected", "edited", "waived"):
            for actor in ("system", "System", "SYSTEM"):
                with self.subTest(event_type=event_type, actor=actor):
                    with self.assertRaises(HitlTransitionError):
                        assert_hitl_transition(
                            current="opened",
                            event_type=event_type,
                            actor=actor,
                            note="reason",
                        )

    def test_system_actor_may_supersede(self) -> None:
        self.assertEqual(
            assert_hitl_transition(current="opened", event_type="superseded", actor="system"),
            "superseded",
        )


@dataclass
class _Event:
    event_type: str
    finding_id: str | None = None
    issue_rule_id: str | None = None
    resulting_state: str | None = None


class LatestHitlStateTests(unittest.TestCase):
    def test_last_matching_state_wins(self) -> None:
        events = [
            _Event("opened", finding_id="f1", resulting_state="opened"),
            _Event("accepted", finding_id="f1", resulting_state="accepted"),
        ]
        self.assertEqual(latest_hitl_state(events, "f1", None), "accepted")

    def test_norm_pack_events_are_ignored(self) -> None:
        events = [
            _Event("opened", finding_id="f1", resulting_state="opened"),
            _Event("norm_rule_proposed", finding_id="f1", resulting_state="accepted"),
            _Event("norm_rule_edited", finding_id="f1", resulting_state="waived"),
        ]
        self.assertEqual(latest_hitl_state(events, "f1", None), "opened")

    def test_finding_id_filter_excludes_other_findings(self) -> None:
        events = [
            _Event("opened", finding_id="f1", resulting_state="opened"),
            _Event("accepted", finding_id="f2", resulting_state="accepted"),
        ]
        self.assertEqual(latest_hitl_state(events, "f1", None), "opened")

    def test_rule_id_used_only_without_finding_id(self) -> None:
        events = [
            _Event("opened", issue_rule_id="R-1", resulting_state="opened"),
            _Event("accepted", issue_rule_id="R-2", resulting_state="accepted"),
        ]
        self.assertEqual(latest_hitl_state(events, None, "R-1"), "opened")

    def test_blank_identifiers_treated_as_none(self) -> None:
        events = [
            _Event("opened", finding_id="f1", resulting_state="opened"),
        ]
        # Blank finding_id must fall back to rule matching (here: no filter → match).
        self.assertEqual(latest_hitl_state(events, "   ", None), "opened")

    def test_empty_resulting_state_does_not_override(self) -> None:
        events = [
            _Event("opened", finding_id="f1", resulting_state="opened"),
            _Event("edited", finding_id="f1", resulting_state="   "),
        ]
        self.assertEqual(latest_hitl_state(events, "f1", None), "opened")

    def test_no_events_returns_none(self) -> None:
        self.assertIsNone(latest_hitl_state([], "f1", None))


class LatestHitlStateOrderTests(unittest.TestCase):
    """Scan-order and comparison-operator kills for latest_hitl_state."""

    def test_norm_pack_event_before_match_does_not_stop_scan(self) -> None:
        """Kills ``continue`` -> ``break`` on the norm-pack skip (L80)."""
        events = [
            _Event("norm_rule_proposed", finding_id="f1", resulting_state="accepted"),
            _Event("opened", finding_id="f1", resulting_state="opened"),
        ]
        self.assertEqual(latest_hitl_state(events, "f1", None), "opened")

    def test_foreign_finding_before_match_does_not_stop_scan(self) -> None:
        """Kills ``continue`` -> ``break`` on the finding filter (L85)."""
        events = [
            _Event("accepted", finding_id="other", resulting_state="accepted"),
            _Event("opened", finding_id="f1", resulting_state="opened"),
        ]
        self.assertEqual(latest_hitl_state(events, "f1", None), "opened")

    def test_foreign_rule_before_match_does_not_stop_scan(self) -> None:
        """Kills ``continue`` -> ``break`` on the rule filter (L88)."""
        events = [
            _Event("accepted", issue_rule_id="R-other", resulting_state="accepted"),
            _Event("opened", issue_rule_id="R-1", resulting_state="opened"),
        ]
        self.assertEqual(latest_hitl_state(events, None, "R-1"), "opened")

    def test_lexicographically_smaller_foreign_ids_are_still_filtered(self) -> None:
        """Kills ``!=`` -> ``>`` on both id filters (L84/L87).

        The foreign event comes *after* the matching one and carries an id
        lexicographically smaller than the filter (``"f1" > "f2"`` is False),
        so the mutant stops skipping it and overrides the correct state.
        """
        by_finding = [
            _Event("opened", finding_id="f2", resulting_state="opened"),
            _Event("accepted", finding_id="f1", resulting_state="accepted"),
        ]
        self.assertEqual(latest_hitl_state(by_finding, "f2", None), "opened")
        by_rule = [
            _Event("opened", issue_rule_id="R-2", resulting_state="opened"),
            _Event("accepted", issue_rule_id="R-1", resulting_state="accepted"),
        ]
        self.assertEqual(latest_hitl_state(by_rule, None, "R-2"), "opened")

    def test_equal_but_not_identical_ids_match(self) -> None:
        """Kills ``!=`` -> ``is not`` on both id filters (L84/L87).

        Runtime-built strings are equal but not interned, so the identity
        mutant wrongly skips matching events.
        """
        runtime_fid = "".join(["f", "1"])
        events = [_Event("opened", finding_id="f1", resulting_state="opened")]
        self.assertEqual(latest_hitl_state(events, runtime_fid, None), "opened")
        runtime_rid = "".join(["R", "-", "1"])
        rule_events = [_Event("opened", issue_rule_id="R-1", resulting_state="opened")]
        self.assertEqual(latest_hitl_state(rule_events, None, runtime_rid), "opened")


if __name__ == "__main__":
    unittest.main()
