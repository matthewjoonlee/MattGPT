"""Tests for the self-healing reliability layer, against dummy functions that
fail in controlled, specific ways — no dependency on any other MattGPT module.
"""

from __future__ import annotations

import pybreaker
import pytest

from mattgpt.self_healing import DataIssueError, FailureType, WrongApproachError, self_healing
from mattgpt.self_healing.logging_sink import FixLogEntry, FixLogger


class RecordingLogger(FixLogger):
    """A FixLogger that skips Langfuse entirely and records entries in memory,
    so tests can assert on exactly what was logged without parsing files.
    """

    def __init__(self) -> None:
        self._langfuse = None
        self.entries: list[FixLogEntry] = []

    def log_fix(self, entry: FixLogEntry) -> None:
        self.entries.append(entry)


# --- Dummy fixtures: each fails in one controlled, specific way ---


def make_transient_then_recovers(fail_times: int = 2):
    calls = {"count": 0}

    def flaky() -> str:
        calls["count"] += 1
        if calls["count"] <= fail_times:
            raise ConnectionError("transient blip")
        return "ok"

    flaky.calls = calls
    return flaky


def make_always_down():
    calls = {"count": 0}

    def always_down() -> str:
        calls["count"] += 1
        raise ConnectionError("permanently unreachable")

    always_down.calls = calls
    return always_down


def make_returns_malformed_data():
    calls = {"count": 0}

    def returns_malformed_data() -> dict:
        calls["count"] += 1
        return {"result": None, "error": "partial response"}

    returns_malformed_data.calls = calls
    return returns_malformed_data


def make_wrong_approach_always_fails():
    calls = {"count": 0}

    def wrong_approach_always_fails() -> str:
        calls["count"] += 1
        raise WrongApproachError("this method doesn't fit the task")

    wrong_approach_always_fails.calls = calls
    return wrong_approach_always_fails


# --- Tests ---


def test_transient_glitch_recovers_via_retry():
    fn = make_transient_then_recovers(fail_times=2)
    log = RecordingLogger()

    healed = self_healing(max_glitch_attempts=3, wait_min=0.01, wait_max=0.02, logger=log)(fn)

    assert healed() == "ok"
    assert fn.calls["count"] == 3

    glitch_entries = [e for e in log.entries if e.failure_type == FailureType.GLITCH]
    assert len(glitch_entries) == 2
    assert all(e.remediation == "retry" and e.outcome == "pending" for e in glitch_entries)
    assert log.entries[-1].outcome == "recovered"
    assert log.entries[-1].remediation == "none"


def test_tool_down_switches_to_backup():
    fn = make_always_down()
    log = RecordingLogger()

    healed = self_healing(
        backup=lambda: "backup-result",
        max_glitch_attempts=3,
        breaker_fail_max=1,
        wait_min=0.01,
        wait_max=0.02,
        logger=log,
    )(fn)

    assert healed() == "backup-result"
    assert fn.calls["count"] == 1  # breaker opened after the first failure — no wasted retries

    backup_entries = [e for e in log.entries if e.remediation == "backup"]
    assert len(backup_entries) == 1
    assert backup_entries[0].failure_type == FailureType.TOOL_DOWN
    assert backup_entries[0].outcome == "recovered"
    assert backup_entries[0].stage == "backup"


def test_data_issue_surfaces_without_retry():
    fn = make_returns_malformed_data()
    log = RecordingLogger()

    healed = self_healing(
        validate_result=lambda r: r.get("result") is not None,
        max_glitch_attempts=3,
        wait_min=0.01,
        wait_max=0.02,
        logger=log,
    )(fn)

    with pytest.raises(DataIssueError):
        healed()

    assert fn.calls["count"] == 1  # never blindly retried

    assert len(log.entries) == 1
    entry = log.entries[0]
    assert entry.failure_type == FailureType.DATA_ISSUE
    assert entry.remediation == "surfaced_data_issue"
    assert entry.outcome == "surfaced"


def test_wrong_approach_triggers_decompose():
    fn = make_wrong_approach_always_fails()
    log = RecordingLogger()

    healed = self_healing(
        decompose=lambda: "decomposed-ok",
        max_glitch_attempts=3,
        wait_min=0.01,
        wait_max=0.02,
        logger=log,
    )(fn)

    assert healed() == "decomposed-ok"
    assert fn.calls["count"] == 1  # no retry/backup wasted on a known wrong approach

    decompose_entries = [e for e in log.entries if e.remediation == "decompose"]
    assert decompose_entries[-1].outcome == "recovered"
    assert decompose_entries[-1].failure_type == FailureType.WRONG_APPROACH


def test_wrong_approach_gives_up_cleanly_without_decompose():
    fn = make_wrong_approach_always_fails()
    log = RecordingLogger()

    healed = self_healing(max_glitch_attempts=3, wait_min=0.01, wait_max=0.02, logger=log)(fn)

    with pytest.raises(WrongApproachError):
        healed()

    give_up_entries = [e for e in log.entries if e.remediation == "give_up"]
    assert len(give_up_entries) == 1
    assert give_up_entries[0].outcome == "exhausted"
    assert give_up_entries[0].failure_type == FailureType.WRONG_APPROACH


def test_logger_falls_back_when_langfuse_unconfigured(monkeypatch, caplog):
    for var in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST"):
        monkeypatch.delenv(var, raising=False)

    logger = FixLogger()  # must not raise despite no Langfuse credentials

    with caplog.at_level("WARNING", logger="mattgpt.self_healing"):
        logger.log_fix(
            FixLogEntry(
                function_name="dummy",
                failure_type=FailureType.GLITCH,
                exception_repr="ConnectionError('x')",
                remediation="retry",
                outcome="pending",
                stage="primary",
            )
        )  # must not raise

    assert any("self_healing fix" in record.message for record in caplog.records)


def test_breaker_already_open_reclassifies_instead_of_spinning():
    fn = make_always_down()
    log = RecordingLogger()

    # max_glitch_attempts is high, but the breaker trips on the very first
    # failure — the retry loop must not burn through all attempts against
    # an already-open breaker.
    healed = self_healing(
        max_glitch_attempts=5,
        breaker_fail_max=1,
        wait_min=0.01,
        wait_max=0.02,
        logger=log,
    )(fn)

    # pybreaker wraps the exception that trips the breaker as a
    # CircuitBreakerError right on that same call (rather than the raw
    # ConnectionError) — but chains the original via __context__, so no
    # diagnostic information is lost.
    with pytest.raises(pybreaker.CircuitBreakerError) as excinfo:
        healed()
    assert isinstance(excinfo.value.__context__, ConnectionError)

    assert fn.calls["count"] == 1

    retry_entries = [e for e in log.entries if e.remediation == "retry"]
    assert retry_entries == []

    give_up_entries = [e for e in log.entries if e.remediation == "give_up"]
    assert len(give_up_entries) == 1
    assert give_up_entries[0].failure_type == FailureType.WRONG_APPROACH
