# MattGPT — Project Outline

*MattGPT is Matthew's personal agent project — built mostly by coordinating existing open-source tools and frameworks rather than building everything from scratch.*

A personally-owned agent that joins Fitbit/Google Health data with calendar and self-logged real-world outcomes, and answers analytical questions about your own life with real statistical/causal rigor — including telling you honestly when it doesn't have enough evidence to claim something.

## 1. Problem

Every commercial wearable coach (Google Health/Gemini Coach, Whoop Coach, Oura Advisor) has a structural conflict of interest: they need daily engagement to justify a subscription, so they're incentivized to always have something encouraging to say. That pushes toward presenting correlation as insight — a documented, named criticism of this entire product category.

## 2. User

Matthew — a Notre Dame student with a real Fitbit strap already in hand. This only works because the builder and the single subject being studied are the same person.

## 3. Differentiator (structural, not a feature gap)

- No commercial app can validate its claims against outcomes only you know (a grade, an interview result) — they don't have access to that ground truth.
- No commercial app lets you inspect the methodology — every "readiness score" or "correlation engine" is a black box.
- No commercial app will ever audit its own score's validity for you, or admit "not enough data to claim this" — bad for a subscription pitch, correct science.
- No commercial app can access the idiosyncratic personal variables only you'd bother logging.

**Occupied categories to avoid re-pitching:** Google Health/Gemini Coach ($9.99/mo), Whoop Coach, Oura Advisor, Lifestack (biometric-driven scheduling), Observa (a "correlation engine"), Meta Muse and general personal-life assistants. The gap that survives all of these is specifically rigor + ground-truth validation + inspectability — not data access, not coaching, not correlation-finding.

## 4. Architecture: Compute, Then Explain

Core principle: the LLM never does the math. A statistical/ML layer computes baselines, trends, and anomalies first; the agent only interprets and explains the result.

- **Data layer** — ETL from Google Health API (Takeout export first, then live API in OAuth Testing mode) + Google Calendar + self-logged outcome variables, into one structured, owned database. Handles real-world mess: gaps when the strap isn't worn, timezone shifts, inconsistent sampling. No third-party aggregator (Terra/Spike) needed for a single-provider (Fitbit) setup — data flows straight from Google to a database you control.
- **Tiered inference engine**, routed by question difficulty:
  - *Tier 1 — descriptive:* rolling averages, simple correlation, no causal claim implied.
  - *Tier 2 — controlled association:* regression/mixed-effects models with confounders controlled, using proper methods for autocorrelated time series.
  - *Tier 3 — causal:* observational N-of-1 counterfactual inference, and/or real controlled experiments (alternating-day protocols). Gated by an explicit data-sufficiency check.
- **Agent + tool-calling layer** — a real multi-step investigative agent, not a single translation step:
  - Tools: `query_metric`, `check_data_sufficiency`, `check_confounders`, `run_tier1/2/3`, `propose_experiment`, `log_finding`.
  - Loop: investigate iteratively (check a correlation, check for a confounder, decide whether to control and re-run, decide whether the evidence clears the causal bar) rather than answering in one pass.
  - Memory: a persistent ledger of hypotheses tested/confirmed/disproven.
  - Optional (NEXT): autonomous hypothesis generation, guarded against p-hacking with multiple-comparisons correction.

## 5. Use Case Pillars

- **Ground-truth validation (flagship).** Log exam grades, interview results, or subjective outcome ratings, and test whether any biometric signal actually predicted them — something no commercial app can build, since they don't have access to your outcomes.
- **Audit the commercial scores.** Test whether a readiness-style score actually predicts anything for you personally.
- **Calendar + health scheduling questions.** Rigorously test things like whether meeting load predicts worse next-day recovery, including the honest "not enough data yet" answer.
- **Sports gambling — decision-quality science, not betting optimization.** Bet logs from FanDuel/DraftKings CSV export, evaluated against **Closing Line Value (CLV)** rather than win/loss (which is dominated by variance). Framed as self-awareness ("sit out when the data says decision quality is low"), and a case no health company could ever build for brand-safety/regulatory reasons.
- **Subjective-vs-objective mismatch detector.** Daily self-logged mood/stress vs. what the body's data shows.
- **Life-event regime-change analysis.** Did your baseline actually shift after a self-defined major event?

## 6. The ML Research Question

