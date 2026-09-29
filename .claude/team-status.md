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
- **Status:** done for this ticket (uncommitted — router work is in the worktree, awaiting Matthew's review before a commit)
- **Blocked by:** nothing
- **Done:** OpenClaw installed (2026.9.6, past the patched version for all 6 CVEs discussed in `spec/openclaw-core.md`) and hardened non-interactively — loopback-only gateway, no channels, no ClawHub skills, telemetry off, `update.checkOnStart=false`; evidence and a correction to the spec's CVE reasoning logged in `spec/openclaw-core.md`. Ollama running locally with `llama3.2`. Router built: `route_question(question, *, model="llama3.2", max_retries=1) -> AnalysisSpec` in `mattgpt/router/`, with a `mock_stats` layer shaped to match Window B's `StatResult` field names. 13/13 tests pass against the live model; 9/12 canned questions hit the expected tier — the 3 misses (all under-escalation on causal/regime-change language) are written up in `demo/router-examples.md`.

## Window D — self-healing
- **Owns:** retry/backoff, circuit-breaker, fault classification, fix logging
- **Branch / worktree:** not yet created
- **Status:** not started
- **Blocked by:** nothing (building against dummy failing functions per its ticket)
- **Done:** —

## Window E — dev-harness
- **Owns:** ECC setup, remaining `spec/` files
- **Branch / worktree:** none — docs-only ticket, done directly in the main worktree. Heads up: the main worktree's current branch is `stats-core` (Window B's), which has its own uncommitted changes (`pyproject.toml`, `mattgpt/stats/`, `tests/stats/`) — don't `git add -A`/blind-commit here, it'd sweep those in too.
- **Status:** done for this pass, one conflict flagged below needs Matthew to reconcile
- **Blocked by:** nothing
- **Done:** ECC assessed (real, active, MIT-licensed repo per direct GitHub API check — recommended as an opt-in pilot on one ticket, not a wholesale replacement of the current CLAUDE.md/roadmap.md/review.md process). Drafted `spec/ground-truth-validation.md` and `spec/tier3-causal-inference.md` from `MattGPT-Outline.md`. OpenClaw evaluated, found to have a real CVE history (CVE-2026-25253 and others), then **decision revised**: building on OpenClaw's core is acceptable under mandatory hardening (loopback-only gateway, no messaging integrations, no ClawHub skills, untrusted content always treated as data) — most of the CVE chain requires a foothold these steps close off. Full reasoning and setup in `spec/openclaw-core.md`, now owned by Window C.
- **⚠️ Conflict flagged, not resolved:** this file previously stated hermes-agent was "evaluated and passed on (has a real open bug — 11.7% tool-call failure on a batch schema edge case — but otherwise healthy)." I independently checked hermes-agent's actual open-issue backlog via the GitHub REST + Search APIs this pass and found no basis for that specific figure anywhere in this repo (no spec file, no demo write-up, nothing greppable), while my own check turned up a very different picture: ~14,000 open issues (excluding PRs), heavily bot-filed/bot-triaged (`from-pain-miner`, `from-benchmark-scout`, `sweeper:*` labels), only ~4% explicitly labeled `bug`, ~7% unconfirmed (`needs-repro`). I did not overwrite the "11.7%" claim in case it came from real verification I can't see (e.g. actually running the tool, which I didn't do) — but the two accounts don't reconcile as written. Matthew: which one should stand, or were these testing two different things (backlog health vs. actually running it)?

## Integration notes
- Windows B/C/D are intentionally building against agreed contracts, not each other's live code — no merge needed until each is independently reviewed.
- Window A's schema is the one contract the others should eventually reconcile against; not a blocker to starting.
