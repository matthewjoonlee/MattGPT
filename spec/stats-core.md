# Statistical/causal inference core (Tier 1-3) — spec

Belongs to Phase 1 (statistical core) per `spec/local-model-layer.md`'s phase reference, but built now as a parallel track against synthetic data — see `roadmap.md`'s "Parallel track" note. Not blocked by, and doesn't block, Phase 0 (real data ingestion).

## Dependency mode

- **numpy, pandas, scipy, statsmodels** — Depend, per `CLAUDE.md`'s build-philosophy table. All actively maintained, MIT/BSD-licensed, and do exactly what's needed (STL decomposition, OLS with HAC/Newey-West standard errors, power analysis, Benjamini-Hochberg FDR correction). No reason to fork or reimplement any of it.
- **N1RT / g-formula counterfactual methodology** — Read as reference, reimplement. Academic methodology, not a maintained library (per `CLAUDE.md`'s existing table entry). `mattgpt/stats/tier3.py`'s `estimate_n_of_1_effect` is a simplified g-formula: fit an outcome model, then predict each observation's counterfactual outcome under both exposure states and average the difference.
- **QuantifyMe** — not touched by this spec. Its N-of-1 experiment-*design* logic (randomization, alternating-day scheduling) is explicitly out of scope here; see "What this doesn't cover" below.

## What this covers

Pure-code compute layer, no model calls (`CLAUDE.md`'s "compute, then explain"):

- **Tier 1** (`mattgpt/stats/tier1.py`) — descriptive only: rolling baseline, STL trend/seasonality decomposition, z-score anomaly detection against the rolling baseline. No causal or associative claim implied.
- **Tier 2** (`mattgpt/stats/tier2.py`) — confounder-controlled association: `check_confounders` flags candidate confounders correlated with both predictor and outcome; `fit_controlled_regression` requires that check's result before it will run (even for a bare bivariate association, checked against an empty candidate pool) and fits OLS with HAC (Newey-West) standard errors for autocorrelated data. `forward_chaining_splits` gives an expanding-window (never shuffled) train/test split generator.
- **Tier 3** (`mattgpt/stats/tier3.py`) — observational N-of-1 causal estimation only: `check_data_sufficiency` runs a power analysis (via `statsmodels.stats.power`) against configurable minimums; `estimate_n_of_1_effect` always runs that gate itself (not caller-optional) and refuses to produce a causal estimate — returning a `descriptive`, "not enough data yet" result instead — when it fails.
- **Multiple-comparisons correction** (`mattgpt/stats/results.py`) — `apply_multiple_comparisons_correction` applies Benjamini-Hochberg FDR across a batch of `StatResult`s. Applied per investigative query/batch, not globally; deciding what counts as "one batch" belongs to the agent/router layer (not yet built).
- **Synthetic data** (`mattgpt/stats/synthetic.py`, `mattgpt/stats/schema.py`) — a `BiometricRecord` long-format schema (subject/timestamp/metric/value/source/quality) standing in for what the real ingestion pipeline (Phase 0, Window A) will eventually produce, plus a generator that bakes in known ground-truth effects so tests check recovery of a known answer, not just that code runs.

## What this doesn't cover (deferred)

- **Real controlled experiments** — randomization, alternating-day assignment, experiment lifecycle tracking. This is the QuantifyMe-fork half of Tier 3 per `MattGPT-Outline.md` §4/§8, and is a separate future ticket.
- **The agent/tool-calling loop** — deciding which tier to run, what counts as one multiple-comparisons batch, iterative investigation. `MattGPT-Outline.md` §4's tool list (`query_metric`, `run_tier1/2/3`, etc.) is the future caller of this module.
- **The full self-healing layer** — retry/backoff, circuit-breaking, a fix audit log (`MattGPT-Outline.md` §12). Each tier's result carries a `diagnostics` dict (e.g. did the regression converge) as the self-check primitive a future self-healing layer would consume, but the remediation/logging machinery itself isn't built here.
- **Real data integration** — this module has never been run against actual Fitbit/Takeout data; the synthetic schema is a best guess pending Phase 0.

## Review-checklist mapping (`review.md`)

- Descriptive/associative/causal claims are distinguished by `StatResult.claim_type`, set by the code, not left to a caller's judgment.
- Confounder check before an association: enforced in `fit_controlled_regression`'s signature (raises without a `ConfounderCheckResult`).
- Data-sufficiency check before a causal claim: enforced inside `estimate_n_of_1_effect` itself, not caller-optional.
- Multiple-comparisons risk: `apply_multiple_comparisons_correction`, tested against `statsmodels`' own reference implementation.
- Forward-chaining validation: `forward_chaining_splits` never produces a test fold that precedes its training fold (tested directly); no shuffle-split exists anywhere in this module.
