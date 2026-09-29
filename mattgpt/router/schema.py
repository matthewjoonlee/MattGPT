"""Structured output shape for the NL question -> analysis spec router.

`KNOWN_VARIABLES` is a placeholder catalog standing in for the real schema
Window A's data-ingestion work will define — the router needs *some* fixed
vocabulary to map free-text questions onto, but these exact names are not
final. Replace with the real metric catalog once `get_metric(name, date_range)`
lands.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

KNOWN_VARIABLES: tuple[str, ...] = (
    "resting_heart_rate",
    "hrv",
    "sleep_duration",
    "steps",
    "active_minutes",
    "calendar_meeting_load",
    "grade",
    "interview_outcome",
    "mood_rating",
    "stress_rating",
)

VariableRole = Literal["outcome", "predictor", "confounder_candidate"]


class Variable(BaseModel):
    name: str = Field(description="One of the known variable names.")
    role: VariableRole


class AnalysisSpec(BaseModel):
    question: str
    variables: list[Variable]
    tier: Literal[1, 2, 3] = Field(
        description=(
            "1 = descriptive (rolling averages, simple correlation, no causal claim). "
            "2 = controlled association (regression/mixed-effects with confounders controlled). "
            "3 = causal (counterfactual inference or a real controlled experiment), "
            "gated downstream by a data-sufficiency check."
        )
    )
    confounder_check_required: bool = Field(
        description="True whenever the answer could be confounded by a third variable "
        "and that needs checking before the association is presented as meaningful."
    )
    rationale: str = Field(description="One or two sentences on why this tier was chosen.")
