"""Failure taxonomy for the self-healing layer (MattGPT-Outline.md §12)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FailureType(str, Enum):
    """The small taxonomy every failure gets named into, per review.md."""

    GLITCH = "glitch"
    TOOL_DOWN = "tool_down"
    DATA_ISSUE = "data_issue"
    WRONG_APPROACH = "wrong_approach"


class WrongApproachError(Exception):
    """Raise this when the approach itself doesn't fit the task.

    Skips straight to the decompose-or-give-up remediation instead of
    waiting for retry/backup to exhaust first.
    """


class DataIssueError(Exception):
    """Raised when a caller-supplied ``validate_result`` check rejects a result.

    Never retried — a bad result is a signal to surface honestly, not a
    transient failure to paper over.
    """


@dataclass(frozen=True)
class FailureContext:
    """Everything the classifier needs to name a failure."""

    exception: BaseException | None
    breaker_state: str | None
    retry_exhausted: bool
    backup_exhausted: bool
