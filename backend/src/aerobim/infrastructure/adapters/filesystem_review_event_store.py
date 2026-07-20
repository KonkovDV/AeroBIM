"""Filesystem-backed HITL review event store (W3.5).

RT-HYPER-002: corrupt JSONL lines are counted; fail-closed profiles raise.
RT-P5: idempotency_key de-dupe, sequence numbers, exclusive append lock.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict
from pathlib import Path

from aerobim.domain.models import ReviewEvent

_logger = logging.getLogger(__name__)

_MAX_LINE_BYTES = 256 * 1024
_LOCK_ATTEMPTS = 50
_LOCK_SLEEP_S = 0.02


class AuditEventCorruptionError(RuntimeError):
    """Raised when audit_fail_closed=True and JSONL contains invalid lines."""


class FilesystemReviewEventStore:
    def __init__(self, storage_dir: Path, *, fail_closed: bool = False) -> None:
        self._dir = storage_dir / "review-events"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._fail_closed = fail_closed
        self.last_invalid_line_count: int = 0
        self.last_load_degraded: bool = False

    def _path(self, report_id: str) -> Path:
        return self._dir / f"{report_id}.jsonl"

    def append(self, event: ReviewEvent) -> str:
        target = self._path(event.report_id)
        existing = self._iter_events(report_id=event.report_id, raise_on_corrupt=self._fail_closed)
        existing_ids = {e.event_id for e in existing}
        existing_keys = {e.idempotency_key for e in existing if e.idempotency_key}
        if event.event_id in existing_ids:
            return event.event_id
        if event.idempotency_key and event.idempotency_key in existing_keys:
            return next(e.event_id for e in existing if e.idempotency_key == event.idempotency_key)

        sequence = event.sequence_number
        if sequence is None:
            sequence = len(existing) + 1
        stamped = ReviewEvent(
            **{
                **event.__dict__,
                "sequence_number": sequence,
            }
        )
        line = json.dumps(asdict(stamped), ensure_ascii=False) + "\n"
        if len(line.encode("utf-8")) > _MAX_LINE_BYTES:
            raise ValueError(f"Review event exceeds max line size ({_MAX_LINE_BYTES} bytes)")
        self._append_exclusive(target, line)
        return stamped.event_id

    def list_for_report(self, report_id: str) -> list[ReviewEvent]:
        return list(self._iter_events(report_id=report_id, raise_on_corrupt=self._fail_closed))

    def discard_report(self, report_id: str) -> None:
        """Compensating delete when report persist fails after HITL trail write."""
        target = self._path(report_id)
        lock_path = target.with_suffix(target.suffix + ".lock")
        target.unlink(missing_ok=True)
        lock_path.unlink(missing_ok=True)

    def _append_exclusive(self, target: Path, line: str) -> None:
        lock_path = target.with_suffix(target.suffix + ".lock")
        for _ in range(_LOCK_ATTEMPTS):
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                try:
                    os.write(fd, b"1")
                finally:
                    os.close(fd)
                try:
                    with target.open("a", encoding="utf-8") as handle:
                        handle.write(line)
                        handle.flush()
                        os.fsync(handle.fileno())
                    return
                finally:
                    lock_path.unlink(missing_ok=True)
            except FileExistsError:
                time.sleep(_LOCK_SLEEP_S)
        raise RuntimeError(f"Could not acquire review-event lock for {target.name}")

    def _iter_events(self, *, report_id: str, raise_on_corrupt: bool) -> list[ReviewEvent]:
        target = self._path(report_id)
        self.last_invalid_line_count = 0
        self.last_load_degraded = False
        if not target.exists():
            return []
        events: list[ReviewEvent] = []
        seen_ids: set[str] = set()
        seen_keys: set[str] = set()
        expected_seq = 1
        for line in target.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            if len(line.encode("utf-8")) > _MAX_LINE_BYTES:
                self.last_invalid_line_count += 1
                continue
            try:
                data = json.loads(line)
                event = ReviewEvent(
                    event_id=str(data["event_id"]),
                    report_id=str(data["report_id"]),
                    event_type=data["event_type"],
                    created_at=str(data["created_at"]),
                    issue_rule_id=data.get("issue_rule_id"),
                    actor=data.get("actor"),
                    note=data.get("note"),
                    latency_ms=data.get("latency_ms"),
                    pack_id=data.get("pack_id"),
                    resulting_pack_version=data.get("resulting_pack_version"),
                    target_approval_status=data.get("target_approval_status"),
                    approval_ref=data.get("approval_ref"),
                    rule_diff_json=data.get("rule_diff_json"),
                    idempotency_key=data.get("idempotency_key"),
                    sequence_number=data.get("sequence_number"),
                    previous_state=data.get("previous_state"),
                    resulting_state=data.get("resulting_state"),
                    finding_id=data.get("finding_id"),
                )
                if event.event_id in seen_ids:
                    self.last_invalid_line_count += 1
                    continue
                if event.idempotency_key and event.idempotency_key in seen_keys:
                    self.last_invalid_line_count += 1
                    continue
                if event.sequence_number is not None and event.sequence_number != expected_seq:
                    _logger.warning(
                        "review-events sequence gap for %s: got %s expected %s",
                        report_id,
                        event.sequence_number,
                        expected_seq,
                    )
                seen_ids.add(event.event_id)
                if event.idempotency_key:
                    seen_keys.add(event.idempotency_key)
                events.append(event)
                expected_seq = (
                    event.sequence_number + 1
                    if event.sequence_number is not None
                    else expected_seq + 1
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                self.last_invalid_line_count += 1
                continue
        if self.last_invalid_line_count:
            self.last_load_degraded = True
            _logger.warning(
                "review-events for %s degraded: invalid_lines=%s",
                report_id,
                self.last_invalid_line_count,
            )
            if raise_on_corrupt:
                raise AuditEventCorruptionError(
                    f"Audit JSONL corrupt for report {report_id}: "
                    f"{self.last_invalid_line_count} invalid line(s)"
                )
        return events
