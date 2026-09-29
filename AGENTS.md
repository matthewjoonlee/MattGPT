# MattGPT — Operating Manual

MattGPT is Matthew's personal agent — a causally-rigorous inference engine over Fitbit/Google Health data, calendar, and self-logged real-world outcomes. Full design reference: `MattGPT-Outline.md`.

## Working style

- Small, reviewable changes. Explain the plan before editing anything that touches the data schema, the inference engine's statistical methods, or OAuth/credentials.
- Keep changes focused on the current ticket — don't drift into unrelated modules.
- Use the existing code style once one is established; don't introduce a new pattern for something already solved.
- After editing, run relevant checks/tests before declaring something done.
- Summarize: what changed, what was tested, what still needs human review.

## Core principles (see `MattGPT-Outline.md` for full detail)

- **Compute, then explain.** A statistics/ML layer computes baselines, trends, anomalies, and causal estimates. The LLM only interprets and explains — it never does the math itself.
- **State confidence honestly.** Every finding says how confident it is and what would change that. "Not enough data to claim this yet" is a valid, preferred answer over a guess.
- **No engagement-bait.** No streaks that guilt a missed day, no points for opening the app, no social comparison. See `MattGPT-Outline.md` §11 for the full gamification anti-pattern list.
- **Self-healing.** Every tool call/computation checks its own work, names what broke (glitch / tool down / data issue / wrong approach), matches the fix to the failure type (retry / switch to backup / decompose and retry), and logs every fix. See `MattGPT-Outline.md` §12.
- **Pull from existing work.** Don't rebuild what's already solved well (Google Health API for data access, `tenacity`/`pybreaker` for retry/circuit-breaking, Langfuse for tracing, QuantifyMe/N1RT methodology for causal inference). Reserve original work for the actual differentiator: the rigor and the ground-truth validation layer.

## Build philosophy: depend, fork, or reimplement

Most of this project should be assembled from existing work, not built from scratch. For any external code, pick one of three modes deliberately — don't default to copying code when depending on it would do:

- **Depend on it as-is** (pip/npm install, no code copied) — the library already does exactly what's needed and is actively maintained. Preferred whenever it fits: you get upstream bug fixes for free and own none of their code.
- **Fork/vendor and strip down** — needed when you have to change internals, or the project is a whole platform and only one piece of it is wanted. Real cost: you now own bugs in code you didn't write and must track upstream changes manually.
- **Read as reference, reimplement your own simplified version** — right when the existing thing is academic paper code or built for infrastructure this project doesn't use. Take the method, not the code.

Before forking or vendoring anything, check its license — this project is portfolio material shown to recruiters, so depending on a package rather than copying it sidesteps license questions entirely whenever that option is available.

**Current mapping** (update as new dependencies are added):

| Piece | Mode |
|---|---|
| Google Health API / Calendar API | Depend |
| `tenacity`/`backoff`, `pybreaker` | Depend |
| NeuroKit2 (HRV extraction) | Depend |
| Langfuse | Depend (self-hosted) |
| Ollama models | Depend |
| FitOut (Takeout parser) | Depend, but check it handles the current export format first |
| QuantifyMe | Fork + strip down to its N-of-1 experiment-design logic |
| N1RT counterfactual framework | Read as reference, reimplement — academic code, not a maintained library |
| OpenClaw core (memory, skill execution, multi-provider abstraction) | Depend, under mandatory hardening — see `spec/openclaw-core.md`. Real CVE history (e.g. CVE-2026-25253); decision made knowingly, not despite not knowing. Gateway bound to loopback only, no messaging integrations, no ClawHub third-party skills, ever |
| numpy / pandas / scipy / statsmodels | Depend — Tier 1-3 statistical/causal core (STL decomposition, HAC regression, power analysis, FDR correction). See `spec/stats-core.md` |
| pytest | Depend (dev) — test runner |

Each new `spec/` file should state which mode applies to any external dependency it introduces.

## Where things live

- `roadmap.md` — what matters *right now*, this phase, and what's explicitly out of scope.
- `review.md` — the quality bar; check changes against this before calling them done.
- `context/` — condensed project context and principles.
- `self/` — Matthew's own current goals/circumstances (the "customer notes" of a project whose customer is its builder).
- `spec/` — one file per feature/module (router, self-healing, ground-truth validation, etc.).
- `demo/` — example query walkthroughs.
- `routines/` — recurring/scheduled task definitions.
- `MattGPT-Outline.md` — the full brainstorm and design reference.
