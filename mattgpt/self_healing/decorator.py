"""The public interface: ``@self_healing(...)``.

Composes classification + retry-with-backoff + circuit-breaker/backup +
decompose-or-give-up + fix logging into the single wrapper other MattGPT
modules apply to their own tool calls.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

from .breaker import build_circuit_breaker, call_with_backup
from .classify import classify_failure
from .logging_sink import FixLogEntry, FixLogger
from .retry import build_glitch_retrying
from .taxonomy import DataIssueError, FailureType

T = TypeVar("T")


def self_healing(
    *,
    validate_result: Callable[[Any], bool] | None = None,
    backup: Callable[..., Any] | None = None,
    decompose: Callable[..., Any] | None = None,
    max_glitch_attempts: int = 3,
    wait_min: float = 0.5,
    wait_max: float = 8.0,
    breaker_fail_max: int = 3,
    breaker_reset_timeout: int = 30,
    logger: FixLogger | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator factory applying the self-healing reliability layer.

    ``validate_result`` and ``decompose`` are caller-supplied, task-specific
    hooks — this module deliberately does not invent generic result
    validation or task decomposition.
    """

    def decorate(fn: Callable[..., T]) -> Callable[..., T]:
        breaker = build_circuit_breaker(
            fail_max=breaker_fail_max, reset_timeout=breaker_reset_timeout, name=fn.__name__
        )
        log = logger or FixLogger()

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            def call_once() -> T:
                result, _stage = call_with_backup(breaker, lambda: fn(*args, **kwargs), None)
                if validate_result is not None and not validate_result(result):
                    raise DataIssueError(f"validate_result rejected the output of {fn.__name__!r}")
                return result

            def is_glitch(exc: BaseException) -> bool:
                return classify_failure(exc, breaker_state=breaker.current_state) is FailureType.GLITCH

            def log_retry(retry_state: Any) -> None:
                exc = retry_state.outcome.exception()
                log.log_fix(
                    FixLogEntry(
                        function_name=fn.__name__,
                        failure_type=FailureType.GLITCH,
                        exception_repr=repr(exc),
                        remediation="retry",
                        outcome="pending",
                        stage="primary",
                    )
                )

            retrying = build_glitch_retrying(
                max_attempts=max_glitch_attempts,
                wait_min=wait_min,
                wait_max=wait_max,
                is_glitch=is_glitch,
                before_retry=log_retry,
            )

            try:
                result = retrying(call_once)
            except BaseException as exc:  # noqa: BLE001 - reclassified below
                return _handle_failure(fn, exc, breaker, backup, decompose, log, args, kwargs)

            log.log_fix(
                FixLogEntry(
                    function_name=fn.__name__,
                    failure_type=None,
                    exception_repr=None,
                    remediation="none",
                    outcome="recovered",
                    stage="primary",
                )
            )
            return result

        return wrapper

    return decorate


def _handle_failure(
    fn: Callable[..., Any],
    exc: BaseException,
    breaker: Any,
    backup: Callable[..., Any] | None,
    decompose: Callable[..., Any] | None,
    log: FixLogger,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    ftype = classify_failure(
        exc,
        breaker_state=breaker.current_state,
        retry_exhausted=True,
        backup_exhausted=(backup is None),
    )

    if ftype is FailureType.DATA_ISSUE:
        log.log_fix(
            FixLogEntry(fn.__name__, ftype, repr(exc), "surfaced_data_issue", "surfaced", "primary")
        )
        raise exc

    if ftype in (FailureType.GLITCH, FailureType.TOOL_DOWN) and backup is not None:
        try:
            result = backup(*args, **kwargs)
        except BaseException:
            pass
        else:
            log.log_fix(
                FixLogEntry(fn.__name__, FailureType.TOOL_DOWN, repr(exc), "backup", "recovered", "backup")
            )
            return result

    # Reclassify with backup now confirmed exhausted (either it was never
    # configured, or it just failed above).
    ftype = classify_failure(exc, breaker_state=breaker.current_state, retry_exhausted=True, backup_exhausted=True)

    if decompose is not None:
        log.log_fix(FixLogEntry(fn.__name__, ftype, repr(exc), "decompose", "pending", "decomposed"))
        try:
            result = decompose(*args, **kwargs)
        except BaseException as decompose_exc:
            log.log_fix(
                FixLogEntry(fn.__name__, ftype, repr(decompose_exc), "decompose", "exhausted", "decomposed")
            )
            raise decompose_exc from exc
        log.log_fix(FixLogEntry(fn.__name__, ftype, None, "decompose", "recovered", "decomposed"))
        return result

    log.log_fix(FixLogEntry(fn.__name__, ftype, repr(exc), "give_up", "exhausted", "primary"))
    raise exc
