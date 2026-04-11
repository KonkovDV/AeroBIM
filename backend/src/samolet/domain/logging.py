"""Structured logging port — domain-level contract for log output.

Follows the structured logging pattern from ISO/IEC 27034 and
the Twelve-Factor App methodology (factor XI: treat logs as event streams).
"""

from __future__ import annotations

from typing import Protocol


class StructuredLogger(Protocol):
    """Domain port for structured, correlation-aware logging."""

    def info(self, message: str, **context: object) -> None: ...

    def warning(self, message: str, **context: object) -> None: ...

    def error(self, message: str, **context: object) -> None: ...

    def debug(self, message: str, **context: object) -> None: ...