Compare three models predicting a target metric (e.g. tomorrow's HRV), tracked as personal data accumulates:

| | Day 1 | Day 10 | Day 30 | Day 100 | Day 365 |
|---|---|---|---|---|---|
| Population model (baseline) | MAE | MAE | MAE | MAE | MAE |
| Population + personal features | MAE | MAE | MAE | MAE | MAE |
| Fully personal model | MAE | MAE | MAE | MAE | MAE |

Does personalization measurably help, by how much, and when does a personal model overtake the population baseline? A real, reportable result — not a hand-wave.

## 7. Technical Depth

- **Data engineering:** messy real-world export parsing, time-series + calendar schema design, a queryable API layer, timezone-aware joins.
- **Statistics/causal inference (the deepest part):** trend/seasonality decomposition, confounder-controlled regression on autocorrelated data, N-of-1 causal methodology, multiple-comparisons correction, time-aware (forward-chaining) validation.
- **Agent/AI layer:** NL question → structured analysis spec, the router, caveated answer generation, calibration evaluation.
- **Systems/backend:** OAuth (own Google Cloud project, Testing mode), background sync jobs, caching, observability/logging (doubles as the calibration eval dataset), security (this touches grades and interview outcomes, not just step counts).
- **Honest gap:** no natural fit for RAG/embeddings/semantic search — the data is structured/numeric, not a document corpus.

## 8. Prior Art to Cite Honestly (not reinvent)

- **QuantifyMe** — open-source single-case experimental design platform.
- **N1RT / g-formula counterfactual frameworks** — published single-subject causal inference methodology.
- **NeuroKit2** — open-source HRV feature extraction pipeline.
- **Terra / Spike / Thryve / Validic** — unified wearable data APIs, relevant only if a second provider (beyond Fitbit) is ever added; not needed for v1.

## 9. Data Access Plan

1. **Now:** Google Takeout export ("Fitbit" category) for full historical data — no API wait, no OAuth setup.
2. **Next:** Google Health API in **OAuth Testing mode**, self as a test user — exempt from the full restricted-scope verification review since this is personal use, not a public app.
3. Own Google Cloud project and OAuth client — not a third-party aggregator, not claude.ai's connectors (which are chat-session-scoped and not embeddable in external software).

## 10. Scope

- **NOW:** Takeout-based historical data; calendar join; Tiers 1–2; one ground-truth outcome type (start with grades); the population-vs-personal MAE comparison as the first reportable result.
- **NEXT:** Live sync via Testing-mode OAuth; Tier 3 causal inference (observational + real experiments); the "audit the commercial score" feature; the sports-gambling CLV module, if pursued.
- **LATER:** Health Connect live mobile sync; full-history reprocessing pipeline as methodology improves; multi-provider support (Terra/Health Connect) if a second device is added; any multi-user/"is there a startup" question — explicitly deferred.
- **Not needed:** rebuilding a unified wearable API; a general personal-life-assistant framing; positioning this as a coaching product.

## 11. Gamification — Gamify the Science, Not the Usage

The project's differentiator is being honest instead of engagement-bait — standard gamification (streaks, points for opening the app) is exactly the manipulative mechanic this project is defined against.

- **Experiment compliance, not app-opens** — reward finishing a full N-of-1 protocol, not daily check-ins.
- **"Confirmed findings" as the real currency** — a running tally of hypotheses tested vs. ones that held up, honestly stated even when most don't.
- **Calibration game against your own model** — predict tomorrow's metric yourself before checking the engine's forecast; tracks your own self-knowledge over time.
- **"Debunked myth" badges** — celebrate when a believed hypothesis gets disproven by the data.
- **Sample-size progress, not a streak bar** — show statistical power accumulating toward a specific question.
- **Self vs. self, never a social leaderboard** — compare this quarter's accuracy/discipline against your own past quarter, kept private.
- **A finding card, not a share prompt** — a one-time summary artifact when a controlled experiment concludes with a confident result.

**Anti-patterns to avoid:** guilt streaks, points for app-opens, infinite-scroll dashboards, engagement-timed notifications, any social comparison mechanic.

## 12. Self-Healing Agent Layer

A cross-cutting reliability property applied to every tool call and computation the agent makes — not a separate module. Extends the "harness, not wrapper" principle from earlier: a harness keeps working and gets better with every job, rather than silently failing or guessing.

1. **Check its own work.** After any tool call or computed result, validate it against an expected shape/range before trusting it (did the regression actually converge, does the confidence interval make sense, did a tool return real data or an error). Known in agent research as a reflection/verification pass.
2. **Name what broke.** Classify failures into a small taxonomy rather than a generic error: transient glitch, tool/service unavailable, data issue, or the approach itself doesn't fit the task.
3. **Match the fix to the failure type:**
   - *Glitch* → retry with backoff — the standard retry/backoff pattern.
   - *Tool down* → switch to a backup — the circuit-breaker pattern. This is also why the model layer should already be a fallback chain (e.g., local Ollama model unavailable → fall back to a Hugging Face-hosted alternative), not a single hardcoded call.
   - *Keeps failing* → decompose the task into smaller sub-steps and retry the decomposed version, rather than blindly repeating the same failed approach (the "Reflexion"-style retry pattern from agent literature).
4. **Log every fix.** Every failure, its classification, the remediation applied, and the outcome — feeding the same audit trail as the findings ledger.

**Pull from existing work, don't build from scratch:** `tenacity`/`backoff` (retry logic), `pybreaker` or a minimal circuit-breaker (fallback switching), **Langfuse** (open-source, self-hostable tracing/logging) for the fix-audit trail rather than a custom logging system.

---

*Full brainstorm and discussion history: [MattGPT Brainstorm doc](https://claude.ai/artifact/AZYREd7npkucHr4S6BDbWE)*
