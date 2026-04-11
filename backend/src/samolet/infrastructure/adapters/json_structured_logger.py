"""Standard-library structured logger adapter.

Outputs JSON-structured log lines to stderr, compatible with ELK/Loki/Datadog
log pipelines. Includes request_id correlation when available.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


class JsonStructuredLogger:
    """Infrastructure adapter implementing ``StructuredLogger`` port."""

    def __init__(self, name: str = "samolet", level: int = logging.INFO) -> None:
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(_JsonFormatter())
            self._logger.addHandler(handler)
        self._logger.setLevel(level)

    def info(self, message: str, **context: object) -> None:
        self._logger.info(message, extra={"structured_context": context})

    def warning(self, message: str, **context: object) -> None:
        self._logger.warning(message, extra={"structured_context": context})

    def error(self, message: str, **context: object) -> None:
        self._logger.error(message, extra={"structured_context": context})

    def debug(self, message: str, **context: object) -> None:
        self._logger.debug(message, extra={"structured_context": context})


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        context = getattr(record, "structured_context", None)
        if isinstance(context, dict):
            payload.update(context)
        if record.exc_info and record.exc_info[1]:
            payload["exception"] = str(record.exc_info[1])
        return json.dumps(payload, ensure_ascii=False, default=str)
