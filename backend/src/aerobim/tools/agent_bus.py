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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import unquote

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
_GATE_KEYS = frozenset(
    {
        "customer_go",
        "market_go",
        "deployment_go",
        "closes_rt001",
        "closes_rt002",
        "closes_rt003",
        "precision_claim_publishable",
        "mep_delivered",
    }
)
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
    _reject_gates(raw)
    issue = raw.get("issue")
    agent = raw.get("agent")
    if not isinstance(issue, int) or isinstance(issue, bool) or issue < 1:
        raise BusError("issue must be a positive integer")
    if not isinstance(agent, str) or not agent.strip() or len(agent) > 64:
        raise BusError("agent must be a short name")
    _require_op(op, raw)
    return BusMessage(op=str(op), issue=issue, agent=agent.strip(), fields=dict(raw))


def first_claim(texts: Sequence[str]) -> BusMessage | None:
    """First claim in caller order. The lease and the clock are ``inspect_thread``."""
    for text in texts:
        for message in parse_messages(text):
            if message.op == "claim":
                return message
    return None


def run_failure_reason(payload: Mapping[str, Any]) -> str | None:
    """None when the payload is a real green run.

    ``runner_id`` comes from the Actions jobs API. ``gh run view --json jobs``
    leaves ``runnerId`` null on a hosted runner, so that view is not evidence.
    """
    if payload.get("status") != "completed" or payload.get("conclusion") != "success":
        return "run is not completed success"
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        return "run has no jobs"
    by_name: dict[str, Mapping[str, Any]] = {}
    for job in jobs:
        if not isinstance(job, dict) or not job.get("name"):
            continue
        by_name[str(job["name"])] = job
        if job.get("conclusion") == "success" and _explicit_zero_runner(job):
            return f"{job['name']} has no runner"
    total = payload.get("total_count")
    if isinstance(total, int) and not isinstance(total, bool) and total != len(jobs):
        return "jobs list is incomplete"
    reason = _same_run(payload, jobs)
    if reason is not None:
        return reason
    for name in REQUIRED_CI_JOBS:
        job = by_name.get(name)
        if job is None:
            return f"missing job {name}"
        if job.get("conclusion") != "success":
            return f"{name} is not success"
        reason = _runner_reason(name, job)
        if reason is not None:
            return reason
        if not _steps_ran(job.get("steps")):
            return f"{name} has no steps"
    return None


@dataclass(frozen=True)
class _Comment:
    at: datetime
    body: str


def inspect_thread(
    payload: object,
    *,
    issue: int,
    now: datetime,
    run: Mapping[str, Any] | None = None,
    compare: Mapping[str, Any] | None = None,
) -> tuple[str | None, str | None]:
    """Return ``(holder, reason)``.

    ``reason`` is set when the thread contradicts itself. A declared
    ``stale_heartbeat_hours`` is not the clock. The clock is the comment
    timestamp. No live holder is ``(None, None)``, not an error.
    """
    holder: BusMessage | None = None
    seen_at: datetime | None = None
    claim_base: str | None = None
    for comment in _comments(payload):
        for message in parse_messages(comment.body):
            if message.issue != issue:
                return None, "bus comment names another issue"
            if message.op == "claim":
                if holder is not None and not _lease_over(holder, seen_at, comment.at):
                    continue
                holder = message
                seen_at = comment.at
                base_sha = message.fields.get("base_sha")
                if isinstance(base_sha, str):
                    claim_base = base_sha
            elif message.op == "heartbeat":
                if holder is None or message.agent != holder.agent:
                    return None, "heartbeat is not from the claim holder"
                seen_at = comment.at
            elif message.op == "steal":
                reason = _steal_reason(holder, seen_at, comment.at, message)
                if reason is not None:
                    return None, reason
                if compare is None:
                    return None, "steal requires check-steal"
                branch = message.fields.get("branch")
                reason = _compare_allows_steal(
                    claim_base, branch if isinstance(branch, str) else "", compare
                )
                if reason is not None:
                    return None, reason
                holder = message
                seen_at = comment.at
            elif message.op == "done":
                if holder is None or message.agent != holder.agent:
                    return None, "done is not from the claim holder"
                if run is None:
                    return None, "done requires check-done"
                reason = _done_matches_run(message, run)
                if reason is not None:
                    return None, reason
                holder = None
                seen_at = None
            elif message.op == "handoff":
                if holder is None or message.agent != holder.agent:
                    return None, "handoff is not from the claim holder"
                holder = None
                seen_at = None
            elif holder is None or message.agent != holder.agent:
                return None, f"{message.op} is not from the claim holder"
    if holder is None or _lease_over(holder, seen_at, now):
        return None, None
    return holder.agent, None


