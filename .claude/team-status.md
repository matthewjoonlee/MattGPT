# Team status

Shared coordination file, lives only in the main worktree. Every window reads this before starting work and updates its own section as it goes. Use `SendMessage` for anything time-sensitive (a dependency unblocking) — don't rely on this file being watched live.

## Window A — data-ingestion
- **Owns:** Google Health API + Google Calendar OAuth, schema design, ingestion pipeline, `get_metric(name, date_range)` interface
- **Branch / worktree:** `worktree-data-ingestion` at `.claude/worktrees/data-ingestion`
- **Status:** worktree created, work not yet confirmed started
- **Blocked by:** nothing
- **Done:** —

## Window B — stats-core
- **Owns:** Tier 1/2/3 statistical/causal inference methods
- **Branch / worktree:** `stats-core`, main worktree
- **Status:** done for this ticket, uncommitted — awaiting Matthew's review before a commit
- **Blocked by:** nothing (built and tested against synthetic data per its ticket)
- **Done:** `mattgpt/stats/` — Tier 1 (`tier1.py`: rolling baseline, STL trend/seasonality decomposition, z-score anomaly detection), Tier 2 (`tier2.py`: `check_confounders` + `fit_controlled_regression` with HAC/Newey-West standard errors — confounder check is a required argument, even for a bare bivariate association; `forward_chaining_splits` for expanding-window validation), Tier 3 (`tier3.py`: `check_data_sufficiency` power-analysis gate that `estimate_n_of_1_effect` always runs itself before producing a causal estimate — a simplified g-formula reimplementation, observational only, no experiment scheduling), shared `results.py` (`StatResult` + Benjamini-Hochberg `apply_multiple_comparisons_correction`), and `schema.py`/`synthetic.py` (the `BiometricRecord` schema + a synthetic-data generator with baked-in ground-truth effects). 18/18 tests pass in `tests/stats/`, including recovery of the generator's known confounder and known causal effect size. Confirmed our `StatResult` fields are a superset of Window C's `MockStatResult` guess — no rename needed when they swap it in. New spec: `spec/stats-core.md`; `roadmap.md`/`CLAUDE.md` updated for this parallel track. **Found and fixed a cross-window conflict:** an earlier edit this session overwrote `pyproject.toml` instead of merging into it, dropping Window D's `tenacity`/`pybreaker`/`langfuse` deps and loosening the `requires-python`/`pytest` pins — restored and merged, tests re-verified against the pinned `pytest<9`.

## Window C — router-local-models (now also owns the agent shell)
- **Owns:** Ollama setup, router (question → tier + structured spec), **OpenClaw core as MattGPT's agent shell** — see `spec/openclaw-core.md`
- **Branch / worktree:** `worktree-router-local-models` at `.claude/worktrees/router-local-models`
- **Status:** router ticket committed and pushed to `origin/worktree-router-local-models` (commit `4dc565a`); awaiting Matthew's review before merge. Telegram channel (his ask, safest-messaging-integration follow-up) is planned but not yet implemented — waiting on him to create a bot via @BotFather and hand over the token.
- **Blocked by:** nothing
- **Done:** OpenClaw installed (2026.9.6, past the patched version for all 6 CVEs discussed in `spec/openclaw-core.md`) and hardened non-interactively — loopback-only gateway, no channels, no ClawHub skills, telemetry off, `update.checkOnStart=false`; evidence and a correction to the spec's CVE reasoning logged in `spec/openclaw-core.md`. Ollama running locally with `llama3.2`. Router built: `route_question(question, *, model="llama3.2", max_retries=1) -> AnalysisSpec` in `mattgpt/router/`, with a `mock_stats` layer shaped to match Window B's `StatResult` field names. 13/13 tests pass against the live model; 9/12 canned questions hit the expected tier — the 3 misses (all under-escalation on causal/regime-change language) are written up in `demo/router-examples.md`. Pushed to `origin/worktree-router-local-models`.

