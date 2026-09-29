import pytest

from mattgpt.ingest.normalize import normalize_records


def test_normalize_records_maps_bundle_fields():
    raw = [
        {"metric_name": "resting_heart_rate", "ts_start": "2026-01-01T00:00:00+00:00", "ts_end": None, "value": 58.0},
        {"metric_name": "steps", "ts_start": "2026-01-01T00:00:00+00:00", "ts_end": None, "value": 8000.0},
    ]

    vitals_rows = normalize_records("vitals", [raw[0]])
    assert vitals_rows[0]["metric_name"] == "resting_heart_rate"
    assert vitals_rows[0]["bundle"] == "vitals"
    assert vitals_rows[0]["unit"] == "bpm"
    assert vitals_rows[0]["granularity"] == "daily"
    assert vitals_rows[0]["source"] == "google_health_api"
    assert vitals_rows[0]["value"] == 58.0

    activity_rows = normalize_records("activity", [raw[1]])
    assert activity_rows[0]["metric_name"] == "steps"
    assert activity_rows[0]["unit"] == "count"


def test_normalize_records_rejects_unknown_bundle():
    with pytest.raises(ValueError, match="unknown bundle"):
        normalize_records("nutrition", [])


def test_normalize_records_rejects_metric_not_in_bundle():
    raw = [{"metric_name": "steps", "ts_start": "2026-01-01T00:00:00+00:00", "ts_end": None, "value": 1.0}]
    with pytest.raises(ValueError, match="not defined for bundle"):
        normalize_records("vitals", raw)


def test_normalize_records_preserves_raw_payload_for_audit():
    raw = [{"metric_name": "steps", "ts_start": "2026-01-01T00:00:00+00:00", "ts_end": None, "value": 8000.0}]
    rows = normalize_records("activity", raw)
    assert "8000" in rows[0]["raw_payload"]