def _reject_gates(raw: object) -> None:
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            if key in {"summary_passed", "summary.passed"}:
                raise BusError("the bus does not carry summary.passed")
            if key in _GATE_KEYS and _truthy_gate(value):
                raise BusError("the bus does not set a product gate")
            if (
                key == "cde_import"
                and isinstance(value, str)
                and value.strip().upper() == "VERIFIED"
            ):
                raise BusError("the bus does not set a product gate")
            _reject_gates(value)
    elif isinstance(raw, list):
        for item in raw:
            _reject_gates(item)


def _truthy_gate(value: object) -> bool:
    if value is True or value == 1:
        return True
    return isinstance(value, str) and value.strip().lower() == "true"


def _explicit_zero_runner(job: Mapping[str, Any]) -> bool:
    runner_id, _name = _runner_fields(job)
    return isinstance(runner_id, int) and not isinstance(runner_id, bool) and runner_id == 0


def _runner_reason(name: str, job: Mapping[str, Any]) -> str | None:
    runner_id, runner_name = _runner_fields(job)
    if "runner_id" not in job and job.get("runnerId") is None:
        return f"{name} has no runner_id; pass the Actions jobs API payload"
    if not isinstance(runner_id, int) or isinstance(runner_id, bool) or runner_id == 0:
        return f"{name} has no runner"
    if not isinstance(runner_name, str) or not runner_name.strip():
        return f"{name} has no runner name"
    return None


def _runner_fields(job: Mapping[str, Any]) -> tuple[object, object]:
    if "runner_id" in job or "runner_name" in job:
        return job.get("runner_id"), job.get("runner_name")
    return job.get("runnerId"), job.get("runnerName")


def _steps_ran(steps: object) -> bool:
    if not isinstance(steps, list):
        return False
    return any(isinstance(step, dict) and step.get("conclusion") == "success" for step in steps)


def _same_run(payload: Mapping[str, Any], jobs: list[Any]) -> str | None:
    run_id = payload.get("id")
    head = payload.get("head_sha")
    job_ids: set[object] = set()
    heads: set[object] = set()
    for job in jobs:
        if not isinstance(job, dict):
            continue
        if "run_id" in job:
            job_ids.add(job.get("run_id"))
        if isinstance(job.get("head_sha"), str):
            heads.add(job.get("head_sha"))
    if isinstance(run_id, int) and not isinstance(run_id, bool) and job_ids and job_ids != {run_id}:
        return "jobs are from another run"
    if len(job_ids) > 1:
        return "jobs are from another run"
    if isinstance(head, str) and heads and heads != {head}:
        return "jobs are from another sha"
    return None


def _done_matches_run(message: BusMessage, run: Mapping[str, Any]) -> str | None:
    reason = run_failure_reason(run)
    if reason is not None:
        return reason
    cited = int(str(message.fields["ci_run_id"]).rsplit("/", 1)[-1])
    run_id = run.get("id")
    jobs = run.get("jobs")
    rows = jobs if isinstance(jobs, list) else []
    job_ids = {job.get("run_id") for job in rows if isinstance(job, dict) and "run_id" in job}
    if isinstance(run_id, int) and not isinstance(run_id, bool) and run_id != cited:
        return "done cites a different run"
    if job_ids and job_ids != {cited}:
        return "done cites a different run"
    if not isinstance(run_id, int) or isinstance(run_id, bool):
        if not job_ids:
            return "run payload has no id"
    head = run.get("head_sha")
    sha = message.fields.get("sha")
    if not isinstance(head, str) or not isinstance(sha, str) or not head.startswith(sha):
        return "done sha is not the run head"
    return None


def _comments(payload: object) -> list[_Comment]:
    rows: object = payload
    if isinstance(payload, Mapping):
        rows = payload.get("comments")
    if isinstance(payload, str) or not isinstance(rows, list):
        raise BusError("comment payload must be a list of timestamped comments")
    comments: list[_Comment] = []
    for item in rows:
        if not isinstance(item, dict):
            raise BusError("comment must be an object")
        body = item.get("body")
        stamp = item.get("createdAt", item.get("created_at"))
        if not isinstance(body, str) or not isinstance(stamp, str):
            raise BusError("every comment needs a body and a timestamp")
        comments.append(_Comment(_parse_time(stamp), body))
    comments.sort(key=lambda comment: comment.at)
    return comments


def _lease_over(holder: BusMessage, seen_at: datetime | None, event_at: datetime | None) -> bool:
    if event_at is None or seen_at is None:
        return False
    if event_at - seen_at >= timedelta(hours=STEAL_AFTER_HOURS):
        return True
    until_raw = holder.fields.get("until") if holder.op == "claim" else None
    if not isinstance(until_raw, str):
        return False
    until = _parse_time(until_raw)
    return event_at > until and seen_at <= until


