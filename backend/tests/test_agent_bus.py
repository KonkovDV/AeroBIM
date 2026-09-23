"""Agent-bus comments and CI attestation stay outside the verdict path."""

from __future__ import annotations

import unittest
from datetime import datetime

from aerobim.tools.agent_bus import (
    SCHEMA,
    BusError,
    first_claim,
    inspect_thread,
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
        "steps": [{"name": "checkout", "conclusion": "success"}] if steps is None else steps,
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
        raw["branch"] = "refs/heads/origin/main"
        with self.assertRaises(BusError):
            validate_object(raw)

    def test_hosted_runner_view_is_not_a_green_run(self) -> None:
        self.assertIsNone(run_failure_reason(_run()))
        jobs = _run()["jobs"]
        assert isinstance(jobs, list)
        jobs[0] = {
            "name": "lint",
            "conclusion": "success",
            "runnerId": None,
            "runnerName": None,
            "steps": [{"name": "checkout", "conclusion": "success"}],
        }
        reason = run_failure_reason(_run(jobs=jobs))
        self.assertIsNotNone(reason)
        assert reason is not None
        self.assertIn("jobs API", reason)
        jobs[0] = _job("lint", steps=["checkout"])
        self.assertEqual(run_failure_reason(_run(jobs=jobs)), "lint has no steps")

    def test_nested_product_gate_is_rejected(self) -> None:
        raw = dict(_CLAIM)
        raw["note"] = {"summary.passed": False}
        with self.assertRaises(BusError):
            validate_object(raw)
        raw = dict(_CLAIM)
        raw["customer_go"] = 1
        with self.assertRaises(BusError):
            validate_object(raw)

    def test_steal_follows_comment_time(self) -> None:
        steal = {
            "schema": SCHEMA,
            "op": "steal",
            "issue": 12,
            "agent": "other-session",
            "branch": "feat/12-bus",
            "stale_heartbeat_hours": 6,
            "branch_commits_since_claim": 0,
        }
        early = _thread(
            ("2026-09-23T08:00:00+00:00", _comment(_CLAIM)),
            ("2026-09-23T10:00:00+00:00", _comment(steal)),
        )
        now = datetime.fromisoformat("2026-09-23T10:00:00+00:00")
        _holder, reason = inspect_thread(early, issue=12, now=now)
        self.assertEqual(reason, "steal requires a heartbeat gap of at least 6 hours")
        late = _thread(
            ("2026-09-23T08:00:00+00:00", _comment(_CLAIM)),
            ("2026-09-23T15:00:00+00:00", _comment(steal)),
        )
        now = datetime.fromisoformat("2026-09-23T15:00:00+00:00")
        _holder, reason = inspect_thread(late, issue=12, now=now)
        self.assertEqual(reason, "steal requires check-steal")
        compare = _compare()
        holder, reason = inspect_thread(late, issue=12, now=now, compare=compare)
        self.assertIsNone(reason)
        self.assertEqual(holder, "other-session")
        wrong = _compare()
        wrong["html_url"] = str(wrong["html_url"]).replace("feat/12-bus", "main")
        _holder, reason = inspect_thread(late, issue=12, now=now, compare=wrong)
        self.assertEqual(reason, "compare head is not the claimed branch")
        compare["ahead_by"] = 2
        _holder, reason = inspect_thread(late, issue=12, now=now, compare=compare)
        self.assertEqual(reason, "claimed branch has commits")

    def test_expired_claim_releases_the_issue(self) -> None:
        first = dict(_CLAIM)
        first["until"] = "2026-09-23T09:00:00+00:00"
        second = dict(_CLAIM)
        second["agent"] = "other-session"
        second["until"] = "2026-09-23T18:00:00+00:00"
        payload = _thread(
            ("2026-09-23T08:00:00+00:00", _comment(first)),
            ("2026-09-23T10:00:00+00:00", _comment(second)),
        )
        holder, reason = inspect_thread(
            payload, issue=12, now=datetime.fromisoformat("2026-09-23T10:30:00+00:00")
        )
        self.assertIsNone(reason)
        self.assertEqual(holder, "other-session")
        _holder, foreign = inspect_thread(
            payload, issue=99, now=datetime.fromisoformat("2026-09-23T10:30:00+00:00")
        )
        self.assertEqual(foreign, "bus comment names another issue")

    def test_done_must_match_the_run_head(self) -> None:
        done = {
            "schema": SCHEMA,
            "op": "done",
            "issue": 12,
            "agent": "local-session",
            "sha": _SHA[:12],
            "pr_url": "https://github.com/KonkovDV/AeroBIM/pull/12",
            "ci_run_id": "https://github.com/KonkovDV/AeroBIM/actions/runs/5",
            "test_quality_gate": ["calls the production function"],
        }
        payload = _thread(
            ("2026-09-23T08:00:00+00:00", _comment(_CLAIM)),
            ("2026-09-23T09:00:00+00:00", _comment(done)),
        )
        now = datetime.fromisoformat("2026-09-23T09:00:00+00:00")
        _holder, reason = inspect_thread(payload, issue=12, now=now)
        self.assertEqual(reason, "done requires check-done")
        attested, reason = inspect_thread(payload, issue=12, now=now, run=_run(id=5, head_sha=_SHA))
        self.assertIsNone(reason)
        self.assertIsNone(attested)
        _holder, reason = inspect_thread(
            payload, issue=12, now=now, run=_run(id=5, head_sha="a" * 40)
        )
        self.assertEqual(reason, "done sha is not the run head")

    def test_jobs_from_another_run_are_rejected(self) -> None:
        self.assertEqual(run_failure_reason(_run(total_count=99)), "jobs list is incomplete")
        jobs = _run()["jobs"]
        assert isinstance(jobs, list)
        jobs[0] = {**_job("lint"), "run_id": 9}
        self.assertEqual(run_failure_reason(_run(id=5, jobs=jobs)), "jobs are from another run")
        from pathlib import Path

        path = Path("tmp-bus-utf16.json")
        path.write_bytes(b"\xff\xfe" + '{"status": "completed"}'.encode("utf-16-le"))
        try:
            from aerobim.tools.agent_bus import _read_json

            self.assertEqual(_read_json(str(path))["status"], "completed")
        finally:
            path.unlink(missing_ok=True)

    def test_steal_cannot_switch_branch(self) -> None:
        steal = {
            "schema": SCHEMA,
            "op": "steal",
            "issue": 12,
            "agent": "other-session",
            "branch": "feat/other",
            "stale_heartbeat_hours": 6,
            "branch_commits_since_claim": 0,
        }
        payload = _thread(
            ("2026-09-23T08:00:00+00:00", _comment(_CLAIM)),
            ("2026-09-23T15:00:00+00:00", _comment(steal)),
        )
        _holder, reason = inspect_thread(
            payload, issue=12, now=datetime.fromisoformat("2026-09-23T15:00:00+00:00")
        )
        self.assertEqual(reason, "steal must stay on the claimed branch")


def _thread(*pairs: tuple[str, str]) -> dict[str, list[dict[str, str]]]:
    return {"comments": [{"createdAt": at, "body": body} for at, body in pairs]}


def _compare() -> dict[str, object]:
    return {
        "ahead_by": 0,
        "total_commits": 0,
        "base_commit": {"sha": _SHA},
        "html_url": f"https://github.com/KonkovDV/AeroBIM/compare/{_SHA[:12]}...feat/12-bus",
    }
