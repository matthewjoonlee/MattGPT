"""Retry-with-backoff for GLITCH-classified failures, built on tenacity."""

from __future__ import annotations

from typing import Callable

from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential


def build_glitch_retrying(
    *,
    max_attempts: int = 3,
    wait_min: float = 0.5,
    wait_max: float = 8.0,
    is_glitch: Callable[[BaseException], bool],
    before_retry: Callable[..., None] | None = None,
) -> Retrying:
    """Return a configured ``tenacity.Retrying`` object.

    ``is_glitch`` decides, per raised exception, whether this attempt should
    be retried at all (a non-GLITCH classification stops the loop
    immediately, even on the first attempt, rather than burning through
    ``max_attempts`` on a failure retrying can't fix). ``reraise=True`` means
    the *original* exception propagates on give-up, never tenacity's own
    ``RetryError`` wrapper.
    """
    return Retrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(min=wait_min, max=wait_max),
        retry=retry_if_exception(is_glitch),
        before_sleep=before_retry,
        reraise=True,
    )
