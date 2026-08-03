"""File-backed day counters for advisory LLM token budget (RT-BUDGET-03).

Domain ``LlmTokenBudget`` stays I/O-free; this adapter persists ``day_key`` /
``tokens_today`` under an exclusive lock so worker pools share one daily cap.
"""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import date
from pathlib import Path
from typing import Any

from aerobim.domain.llm_token_budget import LlmTokenBudget

# Spin-wait bound for exclusive lockfile (no new lock dependency; RT-BUDGET-03).
_LOCK_TIMEOUT_SECONDS = 5.0
_LOCK_POLL_SECONDS = 0.05


class FileBackedLlmTokenBudget(LlmTokenBudget):
    """Process + cross-worker day ledger via JSON + exclusive lockfile."""

    def __init__(self, path: Path, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.budget_scope = "file_shared"
        self._path = path
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _lock_path(self) -> Path:
        return self._path.with_suffix(self._path.suffix + ".lock")

    def _acquire_fs_lock(self) -> int:
        deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
        lock_path = self._lock_path()
        while True:
            try:
                return os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if time.monotonic() >= deadline:
                    # Fail-closed: proceed without cross-process lock but still write
                    # (better than silent zero-charge). Scope stays file_shared best-effort.
                    return -1
                time.sleep(_LOCK_POLL_SECONDS)

    def _release_fs_lock(self, fd: int) -> None:
        if fd < 0:
            return
        try:
            os.close(fd)
        finally:
            try:
                self._lock_path().unlink(missing_ok=True)
            except OSError:
                pass

    def _load(self) -> None:
        if not self._path.is_file():
            return
        fd = self._acquire_fs_lock()
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            day_raw = str(raw.get("day_key") or "")
            tokens = int(raw.get("tokens_today") or 0)
            day = date.fromisoformat(day_raw) if day_raw else self._today()
            self.apply_persisted_day(day_key=day, tokens_today=tokens)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return
        finally:
            self._release_fs_lock(fd)

    def _save(self) -> None:
        payload = {
            "day_key": self.day_key.isoformat(),
            "tokens_today": self.tokens_today,
            "budget_tz": self.budget_tz,
        }
        fd = self._acquire_fs_lock()
        try:
            tmp = self._path.with_suffix(self._path.suffix + ".tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self._path)
        except OSError:
            return
        finally:
            self._release_fs_lock(fd)

    def check_before(self, *, estimated_tokens: int) -> str | None:
        with self._lock:
            self._load()
            return super().check_before(estimated_tokens=estimated_tokens)

    def record(self, *, prompt_tokens: int, completion_tokens: int) -> dict[str, Any]:
        with self._lock:
            self._load()
            out = super().record(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
            self._save()
            return out

    def record_failed(self, *, estimated_tokens: int) -> dict[str, Any]:
        with self._lock:
            self._load()
            out = super().record_failed(estimated_tokens=estimated_tokens)
            self._save()
            return out


__all__ = ["FileBackedLlmTokenBudget"]