## Window D — self-healing
- **Owns:** retry/backoff, circuit-breaker, fault classification, fix logging
- **Branch / worktree:** `worktree-self-healing` at `.claude/worktrees/self-healing` (branched off `main`, not `stats-core` — deliberately avoids Window B's uncommitted changes sitting in the main worktree)
- **Status:** done for this ticket, uncommitted — awaiting Matthew's review before a commit
- **Blocked by:** nothing (built and tested entirely against dummy failing functions, no dependency on A/B/C's actual code)
- **Done:** `mattgpt/self_healing/` — `taxonomy.py` (`FailureType` enum: glitch/tool_down/data_issue/wrong_approach; `WrongApproachError`/`DataIssueError`), `classify.py` (deterministic predicate-table `classify_failure` — no model call; `DataIssueError` is checked first, unconditionally, so it's never overridden by retry/backup-exhaustion bookkeeping), `retry.py` (tenacity `Retrying` wrapper, retry predicate itself is the classifier — a non-glitch failure stops the loop immediately instead of burning attempts), `breaker.py` (pybreaker `CircuitBreaker` + `call_with_backup`), `logging_sink.py` (`FixLogger` — Langfuse `get_client()`/`create_event()` best-effort, always also logs via stdlib `logging`; confirmed against installed `langfuse==4.15.4` source directly, not guessed, since construction never raises on missing credentials but the whole call is still wrapped defensively), `decorator.py` (`self_healing(...)` — the interface other modules apply to their own tool calls, see signature below). 7/7 tests pass in `tests/test_self_healing.py`, fully offline, no real Langfuse credentials needed, including one that caught a real bug during implementation (pybreaker wraps the exception that *trips* the breaker as `CircuitBreakerError` right on that same call, not the raw exception — test updated to assert on that and confirm the original exception is still chained via `__context__`). New spec: `spec/self-healing.md`; `roadmap.md` updated (removed self-healing from "out of scope," added a parallel-track note) — **not yet reconciled against Window B's own uncommitted `roadmap.md` edit**, since this ticket branched off `main` rather than the dirty `stats-core` checkout; needs a merge-time diff resolution, flagging for Matthew.

  **The public interface:**
  ```python
  from mattgpt.self_healing import self_healing, DataIssueError, WrongApproachError

  @self_healing(
      validate_result=lambda r: r is not None,   # optional "check its own work" hook
      backup=backup_query_metric,                # optional, tried once if the breaker trips
      decompose=None,                             # optional, tried once if glitch+backup both exhaust
      max_glitch_attempts=3,
      breaker_fail_max=3,
      breaker_reset_timeout=30,
  )
  def query_metric(...): ...
  ```
  `validate_result`/`decompose` are deliberately caller-supplied — the module doesn't invent generic result-validation or task-decomposition logic, both being task-specific by nature.

## Window E — dev-harness
- **Owns:** ECC setup, remaining `spec/` files
- **Branch / worktree:** none — docs-only ticket, done directly in the main worktree. Heads up: the main worktree's current branch is `stats-core` (Window B's), which has its own uncommitted changes (`pyproject.toml`, `mattgpt/stats/`, `tests/stats/`) — don't `git add -A`/blind-commit here, it'd sweep those in too.
- **Status:** done for this pass, one conflict flagged below needs Matthew to reconcile
- **Blocked by:** nothing
- **Done:** ECC assessed (real, active, MIT-licensed repo per direct GitHub API check — recommended as an opt-in pilot on one ticket, not a wholesale replacement of the current CLAUDE.md/roadmap.md/review.md process). Drafted `spec/ground-truth-validation.md` and `spec/tier3-causal-inference.md` from `MattGPT-Outline.md`. OpenClaw evaluated, found to have a real CVE history (CVE-2026-25253 and others), then **decision revised**: building on OpenClaw's core is acceptable under mandatory hardening (loopback-only gateway, no messaging integrations, no ClawHub skills, untrusted content always treated as data) — most of the CVE chain requires a foothold these steps close off. Full reasoning and setup in `spec/openclaw-core.md`, now owned by Window C.
- **⚠️ Conflict flagged — resolved (by the orchestrating session, not Matthew):** both figures are real, and they're measuring different things, not contradicting each other. The "11.7%" came from one specific GitHub issue in hermes-agent's tracker, explicitly titled around a tool_call schema mismatch, quoting that exact impact figure — not fabricated, but it describes *one already-identified bug's* blast radius, from a shallow sample of the 30 most recent issues. Window E's ~14,000-issue, bot-filing-pattern-aware audit (`from-pain-miner`/`from-benchmark-scout`/`sweeper:*` labels, ~4% actually `bug`-labeled) is a materially more thorough read on overall *backlog health/composition* and should be treated as the authoritative one going forward — it supersedes the earlier, shallower impression. No architectural consequence either way: hermes-agent was never adopted (OpenClaw was, instead), so this is a correction to the historical record, not a pending decision.

## Integration notes
- Windows B/C/D are intentionally building against agreed contracts, not each other's live code — no merge needed until each is independently reviewed.
- Window A's schema is the one contract the others should eventually reconcile against; not a blocker to starting.

## Merged to main — 2026-09-29

All four branches (`worktree-data-ingestion`, `stats-core`, `worktree-self-healing`, `worktree-router-local-models`) are merged into `main` and pushed to `origin/main`. Two real conflicts resolved by hand: `pyproject.toml` (each branch added its own deps — unioned, nothing dropped) and `roadmap.md` (stats-core's and self-healing's "Parallel track" sections — kept both, the "Out of scope" list had already merged cleanly on its own). Also cleaned up: three `.claude/worktrees/*` gitlink entries that had been accidentally committed on `stats-core` (nested-worktree artifacts, not real submodules) — removed from tracking, `.claude/worktrees/` now gitignored so this can't recur. Full suite verified after merge: **54/54 tests pass**.

Windows continuing work should now branch/rebase from `origin/main`, not the old feature branches — those still exist on the remote but are fully absorbed.
