# Review checklist — the quality bar

Before calling any change done, check it against these and sort issues into **must fix**, **should fix**, **okay to ship**.

## Statistical/causal rigor (the core differentiator — hold this to a high bar)

- Does the output correctly distinguish descriptive, associative, and causal claims? Never let a Tier 1/2 (descriptive/regression) result get stated as if it were causal.
- Is a confounder check performed before an association is presented as meaningful?
- Is a data-sufficiency/power check performed before any causal claim is allowed through?
- Does every finding state a confidence level and what would change it?
- If multiple hypotheses were tested against the same data, is multiple-comparisons risk addressed?
- Does time-series validation use forward-chaining (expanding window), never a random shuffle-split that leaks the future into the past?
- Would this finding survive being wrong — i.e., does the system have a way to flag it as stale after a life event or enough new data arrives?

## Safety / self-healing

- Does a failure get named (glitch / tool down / data issue / wrong approach), not just surfaced as a generic error?
- Is the remediation matched to the failure type (retry vs. switch to backup vs. decompose), not a blind retry every time?
- Is every fix logged with what broke, what was done, and the outcome?

## Data handling

- Are OAuth credentials, tokens, or personal outcome data (grades, interview results, bet logs) ever logged in plaintext or committed to the repo?
- Does a change touching the data schema or ingestion pipeline handle missing/gapped data (strap not worn, charging) instead of assuming clean input?

## Product principles

- Does this change introduce anything engagement-bait-shaped (a guilt streak, points for app-opens, a social comparison)? If so, it doesn't ship — see `MattGPT-Outline.md` §11.
- Is the change small enough to review in a diff, and does it match the current `roadmap.md` focus rather than drifting into an out-of-scope module?
