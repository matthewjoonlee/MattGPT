"""Bundle -> metric mapping for the three in-scope Google Health API data-type bundles.

Nutrition, Women's Health, and Body Composition are intentionally excluded: no
scopes are requested for them and no metric names are reserved here. Adding a
bundle later means adding entries to BUNDLES, not a schema change (see
mattgpt/db/schema.py's long-format `metrics` table).

SCOPE STRINGS BELOW ARE PLACEHOLDERS. Per the approved plan, exact OAuth scope
URIs must be confirmed against the current Google Health API docs before the
first real auth run -- do not treat these as verified.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricDef:
    name: str
    unit: str
    granularity: str  # 'instant' | 'minute' | 'daily' | 'session'


BUNDLES: dict[str, dict[str, object]] = {
    "vitals": {
        "scopes": ["<TODO: verify vitals read scope against current API docs>"],
        "metrics": [
            MetricDef("resting_heart_rate", "bpm", "daily"),
            MetricDef("heart_rate", "bpm", "minute"),
            MetricDef("heart_rate_variability", "ms", "daily"),
            MetricDef("blood_oxygen_saturation", "percent", "daily"),
            MetricDef("respiratory_rate", "breaths_per_min", "daily"),
            MetricDef("skin_temperature", "celsius", "daily"),
        ],
    },
    "sleep": {
        "scopes": ["<TODO: verify sleep read scope against current API docs>"],
        "metrics": [
            MetricDef("sleep_session", "minutes", "session"),
            MetricDef("sleep_efficiency", "percent", "session"),
        ],
    },
    "activity": {
        "scopes": ["<TODO: verify activity read scope against current API docs>"],
        "metrics": [
            MetricDef("steps", "count", "daily"),
            MetricDef("distance", "meters", "daily"),
            MetricDef("active_minutes", "minutes", "daily"),
            MetricDef("calories_burned", "kcal", "daily"),
            MetricDef("exercise_session", "minutes", "session"),
            MetricDef("floors_climbed", "count", "daily"),
        ],
    },
}


CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
"""Real, documented Google Calendar API scope -- unlike the Health bundle
scopes above, this one is verified and safe to use as-is."""


def all_scopes() -> list[str]:
    """Every scope this app requests under its single OAuth client -- Health
    bundles plus Calendar, so one consent screen and one token cover both."""
    scopes: list[str] = [CALENDAR_SCOPE]
    for bundle in BUNDLES.values():
        scopes.extend(bundle["scopes"])  # type: ignore[arg-type]
    return scopes
