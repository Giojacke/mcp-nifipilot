import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from nifi_mcp.config import settings

_logger = logging.getLogger("nifi_mcp.audit")
_logger.addHandler(logging.NullHandler())

_SENSITIVE = re.compile(r"password|secret|token|credential|key|auth", re.IGNORECASE)


def _redact(params: dict) -> dict:
    result = {}
    for k, v in params.items():
        if _SENSITIVE.search(str(k)):
            result[k] = "***REDACTED***"
        elif isinstance(v, dict):
            result[k] = _redact(v)
        else:
            result[k] = v
    return result


def _setup() -> None:
    _logger.setLevel(logging.INFO)
    if not settings.mcp_audit_log:
        return
    log_path = Path(settings.mcp_audit_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(handler)


_setup()


def log_call(
    tool: str,
    params: dict,
    result: str,
    error: str | None = None,
) -> None:
    """Append a single structured JSON line for every tool invocation."""
    entry = {
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "tool": tool,
        "params": _redact(params),
        "result": result,
        "error": error,
    }
    _logger.info(json.dumps(entry, default=str))
