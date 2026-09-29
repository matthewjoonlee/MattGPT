# Roadmap — current focus

## Current phase: Phase 0 — Data foundation

Set up the Google Cloud project + OAuth client (Testing mode, self as test user), pull a Google Takeout export of Fitbit/Google Health data, design the structured schema (biometric time series + calendar + self-logged outcomes), and get real historical data loaded into a local, queryable database (SQLite to start).

**Definition of done for this phase:** a working database, populated with real historical Fitbit data, that can answer a simple descriptive query (e.g., "what was my average resting heart rate last month") without any model call — pure code.

## Parallel track: statistical/causal core (Tier 1-3, synthetic data)

Window B is building the Tier 1/2/3 compute layer now, against a synthetic dataset shaped like what this phase's real pipeline will produce — see `spec/stats-core.md`. This doesn't block on or block Phase 0; it's ready to be pointed at real data once Phase 0 ships. Tier 3 here means observational N-of-1 counterfactual inference only.

## Out of scope right now

- Real controlled experiments (randomization/scheduling, alternating-day protocols — the QuantifyMe-fork half of Tier 3)
- The router and any model integration (Ollama, Jev, Hugging Face) — see `spec/local-model-layer.md` for the plan once this phase starts
- Self-healing layer
- Gamification mechanics
- Calendar integration
- The gambling / audit-the-commercial-score / life-event modules

Keep this file updated as the current phase changes — see `MattGPT-Outline.md` §"Roadmap" for the full phase sequence (0–9) this rolls through over time.