def _steal_reason(
    holder: BusMessage | None,
    seen_at: datetime | None,
    event_at: datetime | None,
    message: BusMessage,
) -> str | None:
    if event_at is None or seen_at is None:
        return "steal requires comment timestamps"
    if holder is None:
        return "steal requires a claim"
    if message.agent == holder.agent:
        return "steal requires another agent"
    held_branch = holder.fields.get("branch")
    if isinstance(held_branch, str) and message.fields.get("branch") != held_branch:
        return "steal must stay on the claimed branch"
    if event_at - seen_at < timedelta(hours=STEAL_AFTER_HOURS):
        return "steal requires a heartbeat gap of at least 6 hours"
    return None


def _compare_allows_steal(
    base_sha: str | None, branch: str, compare: Mapping[str, Any]
) -> str | None:
    """The declared commit count is not evidence. The compare API is."""
    ahead = compare.get("ahead_by")
    total = compare.get("total_commits")
    commits = compare.get("commits")
    if (
        isinstance(ahead, bool)
        or isinstance(total, bool)
        or ahead != 0
        or total != 0
        or (isinstance(commits, list) and commits)
    ):
        return "claimed branch has commits"
    base = compare.get("base_commit")
    got = base.get("sha") if isinstance(base, dict) else None
    if not isinstance(base_sha, str) or not isinstance(got, str) or not got.startswith(base_sha):
        return "compare base is not the claim base"
    html = compare.get("html_url")
    if not isinstance(html, str) or not _compare_head_is(html, branch):
        return "compare head is not the claimed branch"
    return None


def _compare_head_is(html: str, branch: str) -> bool:
    prefix = "https://github.com/KonkovDV/AeroBIM/compare/"
    if not html.startswith(prefix) or "..." not in html:
        return False
    head = unquote(html.split("...", 1)[1].split("?", 1)[0].split("#", 1)[0])
    return head == branch


def _parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BusError("timestamp must include a timezone") from exc
    if parsed.tzinfo is None:
        raise BusError("timestamp must include a timezone")
    return parsed


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
    if not isinstance(value, str) or ".." in value or _BRANCH.fullmatch(value) is None:
        raise BusError("branch must be a feature branch")
    bare = value
    changed = True
    while changed:
        changed = False
        for prefix in ("refs/heads/", "origin/"):
            if bare.startswith(prefix):
                bare = bare[len(prefix) :]
                changed = True
    if bare in {"main", "master"}:
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


def _merged_run(path: str, jobs_path: str | None) -> dict[str, Any]:
    payload = dict(_read_json(path))
    if not jobs_path:
        return payload
    jobs_doc = _read_json(jobs_path)
    jobs = jobs_doc.get("jobs")
    if not isinstance(jobs, list):
        raise BusError("jobs file has no jobs")
    payload["jobs"] = jobs
    if "total_count" in jobs_doc:
        payload["total_count"] = jobs_doc["total_count"]
    return payload


def _read_text(path: str) -> str:
    raw = Path(path).read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise BusError("file is not utf-8 text") from exc


def _read_json(path: str) -> Mapping[str, Any]:
    try:
        raw = json.loads(_read_text(path))
    except json.JSONDecodeError as exc:
        raise BusError("json is not valid") from exc
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
    run.add_argument("jobs", nargs="?")
    thread = sub.add_parser("check-thread")
    thread.add_argument("issue", type=int)
    thread.add_argument("path")
    done = sub.add_parser("check-done")
    done.add_argument("issue", type=int)
    done.add_argument("path")
    done.add_argument("run")
    done.add_argument("jobs", nargs="?")
    steal = sub.add_parser("check-steal")
    steal.add_argument("issue", type=int)
    steal.add_argument("path")
    steal.add_argument("compare")
    args = parser.parse_args(argv)
    try:
        if args.command == "check-comment":
            messages = parse_messages(_read_text(args.path))
            if not messages:
                raise BusError("no AGENT_BUS comment")
            print(f"{len(messages)} bus message(s)")
        elif args.command in {"check-thread", "check-done", "check-steal"}:
            run_payload = _merged_run(args.run, args.jobs) if args.command == "check-done" else None
            compare_payload = _read_json(args.compare) if args.command == "check-steal" else None
            holder, reason = inspect_thread(
                _read_json(args.path),
                issue=args.issue,
                now=datetime.now().astimezone(),
                run=run_payload,
                compare=compare_payload,
            )
            if reason is not None:
                raise BusError(reason)
            if args.command == "check-done" and holder is None:
                print("done attested")
            else:
                print("no holder" if holder is None else holder)
        else:
            reason = run_failure_reason(_merged_run(args.path, args.jobs))
            if reason is not None:
                raise BusError(reason)
            print("run attested")
    except (OSError, BusError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
