"""Fix-audit logging: Langfuse as the trace sink, stdlib logging as the
always-on local source of truth (never a bespoke logging system).
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from .taxonomy import FailureType

_log = logging.getLogger("mattgpt.self_healing")


@dataclass(frozen=True)
class FixLogEntry:
    """One record of a failure, its classification, the remediation applied,
    and the outcome — per review.md's "log every fix" requirement.
    """

    function_name: str
    failure_type: FailureType | None
    exception_repr: str | None
    remediation: str  # "retry" | "backup" | "decompose" | "give_up" | "surfaced_data_issue" | "none"
    outcome: str  # "pending" | "recovered" | "exhausted" | "surfaced"
    stage: str  # "primary" | "backup" | "decomposed"
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())


class FixLogger:
    """Logs every remediation decision. Never raises — a broken logger must
    not break the tool call it's logging (self-healing applied recursively
    to the self-healer itself).
    """

    def __init__(self) -> None:
        self._langfuse = self._try_build_langfuse_client()

    @staticmethod
    def _try_build_langfuse_client():
        try:
            from langfuse import get_client

            return get_client()
        except Exception:
            _log.warning(
                "Langfuse client unavailable — fix log falling back to local logging only",
                exc_info=True,
            )
            return None

    def log_fix(self, entry: FixLogEntry) -> None:
        payload = asdict(entry)
        payload["failure_type"] = entry.failure_type.value if entry.failure_type else None
        _log.warning("self_healing fix: %s", payload)

        if self._langfuse is None:
            return
        try:
            self._langfuse.create_event(
                name=f"self-healing:{entry.function_name}",
                metadata=payload,
                level="WARNING",
                status_message=f"{entry.remediation} -> {entry.outcome}",
            )
        except Exception:
            _log.warning("Langfuse create_event failed — local log entry above is the record", exc_info=True)
