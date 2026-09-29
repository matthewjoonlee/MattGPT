"""Circuit-breaker for TOOL_DOWN failures, built on pybreaker."""

from __future__ import annotations

from typing import Callable, TypeVar

import pybreaker

T = TypeVar("T")


def build_circuit_breaker(
    *,
    fail_max: int = 3,
    reset_timeout: int = 30,
    name: str = "default",
) -> pybreaker.CircuitBreaker:
    """Build one breaker instance for a protected call-site.

    Build once at decoration time and reuse across calls — trip state must
    persist across calls, which is the entire point of a circuit breaker.
    """
    return pybreaker.CircuitBreaker(fail_max=fail_max, reset_timeout=reset_timeout, name=name)


def call_with_backup(
    breaker: pybreaker.CircuitBreaker,
    primary: Callable[[], T],
    backup: Callable[[], T] | None,
) -> tuple[T, str]:
    """Run ``primary`` through the breaker; fall through to ``backup`` once
    the breaker is open.

    A single failure of ``primary`` while the breaker is still closed is
    recorded by the breaker but re-raised as-is (it's a GLITCH candidate,
    not yet a confirmed tool-down — the caller's retry loop handles it).
    Only once the breaker has actually tripped open does this switch to
    ``backup`` (never itself passed through the breaker). Returns
    ``(result, stage)`` with ``stage in {"primary", "backup"}``.
    """
    try:
        return breaker.call(primary), "primary"
    except pybreaker.CircuitBreakerError:
        if backup is None:
            raise
        return backup(), "backup"
