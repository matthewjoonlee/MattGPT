# MattGPT — Features

## Ask real questions, get rigorously-tiered answers
- Ask a natural-language question about your own health/life data and get an answer at the right level of rigor — descriptive, confounder-controlled association, or real causal inference — chosen automatically, not guessed.
- Get an honest "not enough data to claim this yet" instead of a forced answer when the evidence doesn't support one.
- Every answer states its confidence and what would change it — no black-box score.

## Ground-truth validation (the flagship differentiator)
- Test whether any biometric signal actually predicted a real outcome you log yourself — a grade, an interview result, a subjective "how did that go" rating.
- Audit a commercial wellness score (Oura/Whoop-style) against your own outcomes to see if it means anything for you personally, or is noise.

## Calendar + health reasoning
- Ask scheduling questions grounded in your actual data — does meeting load predict worse next-day recovery, is there a real high-readiness window — with the honest "sample too small" answer when that's true.

## Decision-quality science
- Sports gambling module: evaluates decisions against Closing Line Value (not win/loss, which is noise-dominated), framed as self-awareness ("sit out when the data says decision quality is low"), not betting optimization.
- Subjective-vs-objective mismatch detector: flags days your self-logged mood/stress disagreed with what your body's data showed.
- Life-event regime-change analysis: tests whether your baseline actually shifted after a self-defined major event, not just a rolling trend.

## The measurable research result
- Tracks population-model vs. personal-model prediction accuracy (MAE) over time — a real, reportable answer to whether personalization is actually working, not a marketing claim.

## Reliability (self-healing)
- Checks its own work before trusting a result.
- Names what broke (glitch / tool down / data issue / wrong approach) instead of a generic error.
- Matches the fix to the failure — retries, falls back to a backup, or breaks the task down — rather than one blind response to every failure.
- Logs every fix, building an audit trail that also seeds recalibration over time.

## Motivation without manipulation
- Rewards finishing a full experiment protocol, not opening the app.
- Tracks "confirmed findings" honestly, including a "debunked myth" badge when a hypothesis you believed turns out false.
- A calibration game against your own predictions, and self-vs-self progress — never a social leaderboard or guilt streak.

## Cost and ownership
- Runs on free/local models (Ollama) plus near-zero-cost classification (Jev) — no meaningful ongoing API spend.
- Connects directly to the Google Health API and Google Calendar API — no third-party aggregator, full ownership of where the data ultimately lives.
