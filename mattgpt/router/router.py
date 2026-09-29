"""NL question -> structured analysis spec, via a local Ollama model.

Per CLAUDE.md's "compute, then explain" principle, this module does no
statistics itself — it only decides *what* analysis is needed (which
variables, which tier, whether a confounder check applies) and hands that
decision off as a typed `AnalysisSpec`.
"""

from __future__ import annotations

import ollama
from pydantic import ValidationError

from mattgpt.router.schema import KNOWN_VARIABLES, AnalysisSpec

SYSTEM_PROMPT = f"""You are the router for MattGPT, a personal health/causal-inference \
assistant. Turn the user's question into a structured analysis spec.

Known variables you may reference (use these exact names, don't invent new ones):
{", ".join(KNOWN_VARIABLES)}

Pick the analysis tier:
- Tier 1 (descriptive): rolling averages, simple correlation, no causal claim implied.
- Tier 2 (controlled association): regression/mixed-effects with confounders controlled.
- Tier 3 (causal): counterfactual inference or a real controlled experiment. Use this \
whenever the question asks whether something actually *caused*, *improved*, or *changed* \
an outcome, or proposes an intervention ("if I did X, would Y change?").

Set confounder_check_required=true whenever a third variable could plausibly explain an \
association in the data (almost always true for tier 2 and 3; usually false for tier 1 \
unless the question itself implies a comparison across groups).

Respond with JSON matching the given schema only."""


def route_question(
    question: str,
    *,
    model: str = "llama3.2",
    max_retries: int = 1,
) -> AnalysisSpec:
    """Route a natural-language question to a structured analysis spec.

    Calls the local Ollama model at temperature 0 for determinism, and
    validates the response against `AnalysisSpec`. On a malformed response
    (bad JSON, wrong shape), retries once with a stricter follow-up before
    giving up — a narrow, local instance of the self-healing "name the
    failure, match the fix" pattern (failure: malformed model output; fix:
    retry with a stricter instruction), not the full self-healing framework.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        response = ollama.chat(
            model=model,
            messages=messages,
            format=AnalysisSpec.model_json_schema(),
            options={"temperature": 0},
        )
        content = response["message"]["content"]
        try:
            return AnalysisSpec.model_validate_json(content)
        except ValidationError as exc:
            last_error = exc
            messages.append({"role": "assistant", "content": content})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "That wasn't valid JSON matching the schema. "
                        "Return only valid JSON matching the schema, nothing else."
                    ),
                }
            )

    raise ValueError(
        f"Model {model!r} failed to produce a valid AnalysisSpec after "
        f"{max_retries + 1} attempt(s) for question: {question!r}"
    ) from last_error
