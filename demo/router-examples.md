# Router examples

Canned questions run through `route_question()` (model: `llama3.2`, temperature 0),
each fed through the mocked stats layer (`mock_stats.run_mock_stats`) to confirm
the spec it produces is consumable downstream. Real numbers throughout are
placeholders — see `mattgpt/router/mock_stats.py`.

Full test run: 13/13 tests passed; 9/12 canned questions landed on the tier
listed below as "expected." The 3 mismatches are called out at the end.

## Tier 1 — descriptive

| Question | Tier | Confounder check |
|---|---|---|
| What was my average resting heart rate last month? | 1 | no |
| How many steps have I taken on average this week? | 1 | no |
| What's the trend in my sleep duration over the last 30 days? | 1 | no |
| How does my HRV today compare to my typical HRV? | 1 | no |

## Tier 2 — controlled association

| Question | Tier | Confounder check |
|---|---|---|
| Does sleep duration predict next-day HRV, controlling for how much I worked out? | 2 | yes |
| Is there a relationship between my meeting load and my resting heart rate, after accounting for how much I slept? | 2 | yes |
| Controlling for stress, does step count predict mood? | 2 | yes |

## Tier 3 — causal intent

| Question | Tier | Confounder check |
|---|---|---|
| Did cutting caffeine actually improve my sleep? | 3 | yes |
| If I meditate daily, does my HRV go up? | 3 | yes |
| Would sleeping more actually cause my grades to improve? | 3 | yes |
| Does more sleep cause better grades? | 3 | yes |

## Ambiguous / adversarial

| Question | Tier | Notes |
|---|---|---|
| Am I sleeping better since I moved apartments in December? | 2 | Regime-change question — a before/after comparison with a plausible confounder (the move itself), not a clean tier 1 average. |

## Wrong-tier cases (expected vs. actual, this run)

- **"If I meditate daily, does my HRV go up?"** — expected tier 3, router returned tier 2. Rationale given: *"This question implies a causal claim, so we'll use a controlled association analysis... check for potential confounders."* Defensible either way: no experiment is proposed, so treating it as an observational association isn't unreasonable, but it undersells the causal intent in the question.
- **"Does more sleep cause better grades?"** — expected tier 3, router returned tier 2. Same pattern: the model reliably favors tier 2 over tier 3 for causal-language questions that don't explicitly ask about an intervention or experiment.
- **"Am I sleeping better since I moved apartments in December?"** — expected tier 2, router returned tier 1. Rationale given: *"Tier 1 because the question asks for a general trend... without implying causation. However, moving_date is a plausible confounder."* The model noticed the confounder but didn't act on it by bumping the tier.

Pattern across all 3 misses: the router under-escalates on causal/regime-change
language it explicitly acknowledges in its own rationale — it names the right
consideration (a confounder, a causal implication) but doesn't consistently
convert that into the higher tier. Worth revisiting with a sharper tier-2-vs-3
boundary in the prompt, or a larger model, before this becomes a determinative
part of the pipeline.
