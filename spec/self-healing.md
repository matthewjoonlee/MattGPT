# Self-healing reliability layer — spec

Implements `MattGPT-Outline.md` §12. Owned by Window D — see `.claude/team-status.md`.

## Dependency mode

Per `CLAUDE.md`'s build-philosophy table:

| Piece | Mode |
|---|---|
| `tenacity` (retry/backoff) | Depend |
| `pybreaker` (circuit breaker) | Depend |
| Langfuse (fix-audit trail) | Depend (self-hosted; degrades to a local no-op automatically when unconfigured/unreachable) |

## What it's for

A cross-cutting reliability wrapper — `mattgpt.self_healing.self_healing` — that
any MattGPT module (db, ingest, the inference engine, the router) applies to
its own tool calls. It is not itself an LLM call: classification is a
deterministic predicate table, per "compute, then explain."

## Failure taxonomy

- **Glitch** — a transient exception (e.g. `ConnectionError`, `TimeoutError`)
  while the circuit breaker is still closed.
- **Tool down** — the circuit breaker has tripped open (repeated failures),
  or a caller-registered "tool unavailable" exception type.
- **Data issue** — the call succeeded but a caller-supplied
  `validate_result` predicate rejected the result ("check its own work").
  Raised internally as `DataIssueError`.
- **Wrong approach** — a caller explicitly raises `WrongApproachError`, or
  glitch-retries and the backup have both been exhausted with no recovery.

## Remediation mapping

| Failure type | Remediation |
|---|---|
| Glitch | Retry with exponential backoff (bounded by `max_glitch_attempts`) |
| Tool down | Switch to the caller-supplied `backup` callable once (not looped) |
| Data issue | Surface immediately — **never retried**, per `review.md`'s explicit anti-pattern ("not a blind retry every time") |
| Wrong approach | Call the caller-supplied `decompose` callable once if provided; otherwise give up and re-raise the original exception |

Every remediation decision is logged via `FixLogger` — to Langfuse
(`create_event`) when configured, and always to Python's stdlib `logging`
module (`mattgpt.self_healing` logger) as the source of truth in dev.

## Interface

```python
from mattgpt.self_healing import self_healing

@self_healing(
    validate_result=lambda r: r is not None,
    backup=backup_query_metric,
    decompose=None,
    max_glitch_attempts=3,
    breaker_fail_max=3,
    breaker_reset_timeout=30,
)
def query_metric(...): ...
```

## Non-goals

- No generic task-decomposition logic — `decompose` is a caller-supplied,
  task-specific hook.
- No generic result-validation logic — `validate_result` is caller-supplied.
- Not a general observability platform — Langfuse integration is a single
  `create_event` call per fix, not a tracing SDK wrapper.
- Circuit-breaker state is per-process, in-memory (one `pybreaker.CircuitBreaker`
  per decorated function) — no distributed/thread-safety guarantee across
  concurrent workers yet.

## Testing

`tests/test_self_healing.py` — 7 tests against dummy functions written to
fail in controlled, specific ways (a transient-then-recovers function, an
always-down function, a function returning malformed data, and a function
that always signals `WrongApproachError`), plus the Langfuse-unconfigured
logger fallback and the "breaker already open" edge case. All run fully
offline, no real Langfuse credentials required.
