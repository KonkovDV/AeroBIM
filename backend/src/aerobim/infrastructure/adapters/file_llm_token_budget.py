"""File-backed day counters for advisory LLM token budget (RT-BUDGET-03 / RT-LEDGER).

Domain ``LlmTokenBudget`` stays I/O-free; this adapter persists ``day_key`` /
``tokens_today`` under an exclusive lock so worker pools share one daily cap.

RT-LEDGER-01: a stuck ``.lock`` after a crashed holder is detected by mtime and
removed; if the lock still cannot be acquired, ``lock_degraded=True`` is set so
the loss of cross-process mutual exclusion is visible in ``snapshot()`` / audit
(silent process-local fallback is forbidden).
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

# Spin-wait bound for exclusive lockfile (no new lock dependency).
_LOCK_TIMEOUT_SECONDS = 5.0
_LOCK_POLL_SECONDS = 0.05
# Lock older than this is treated as abandoned after a crash (RT-LEDGER-01).
# Source: 6× spin timeout — longer than any healthy holder of a JSON rewrite.
_STALE_LOCK_SECONDS = 30.0


class FileBackedLlmTokenBudget(LlmTokenBudget):
    """Process + cross-worker day ledger via JSON + exclusive lockfile."""

    def __init__(self, path: Path, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.budget_scope = "file_shared"
        self.lock_degraded = False
        self._path = path
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _lock_path(self) -> Path:
        return self._path.with_suffix(self._path.suffix + ".lock")

    def _try_clear_stale_lock(self, lock_path: Path) -> bool:
        """Remove abandoned lockfile; return True if cleared or absent."""
        try:
            if not lock_path.exists():
                return True
            age = time.time() - lock_path.stat().st_mtime
            if age >= _STALE_LOCK_SECONDS:
                lock_path.unlink(missing_ok=True)
                return True
        except OSError:
            return False
        return False

    def _acquire_fs_lock(self) -> int:
        """Return lock fd, or -1 when degraded (cross-process lock unavailable)."""
        deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
        lock_path = self._lock_path()
        stale_cleared = False
        while True:
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                # Write pid for operators inspecting a live lock.
                try:
                    os.write(fd, f"{os.getpid()}\n".encode("ascii"))
                except OSError:
                    pass
                return fd
            except FileExistsError:
                if not stale_cleared and self._try_clear_stale_lock(lock_path):
                    stale_cleared = True
                    continue
                if time.monotonic() >= deadline:
                    # Visible degradation — never silently look like file_shared
                    # while running without mutual exclusion (RT-LEDGER-01).
                    self.lock_degraded = True
                    self.budget_scope = "file_shared_lock_degraded"
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
        fd = self._acquire_fs_lock()
        try:
            if not self._path.is_file():
                return
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
            "lock_degraded": self.lock_degraded,
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

    def snapshot(self, *, include_last_charge: int | None = None) -> dict[str, Any]:
        out = super().snapshot(include_last_charge=include_last_charge)
        out["lock_degraded"] = bool(self.lock_degraded)
        if self.lock_degraded:
            out["budget_scope"] = "file_shared_lock_degraded"
            out["lock_degraded_reason"] = (
                "cross-process lock unavailable or timed out; day counters may "
                "diverge across workers until the stale .lock is cleared"
            )
        return out

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
