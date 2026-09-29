"""Deterministic fault classification — no model call, per "compute, then explain"."""

from __future__ import annotations

from .taxonomy import DataIssueError, FailureType, WrongApproachError

# Extensible by callers who know their own tool's transient/unavailable shapes.
TRANSIENT_EXCEPTIONS: tuple[type[BaseException], ...] = (
    ConnectionError,
    TimeoutError,
)

TOOL_DOWN_EXCEPTIONS: tuple[type[BaseException], ...] = ()


def classify_failure(
    exc: BaseException | None,
    *,
    breaker_state: str | None = None,
    retry_exhausted: bool = False,
    backup_exhausted: bool = False,
) -> FailureType:
    """Classify a failure into the small taxonomy from review.md.

    A pure predicate-table lookup: no I/O, no randomness, so it's
    independently unit-testable and never involves an LLM call.
    """
    # DataIssueError is checked first and unconditionally: it's the one
    # classification that must never be overridden by exhaustion bookkeeping
    # (a validate_result failure is never "the approach doesn't fit" just
    # because no backup happens to be configured).
    if isinstance(exc, DataIssueError):
        return FailureType.DATA_ISSUE

    if isinstance(exc, WrongApproachError) or (retry_exhausted and backup_exhausted):
        return FailureType.WRONG_APPROACH

    if breaker_state == "open" or isinstance(exc, TOOL_DOWN_EXCEPTIONS):
        return FailureType.TOOL_DOWN

    if isinstance(exc, TRANSIENT_EXCEPTIONS):
        return FailureType.GLITCH

    # Least destructive default for an unrecognized exception: assume it
    # might just be a blip, and let the retry loop's attempt cap bound the
    # cost of being wrong.
    return FailureType.GLITCH
