"""
Structured JSON logging for Cloud Logging compatibility.
Every log line is a JSON object so Cloud Logging can index
fields like `tag`, `session_id`, `ms`, `error` individually.
"""
import logging
import json
import os
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    LEVEL_MAP = {
        logging.DEBUG:    "DEBUG",
        logging.INFO:     "INFO",
        logging.WARNING:  "WARNING",
        logging.ERROR:    "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "severity": self.LEVEL_MAP.get(record.levelno, "INFO"),
            "message":  record.getMessage(),
            "logger":   record.name,
            "time":     self.formatTime(record, self.datefmt),
        }

        # Attach any extra fields passed via logging.info(..., extra={...})
        for key, val in record.__dict__.items():
            if key not in (
                "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "name",
                "message", "asctime",
            ):
                payload[key] = val

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Call once at app startup."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove default handlers
    root.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    root.addHandler(handler)

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "google.auth", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


# ── Convenience helpers ───────────────────────────────────────────

def log(level: str, message: str, **fields) -> None:
    """Structured log with arbitrary extra fields."""
    logger = logging.getLogger("app")
    getattr(logger, level)(message, extra=fields)


def log_request(tag: str, session_id: str, **fields) -> None:
    log("info", f"request:{tag}", tag=tag, session_id=session_id, **fields)


def log_response(tag: str, session_id: str, ms: int, **fields) -> None:
    log("info", f"response:{tag}", tag=tag, session_id=session_id, ms=ms, **fields)


def log_error(tag: str, session_id: str, error: str, **fields) -> None:
    log("error", f"error:{tag}", tag=tag, session_id=session_id, error=error, **fields)
