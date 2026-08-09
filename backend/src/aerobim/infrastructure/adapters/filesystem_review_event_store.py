"""Filesystem-backed HITL review event store (W3.5).

RT-HYPER-002: corrupt JSONL lines are counted; fail-closed profiles raise.
RT-P5: idempotency_key de-dupe, sequence numbers, exclusive append lock.
RT-AUDIT-001/002: locked API append + hash chain tamper-evidence.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, replace
from pathlib import Path

from aerobim.domain.models import ReviewEvent
from aerobim.domain.review_event_append import HitlStateConflictError, ReviewEventAppendSpec
from aerobim.domain.review_event_chain import genesis_previous_hash, review_event_content_hash
from aerobim.domain.review_state_machine import (
    HitlTransitionError,
    assert_hitl_transition,
    latest_hitl_state,
)

_logger = logging.getLogger(__name__)

_MAX_LINE_BYTES = 256 * 1024
_LOCK_ATTEMPTS = 50
_LOCK_SLEEP_S = 0.02
_LOCK_STALE_S = 60.0
_NORM_PACK_EVENT_TYPES = frozenset({"norm_rule_proposed", "norm_rule_edited"})


class AuditEventCorruptionError(RuntimeError):
    """Raised when audit_fail_closed=True and JSONL contains invalid lines."""


class ReviewEventChainError(RuntimeError):
    """Raised when hash-chain verification fails under fail-closed."""


class SequenceClaimError(RuntimeError):
    """Raised when another writer already claimed this sequence slot (CAS conflict)."""


def _acquire_excl_lock(lock_path: Path) -> int:
    """Create exclusive lock file; reclaim stale locks via exclusive reclaim marker.

    Age-based unlink alone is a race (two reclaimers can both succeed). The
    ``.reclaim`` marker is created with O_EXCL so only one process clears the
    stale lock. Sequence numbers still use O_EXCL slots — lock is an optimization.
    """

    try:
        return os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            age = time.time() - lock_path.stat().st_mtime
        except OSError:
            age = 0.0
        if age < _LOCK_STALE_S:
            raise
        reclaim_path = Path(str(lock_path) + ".reclaim")
        try:
            rfd = os.open(str(reclaim_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(rfd)
        except FileExistsError:
            raise FileExistsError from None
        try:
            try:
                age = time.time() - lock_path.stat().st_mtime
            except OSError:
                age = _LOCK_STALE_S
            if age < _LOCK_STALE_S:
                raise FileExistsError
            lock_path.unlink(missing_ok=True)
            return os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        finally:
            reclaim_path.unlink(missing_ok=True)


def _claim_sequence_slot(target: Path, sequence: int) -> Path:
    """Create sequence claim file exclusively — duplicate sequence becomes impossible."""

    slot = target.with_name(f"{target.name}.seq.{sequence}")
    try:
        fd = os.open(str(slot), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise SequenceClaimError(f"sequence {sequence} already claimed for {target.name}") from exc
    try:
        os.write(fd, b"1")
    finally:
        os.close(fd)
    return slot


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
        return self._append_under_lock(target, event)

    def append_api_event(self, spec: ReviewEventAppendSpec) -> ReviewEvent:
        """Validate HITL transitions and assign sequence/hash under exclusive lock."""

        target = self._path(spec.report_id)
        lock_path = target.with_suffix(target.suffix + ".lock")
        for _ in range(_LOCK_ATTEMPTS):
            try:
                fd = _acquire_excl_lock(lock_path)
                try:
                    os.write(fd, f"{time.time():.3f}".encode("ascii"))
                finally:
                    os.close(fd)
                try:
                    return self._append_api_under_lock(target, spec)
                finally:
                    lock_path.unlink(missing_ok=True)
            except (FileExistsError, SequenceClaimError):
                time.sleep(_LOCK_SLEEP_S)
        raise RuntimeError(f"Could not acquire review-event lock for {target.name}")

    def list_for_report(self, report_id: str) -> list[ReviewEvent]:
        return list(self._iter_events(report_id=report_id, raise_on_corrupt=self._fail_closed))

    def discard_report(self, report_id: str) -> None:
        """Compensating delete when report persist fails after HITL trail write."""

        target = self._path(report_id)
        lock_path = target.with_suffix(target.suffix + ".lock")
        for _ in range(_LOCK_ATTEMPTS):
            try:
                fd = _acquire_excl_lock(lock_path)
                try:
                    os.write(fd, f"{time.time():.3f}".encode("ascii"))
                finally:
                    os.close(fd)
                try:
                    target.unlink(missing_ok=True)
                    return
                finally:
                    lock_path.unlink(missing_ok=True)
            except FileExistsError:
                time.sleep(_LOCK_SLEEP_S)
        raise RuntimeError(f"Could not acquire review-event lock for discard {target.name}")

    def _append_api_under_lock(self, target: Path, spec: ReviewEventAppendSpec) -> ReviewEvent:
        existing = self._iter_events(
            report_id=spec.report_id,
            raise_on_corrupt=self._fail_closed,
        )
        existing_ids = {e.event_id for e in existing}
        existing_keys = {e.idempotency_key for e in existing if e.idempotency_key}
        idem = (spec.idempotency_key or "").strip() or None
        event_id = (spec.event_id or "").strip() or None
        if not event_id and idem:
            import hashlib

            event_id = hashlib.sha256(idem.encode("utf-8")).hexdigest()[:32]
        if not event_id:
            raise ValueError("event_id or idempotency_key is required")

        if event_id in existing_ids:
            return next(e for e in existing if e.event_id == event_id)
        if idem and idem in existing_keys:
            return next(e for e in existing if e.idempotency_key == idem)

        server_state = latest_hitl_state(
            existing,
            spec.finding_id,
            spec.issue_rule_id,
        )
        resulting_state: str | None = None
        if spec.event_type not in _NORM_PACK_EVENT_TYPES:
            client_previous = (spec.previous_state or "").strip() or None
            if server_state is not None:
                if spec.previous_state is None:
                    raise HitlTransitionError(
                        "previous_state is required when appending to existing HITL state"
                    )
                if client_previous != server_state:
                    raise HitlStateConflictError(
                        f"previous_state does not match server HITL state "
                        f"(server={server_state!r}, client={client_previous!r})"
                    )
            try:
                resulting_state = assert_hitl_transition(
                    current=server_state,
                    event_type=spec.event_type,
                    actor=spec.actor,
                    note=spec.note,
                )
            except HitlTransitionError:
                raise

        sequence = len(existing) + 1
        previous_hash = (
            existing[-1].content_hash
            if existing and existing[-1].content_hash
            else genesis_previous_hash()
        )
        draft = ReviewEvent(
            event_id=event_id,
            report_id=spec.report_id,
            event_type=spec.event_type,  # type: ignore[arg-type]
            created_at=spec.created_at,
            issue_rule_id=spec.issue_rule_id,
            actor=spec.actor,
            note=spec.note,
            latency_ms=spec.latency_ms,
            idempotency_key=idem,
            sequence_number=sequence,
            previous_state=server_state,
            resulting_state=resulting_state,
            finding_id=spec.finding_id,
            previous_event_hash=previous_hash,
        )
        content_hash = review_event_content_hash(draft, previous_event_hash=previous_hash)
        stamped = replace(draft, content_hash=content_hash)
        self._write_event_line(target, stamped, sequence=sequence)
        return stamped

    def _append_under_lock(self, target: Path, event: ReviewEvent) -> str:
        """Read-modify-write under exclusive lock (RT-HITL-001)."""

        lock_path = target.with_suffix(target.suffix + ".lock")
        report_id = event.report_id
        for _ in range(_LOCK_ATTEMPTS):
            try:
                fd = _acquire_excl_lock(lock_path)
                try:
                    os.write(fd, f"{time.time():.3f}".encode("ascii"))
                finally:
                    os.close(fd)
                try:
                    existing = self._iter_events(
                        report_id=report_id,
                        raise_on_corrupt=self._fail_closed,
                    )
                    existing_ids = {e.event_id for e in existing}
                    existing_keys = {e.idempotency_key for e in existing if e.idempotency_key}
                    if event.event_id in existing_ids:
                        return event.event_id
                    if event.idempotency_key and event.idempotency_key in existing_keys:
                        return next(
                            e.event_id
                            for e in existing
                            if e.idempotency_key == event.idempotency_key
                        )

                    sequence = len(existing) + 1
                    previous_hash = (
                        existing[-1].content_hash
                        if existing and existing[-1].content_hash
                        else genesis_previous_hash()
                    )
                    draft = replace(
                        event,
                        sequence_number=sequence,
                        previous_event_hash=event.previous_event_hash or previous_hash,
                    )
                    if not draft.content_hash:
                        content_hash = review_event_content_hash(
                            draft,
                            previous_event_hash=draft.previous_event_hash or previous_hash,
                        )
                        draft = replace(draft, content_hash=content_hash)
                    self._write_event_line(target, draft, sequence=sequence)
                    return draft.event_id
                finally:
                    lock_path.unlink(missing_ok=True)
            except (FileExistsError, SequenceClaimError):
                time.sleep(_LOCK_SLEEP_S)
        raise RuntimeError(f"Could not acquire review-event lock for {target.name}")

    def _write_event_line(self, target: Path, event: ReviewEvent, *, sequence: int) -> None:
        line = json.dumps(asdict(event), ensure_ascii=False) + "\n"
        if len(line.encode("utf-8")) > _MAX_LINE_BYTES:
            raise ValueError(f"Review event exceeds max line size ({_MAX_LINE_BYTES} bytes)")
        # Claim sequence before append so lock-reclaim races cannot duplicate numbers.
        _claim_sequence_slot(target, sequence)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())

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
        expected_prev_hash = genesis_previous_hash()
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
                    content_hash=data.get("content_hash"),
                    previous_event_hash=data.get("previous_event_hash"),
                )
                if event.event_id in seen_ids:
                    self.last_invalid_line_count += 1
                    continue
                if event.idempotency_key and event.idempotency_key in seen_keys:
                    self.last_invalid_line_count += 1
                    continue
                if event.sequence_number is not None and event.sequence_number != expected_seq:
                    msg = (
                        f"review-events sequence gap for {report_id}: "
                        f"got {event.sequence_number} expected {expected_seq}"
                    )
                    if raise_on_corrupt:
                        raise ReviewEventChainError(msg)
                    _logger.warning(msg)
                    self.last_load_degraded = True
                if event.content_hash:
                    prev = event.previous_event_hash or genesis_previous_hash()
                    if prev != expected_prev_hash:
                        msg = (
                            f"review-events hash-chain break for {report_id} "
                            f"at seq {event.sequence_number}"
                        )
                        if raise_on_corrupt:
                            raise ReviewEventChainError(msg)
                        _logger.warning(msg)
                        self.last_load_degraded = True
                    recomputed = review_event_content_hash(event, previous_event_hash=prev)
                    if recomputed != event.content_hash:
                        msg = f"review-events content_hash mismatch for {report_id}"
                        if raise_on_corrupt:
                            raise ReviewEventChainError(msg)
                        _logger.warning(msg)
                        self.last_load_degraded = True
                    expected_prev_hash = event.content_hash
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
