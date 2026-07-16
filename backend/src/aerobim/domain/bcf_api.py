"""Domain models for BCF API 3.0 push results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BcfApiTopicPushResult:
    title: str
    remote_guid: str | None
    server_assigned_id: str | None
    success: bool
    error_message: str | None = None


@dataclass(frozen=True)
class BcfApiPushResult:
    project_id: str
    attempted: int
    succeeded: int
    failed: int
    topics: tuple[BcfApiTopicPushResult, ...]
