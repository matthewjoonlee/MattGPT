# Roadmap — current focus

## Current phase: Phase 0 — Data foundation

Set up the Google Cloud project + OAuth client (Testing mode, self as test user), pull a Google Takeout export of Fitbit/Google Health data, design the structured schema (biometric time series + calendar + self-logged outcomes), and get real historical data loaded into a local, queryable database (SQLite to start).

**Definition of done for this phase:** a working database, populated with real historical Fitbit data, that can answer a simple descriptive query (e.g., "what was my average resting heart rate last month") without any model call — pure code.

## Out of scope right now

- Tier 3 causal inference / controlled experiments
- The router and any model integration (Ollama, Jev, Hugging Face) — see `spec/local-model-layer.md` for the plan once this phase starts
- Self-healing layer
- Gamification mechanics
- Calendar integration
- The gambling / audit-the-commercial-score / life-event modules

Keep this file updated as the current phase changes — see `MattGPT-Outline.md` §"Roadmap" for the full phase sequence (0–9) this rolls through over time.
