"""Agent-bus comments and CI attestation stay outside the verdict path."""

from __future__ import annotations

import unittest

from aerobim.tools.agent_bus import (
    SCHEMA,
    BusError,
    first_claim,
    parse_messages,
    run_failure_reason,
    validate_object,
)

_SHA = "bfe69cd5a1b2c3d4e5f60718293a4b5c6d7e8f90"
_CLAIM = {
    "schema": SCHEMA,
    "op": "claim",
    "issue": 12,
    "agent": "local-session",
    "host": "local",
    "base_sha": _SHA[:12],
    "branch": "feat/12-bus",
    "until": "2026-09-24T14:00:00+03:00",
}


def _comment(payload: dict[str, object]) -> str:
    import json

    return f"### AGENT_BUS {SCHEMA}\n```json\n{json.dumps(payload)}\n```\n"


def _job(name: str, *, runner_id: int = 7, steps: list[str] | None = None) -> dict[str, object]:
    return {
        "name": name,
        "conclusion": "success",
        "runner_id": runner_id,
        "runner_name": "github-hosted",
        "steps": ["checkout"] if steps is None else steps,
    }


def _run(**overrides: object) -> dict[str, object]:
    from aerobim.tools.agent_bus import REQUIRED_CI_JOBS

    payload: dict[str, object] = {
        "status": "completed",
        "conclusion": "success",
        "jobs": [_job(name) for name in REQUIRED_CI_JOBS],
    }
    payload.update(overrides)
    return payload


class AgentBusTests(unittest.TestCase):
    def test_first_claim_wins(self) -> None:
        later = dict(_CLAIM)
        later["agent"] = "other-session"
        winner = first_claim([_comment(_CLAIM), _comment(later)])
        self.assertIsNotNone(winner)
        assert winner is not None
        self.assertEqual(winner.agent, "local-session")

    def test_done_requires_a_real_run_url(self) -> None:
        raw = {
            "schema": SCHEMA,
            "op": "done",
            "issue": 12,
            "agent": "local-session",
            "sha": _SHA[:12],
            "pr_url": "https://github.com/KonkovDV/AeroBIM/pull/12",
            "ci_run_id": "https://github.com/KonkovDV/AeroBIM/actions/runs/1",
            "test_quality_gate": ["calls the production function"],
        }
        self.assertEqual(validate_object(raw).op, "done")
        raw["ci_run_id"] = "https://example.invalid/runs/1"
        with self.assertRaises(BusError):
            validate_object(raw)

    def test_bus_does_not_carry_a_verdict(self) -> None:
        raw = dict(_CLAIM)
        raw["summary_passed"] = True
        with self.assertRaises(BusError):
            validate_object(raw)
        raw = dict(_CLAIM)
        raw["customer_go"] = True
        with self.assertRaises(BusError):
            validate_object(raw)

    def test_steal_requires_silence_and_no_commits(self) -> None:
        raw = {
            "schema": SCHEMA,
            "op": "steal",
            "issue": 12,
            "agent": "local-session",
            "branch": "feat/12-bus",
            "stale_heartbeat_hours": 6,
            "branch_commits_since_claim": 0,
        }
        self.assertEqual(validate_object(raw).op, "steal")
        raw["branch_commits_since_claim"] = 1
        with self.assertRaises(BusError):
            validate_object(raw)

    def test_foreign_schema_is_rejected(self) -> None:
        raw = dict(_CLAIM)
        raw["schema"] = "kontur.agent_bus.v2"
        with self.assertRaises(BusError):
            validate_object(raw)

    def test_zero_runner_is_not_a_green_run(self) -> None:
        jobs = _run()["jobs"]
        assert isinstance(jobs, list)
        jobs[0] = _job("lint", runner_id=0)
        self.assertEqual(run_failure_reason(_run(jobs=jobs)), "lint has no runner")
        jobs[0] = _job("lint", steps=[])
        self.assertEqual(run_failure_reason(_run(jobs=jobs)), "lint has no steps")

    def test_nested_json_stays_intact(self) -> None:
        raw = dict(_CLAIM)
        raw["note"] = {"left": "panel", "count": 2}
        parsed = parse_messages(_comment(raw))
        self.assertEqual(parsed[0].fields["note"], {"left": "panel", "count": 2})

    def test_heading_without_json_fails(self) -> None:
        with self.assertRaises(BusError):
            parse_messages(f"### AGENT_BUS {SCHEMA}\n")

    def test_main_branch_is_not_a_claim_branch(self) -> None:
        raw = dict(_CLAIM)
        raw["branch"] = "main"
        with self.assertRaises(BusError):
            validate_object(raw)
