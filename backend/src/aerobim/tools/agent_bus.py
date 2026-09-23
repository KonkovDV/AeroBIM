"""GitHub issue bus for parallel work sessions.

One JSON comment on an issue is the queue. Code changes only through a
pull request. A green check is a completed run whose required jobs have a
real runner. This module does not write a verdict and does not call GitHub.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

SCHEMA = "aerobim.agent_bus.v1"
OPS = frozenset({"claim", "heartbeat", "blocked", "handoff", "steal", "done"})
HOSTS = frozenset({"local", "cloud"})
REQUIRED_CI_JOBS = (
    "lint",
    "typecheck",
    "test",
    "pytest-readme-extras",
    "frontend",
    "baseline-integrity",
)
STEAL_AFTER_HOURS = 6

_HEADING = re.compile(r"^### AGENT_BUS\s+aerobim\.agent_bus\.v1\s*$", re.MULTILINE)
_SHA = re.compile(r"^[0-9a-f]{7,40}$")
_BRANCH = re.compile(r"^[A-Za-z0-9._/-]{1,80}$")
_RUN_URL = re.compile(r"^https://github\.com/KonkovDV/AeroBIM/actions/runs/\d+$")
_PR_URL = re.compile(r"^https://github\.com/KonkovDV/AeroBIM/pull/\d+$")


class BusError(ValueError):
    """A comment or CI payload does not match the bus."""


@dataclass(frozen=True)
class BusMessage:
    op: str
    issue: int
    agent: str
    fields: Mapping[str, Any]


def _object_after_heading(section: str) -> dict[str, Any]:
    marker = section.find("```json")
    if marker < 0:
        raise BusError("AGENT_BUS heading has no json block")
    body_at = section.find("\n", marker)
    if body_at < 0:
        raise BusError("AGENT_BUS heading has no json block")
    try:
        raw, _end = json.JSONDecoder().raw_decode(section[body_at + 1 :].lstrip())
    except json.JSONDecodeError as exc:
        raise BusError("AGENT_BUS json is not valid") from exc
    if not isinstance(raw, dict):
        raise BusError("AGENT_BUS json must be an object")
    return raw


def parse_messages(text: str) -> list[BusMessage]:
    """Return bus messages in file order. Other text is ignored."""
    messages: list[BusMessage] = []
    headings = list(_HEADING.finditer(text))
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        messages.append(validate_object(_object_after_heading(text[match.end() : end])))
    return messages


def validate_object(raw: Mapping[str, Any]) -> BusMessage:
    if raw.get("schema") != SCHEMA:
        raise BusError(f"schema must be {SCHEMA}")
    op = raw.get("op")
    if op not in OPS:
        raise BusError("op is not a bus operation")
    if "summary_passed" in raw:
        raise BusError("the bus does not carry summary.passed")
    if raw.get("customer_go") is True:
        raise BusError("the bus does not set customer_go")
    issue = raw.get("issue")
    agent = raw.get("agent")
    if not isinstance(issue, int) or isinstance(issue, bool) or issue < 1:
        raise BusError("issue must be a positive integer")
    if not isinstance(agent, str) or not agent.strip() or len(agent) > 64:
        raise BusError("agent must be a short name")
    _require_op(op, raw)
    return BusMessage(op=str(op), issue=issue, agent=agent.strip(), fields=dict(raw))


def first_claim(texts: Sequence[str]) -> BusMessage | None:
    """The earliest valid claim wins. A later claim does not replace it."""
    for text in texts:
        for message in parse_messages(text):
            if message.op == "claim":
                return message
    return None


def run_failure_reason(payload: Mapping[str, Any]) -> str | None:
    """None when the Actions payload is a real green run."""
    if payload.get("status") != "completed" or payload.get("conclusion") != "success":
        return "run is not completed success"
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        return "run has no jobs"
    by_name = {
        str(job.get("name")): job for job in jobs if isinstance(job, dict) and job.get("name")
    }
    for name in REQUIRED_CI_JOBS:
        job = by_name.get(name)
        if not isinstance(job, dict):
            return f"missing job {name}"
        if job.get("conclusion") != "success":
            return f"{name} is not success"
        runner_id = job.get("runner_id")
        if not isinstance(runner_id, int) or isinstance(runner_id, bool) or runner_id == 0:
            return f"{name} has no runner"
        runner_name = job.get("runner_name")
        if not isinstance(runner_name, str) or not runner_name.strip():
            return f"{name} has no runner name"
        steps = job.get("steps")
        if not isinstance(steps, list) or not steps:
            return f"{name} has no steps"
    return None


def _require_op(op: str, raw: Mapping[str, Any]) -> None:
    if op == "claim":
        _host(raw)
        _sha(raw, "base_sha")
        _branch(raw)
        _until(raw)
    elif op == "heartbeat":
        _branch(raw)
    elif op == "blocked":
        _text(raw, "reason")
        blocked = raw.get("blocked_by")
        if (
            not isinstance(blocked, list)
            or not blocked
            or any(
                not isinstance(item, int) or isinstance(item, bool) or item < 1 for item in blocked
            )
        ):
            raise BusError("blocked_by must be issue numbers")
    elif op == "handoff":
        _sha(raw, "sha")
        _url(raw, "pr_url", _PR_URL)
        _text(raw, "done_note")
        _text(raw, "left_note")
    elif op == "steal":
        _branch(raw)
        hours = raw.get("stale_heartbeat_hours")
        commits = raw.get("branch_commits_since_claim")
        if not isinstance(hours, int) or isinstance(hours, bool) or hours < STEAL_AFTER_HOURS:
            raise BusError("steal requires a heartbeat gap of at least 6 hours")
        if commits != 0:
            raise BusError("steal requires no commits on the claimed branch")
    elif op == "done":
        _sha(raw, "sha")
        _url(raw, "pr_url", _PR_URL)
        _url(raw, "ci_run_id", _RUN_URL)
        gate = raw.get("test_quality_gate")
        if (
            not isinstance(gate, list)
            or not gate
            or any(not isinstance(item, str) or not item.strip() for item in gate)
        ):
            raise BusError("done requires a test quality gate")


def _host(raw: Mapping[str, Any]) -> None:
    if raw.get("host") not in HOSTS:
        raise BusError("host must be local or cloud")


def _sha(raw: Mapping[str, Any], key: str) -> None:
    value = raw.get(key)
    if not isinstance(value, str) or _SHA.fullmatch(value) is None:
        raise BusError(f"{key} must be a git sha")


def _branch(raw: Mapping[str, Any]) -> None:
    value = raw.get("branch")
    if (
        not isinstance(value, str)
        or value in {"main", "master"}
        or _BRANCH.fullmatch(value) is None
    ):
        raise BusError("branch must be a feature branch")


def _until(raw: Mapping[str, Any]) -> None:
    value = raw.get("until")
    if not isinstance(value, str):
        raise BusError("until must be a timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise BusError("until must be a timestamp") from exc
    if parsed.tzinfo is None:
        raise BusError("until must include a timezone")


def _text(raw: Mapping[str, Any], key: str) -> None:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BusError(f"{key} is required")


def _url(raw: Mapping[str, Any], key: str, pattern: re.Pattern[str]) -> None:
    value = raw.get(key)
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise BusError(f"{key} must be an AeroBIM URL")


def _read_json(path: str) -> Mapping[str, Any]:
    with open(path, encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise BusError("json must be an object")
    return raw


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check an AeroBIM agent-bus comment or CI run")
    sub = parser.add_subparsers(dest="command", required=True)
    comment = sub.add_parser("check-comment")
    comment.add_argument("path")
    run = sub.add_parser("check-run")
    run.add_argument("path")
    args = parser.parse_args(argv)
    try:
        if args.command == "check-comment":
            text = open(args.path, encoding="utf-8").read()
            messages = parse_messages(text)
            if not messages:
                raise BusError("no AGENT_BUS comment")
            print(f"{len(messages)} bus message(s)")
        else:
            reason = run_failure_reason(_read_json(args.path))
            if reason is not None:
                raise BusError(reason)
            print("run attested")
    except (OSError, json.JSONDecodeError, BusError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
