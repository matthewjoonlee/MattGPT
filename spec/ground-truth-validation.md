# Ground-truth validation — spec

The flagship differentiator (`MattGPT-Outline.md` §5, §10 NOW list — "one ground-truth outcome type, start with grades"). Implementation depends on the Tier 1/2 inference engine existing first, which isn't specced yet — this file documents the design now, per `spec/README.md`'s "written before it's built."

## What it's for

Log real outcomes only Matthew knows (exam grades, interview results, subjective ratings) and rigorously test whether any biometric signal actually predicted them — the thing no commercial wearable coach can do, since they have no access to your ground truth. "Not enough evidence to claim this yet" is a valid, preferred output, not a failure state.

## Dependency mode

Per `CLAUDE.md`'s build-philosophy table:

- **Outcome storage** — extends the Phase 0 database schema with a new table. No new external dependency.
- **Statistical testing** — reuses whichever Tier 1/2 regression stack gets chosen when that spec is written (depend on it; don't build a parallel stats path just for this feature).
- **Outcome logging itself** — no third-party service. Matches the outline's framing that this only works because the idiosyncratic personal variables are ones Matthew bothers to log himself.

## Data model

An outcome-log entry:

| Field | Notes |
|---|---|
| `timestamp` | when the outcome occurred (not when it was logged) |
| `outcome_type` | enum: `grade`, `interview_result`, `subjective_rating`, `custom` |
| `value` | numeric or ordinal-encoded |
| `scale` | required for `subjective_rating` — must be fixed and consistent over time (e.g. always 1–10) so entries stay comparable |
| `note` | optional free text |
| `source` | always `self_logged` for now |

Handle real irregularity: grades and interview results don't arrive on a daily cadence — the schema can't assume one observation per day the way biometric time series roughly can.

## Validation workflow

Each step ties to a `review.md` rigor requirement — this is the enforcement mechanism, not a suggestion:

1. **Data-sufficiency check first.** Before touching a candidate biometric signal, confirm there are enough paired (biometric, outcome) observations to attempt a Tier 2 association at all. Fail closed: return "not enough data" rather than run a underpowered model.
2. **Candidate signal selection.** Which biometric features are being tested against this outcome type, and over what window before the outcome event (e.g. resting HR / HRV / sleep score / step count in the 3 days leading up to an exam).
3. **Confounder check.** Identify plausible confounders (day-of-week, semester timing, cumulative sleep debt) before any correlation is presented as meaningful.
4. **Tier 2 controlled-association test.** Regression/mixed-effects with confounders controlled, using time-series-appropriate methods. This is this spec's ceiling — no causal claim is made here. (Causal claims are `spec/tier3-causal-inference.md`'s job, and only after its own data-sufficiency gate clears.)
5. **Multiple-comparisons correction.** Applies whenever more than one candidate biometric signal is tested against the same outcome type in one pass.
6. **Confidence statement + staleness trigger.** Every finding states its confidence and what would change it (more data, a declared life event). Findings are flagged stale after a life event or after enough new data arrives to warrant a re-run.
7. **Log to the findings ledger.** Joins the same persistent hypothesis ledger described in `MattGPT-Outline.md` §4 (tested / confirmed / disproven).

## Self-healing hooks

Named failure types specific to this feature, matched to the remediation from `review.md`'s safety checklist — not a blind retry in every case:

- **Data issue — outcome logged inconsistently** (e.g. some exams logged, others not) → surface the gap, don't silently drop or interpolate grades.
- **Data issue — biometric gap near the outcome date** (strap not worn, device not synced) → name the gap explicitly in the finding rather than treating missing as zero.
- **Wrong approach — sample too small for Tier 2** (e.g. three logged exams) → this is not a retry-able glitch; the honest answer is "not enough data yet," stated plainly.

## Anti-pattern guard

Every output here ties to one specific, named outcome the user logged, with a stated confidence level. This must never collapse into a generic "readiness score" — that's exactly the black-box pattern this project is defined against (`MattGPT-Outline.md` §11, `review.md` product principles).

## Open questions for Matthew

- What's the fixed scale for `subjective_rating` (1–10? categorical buckets?) — needs to be decided once, since changing it later breaks comparability across entries.
- Where does outcome logging actually happen — a CLI command, a simple form, something else? Not decided by this spec.
