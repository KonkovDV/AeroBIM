"""Filesystem-backed HITL review event store (W3.5)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from aerobim.domain.models import ReviewEvent


class FilesystemReviewEventStore:
    def __init__(self, storage_dir: Path) -> None:
        self._dir = storage_dir / "review-events"
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, report_id: str) -> Path:
        return self._dir / f"{report_id}.jsonl"

    def append(self, event: ReviewEvent) -> str:
        target = self._path(event.report_id)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
        return event.event_id

    def list_for_report(self, report_id: str) -> list[ReviewEvent]:
        target = self._path(report_id)
        if not target.exists():
            return []
        events: list[ReviewEvent] = []
        for line in target.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                events.append(
                    ReviewEvent(
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
                    )
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
        return events
