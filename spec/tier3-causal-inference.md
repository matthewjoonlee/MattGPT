# Tier 3 causal inference — spec

Explicitly out of scope for implementation right now — `roadmap.md`'s out-of-scope list for the current phase names "Tier 3 causal inference / controlled experiments" directly. Drafted now, gated behind Tiers 1–2 existing and a real data-sufficiency bar, per `MattGPT-Outline.md` §4. Per `spec/README.md`, specs are written before the feature is built.

## What it's for

The deepest differentiator: moving from "X is associated with Y after controlling for confounders" (Tier 2) to "X causes Y for this specific person" — via N-of-1 observational counterfactual methods and/or real controlled experiments, and never claimed unless an explicit data-sufficiency gate clears first.

## Dependency mode

Straight from `CLAUDE.md`'s build-philosophy table — don't re-derive these choices per-feature:

- **QuantifyMe** → fork + strip down to its N-of-1 experiment-design logic only.
- **N1RT counterfactual framework** → read as reference, reimplement a simplified version — academic code, not a maintained library, so the method is taken, not the code.
- **Shared statistical stack** (whatever Tiers 1–2 depend on) → depend, reuse as-is.

## Two methodologies (`MattGPT-Outline.md` §4)

1. **Observational N-of-1 counterfactual inference.** Uses existing historical data, no new experiment required. A g-formula-style counterfactual estimate, reimplemented from N1RT methodology. Gated on enough historical variation in the exposure variable (e.g., enough days both with and without the behavior in question) and enough outcome data around each.
2. **Real controlled experiments (alternating-day protocols).** When observational variation is insufficient to support (1), propose a real experiment — protocol design adapted from the forked QuantifyMe logic. This is the only path to a causal claim when the historical data alone doesn't clear the bar.

## Data-sufficiency gate

The single most important control in this spec, per `MattGPT-Outline.md` §4 ("gated by an explicit data-sufficiency check") and `review.md` ("is a data-sufficiency/power check performed before any causal claim is allowed through?"). Concrete, numeric, and **fail-closed** — defaults to "not causal yet," never fails open:

- Minimum N of exposure days in each arm (with vs. without).
- Minimum detectable effect size given the existing variance in the outcome.
- Power calculation adjusted for autocorrelation — a naive i.i.d. power calc overstates confidence on time series data.

## Time-series validation

Forward-chaining (expanding window) validation only, per `review.md`. A random shuffle-split is disallowed outright for this feature — it leaks future data into the past and would silently invalidate any causal claim built on it.

## Multiple-comparisons guard

Applies even when only one causal hypothesis is nominally being tested, if multiple candidate lags or exposure windows are tried against the same outcome (e.g. testing same-day vs. next-day vs. 2-day-lag effects) — correct for the number of windows tried, not just the number of named hypotheses.

## Experiment protocol tooling

`propose_experiment` (from the tool list in `MattGPT-Outline.md` §4) generates and tracks an alternating-day protocol. Compliance tracking ties to §11's gamification-of-the-science pattern — **reward finishing the full protocol, not opening the app daily.** No streak bar, no guilt mechanic; a sample-size/compliance progress indicator instead.

## Findings ledger integration

Each causal hypothesis moves through an explicit state machine — `proposed → testing → confirmed / disproven` — persisted in the same ledger described in §4, not a one-off result thrown away after the answer is given.

## Self-healing hooks

Three distinct failure types for this feature, each matched to its own remediation per `review.md`'s safety checklist — not a single blind retry path:

- **Data issue — not enough data yet.** The honest default outcome when the sufficiency gate doesn't clear. Not an error; state it plainly and stop.
- **Wrong approach — protocol broke mid-experiment** (e.g. user couldn't sustain the alternating pattern). Not retry-able as-is — decompose into a shorter/easier alternation window and re-propose, per the Reflexion-style remediation in `MattGPT-Outline.md` §12.
- **Glitch — the counterfactual model didn't converge.** A transient computation failure, not a data or design problem — retry with backoff, per the standard retry pattern.

## Explicit non-goals

- No gamification beyond the compliance-reward pattern above — no streaks, no points for app-opens (`review.md` product principles).
- Does not cover the sports-gambling CLV module or the "audit the commercial score" feature — both are separate, still-unspecced modules per `MattGPT-Outline.md` §10's NEXT list.

## Open questions for Matthew

- Which exposure variables should the first observational counterfactual pass prioritize?
- How many concurrent alternating-day protocols are realistic given current life load — `self/current-goals.md` is still a placeholder, so this spec can't answer that yet.
