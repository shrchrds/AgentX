"""Structured logging setup for AgentX.

Configures Python's stdlib logging with JSON-formatted output.
Provides context helpers to attach ``task_id`` and ``agent_id`` to log records.
Sensitive fields (passwords, tokens, keys) are never logged.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# Context variables for request-scoped tracing
_task_id_var: ContextVar[str] = ContextVar("task_id", default="")
_agent_id_var: ContextVar[str] = ContextVar("agent_id", default="")

# Patterns to redact from log output
_SENSITIVE_PATTERNS = re.compile(
    r"(api[_-]?key|secret|token|password|credential|authorization)" r"\s*[:=]\s*\S+",
    re.IGNORECASE,
)


def set_task_context(task_id: str) -> None:
    """Set the current task_id for log context."""
    _task_id_var.set(task_id)


def set_agent_context(agent_id: str) -> None:
    """Set the current agent_id for log context."""
    _agent_id_var.set(agent_id)


class _JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": self._redact(record.getMessage()),
        }

        # Attach context if available
        task_id = _task_id_var.get("")
        agent_id = _agent_id_var.get("")
        if task_id:
            log_entry["task_id"] = task_id
        if agent_id:
            log_entry["agent_id"] = agent_id

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])

        return json.dumps(log_entry, default=str)

    @staticmethod
    def _redact(message: str) -> str:
        """Redact sensitive values from log messages."""
        return _SENSITIVE_PATTERNS.sub(r"\1=***REDACTED***", message)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure the root logger with JSON formatting.

    Args:
        log_level: Logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates on re-init
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JSONFormatter())
    root_logger.addHandler(handler)

    # Quiet noisy third-party loggers
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger for use in application modules.

    Args:
        name: Logger name, typically ``__name__`` of the calling module.
    """
    return logging.getLogger(name)
