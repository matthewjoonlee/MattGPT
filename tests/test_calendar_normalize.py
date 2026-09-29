from mattgpt.ingest.calendar_normalize import derive_daily_metrics, normalize_calendar_events

TIMED_EVENT = {
    "id": "evt1",
    "summary": "1:1 with advisor",
    "start": {"dateTime": "2026-01-15T09:00:00-05:00"},
    "end": {"dateTime": "2026-01-15T09:30:00-05:00"},
    "attendees": [{"email": "a@example.com"}, {"email": "b@example.com"}],
}

ALL_DAY_EVENT = {
    "id": "evt2",
    "summary": "Spring Break",
    "start": {"date": "2026-01-16"},
    "end": {"date": "2026-01-17"},
}


def test_normalize_calendar_events_parses_timed_event():
    rows = normalize_calendar_events([TIMED_EVENT])
    row = rows[0]
    assert row["event_id"] == "evt1"
    assert row["title"] == "1:1 with advisor"
    assert row["is_all_day"] is False
    assert row["attendee_count"] == 2
    assert row["ts_start"].startswith("2026-01-15T14:00:00")  # normalized to UTC


def test_normalize_calendar_events_parses_all_day_event():
    rows = normalize_calendar_events([ALL_DAY_EVENT])
    row = rows[0]
    assert row["is_all_day"] is True
    assert row["attendee_count"] == 0


def test_derive_daily_metrics_excludes_all_day_events():
    rows = normalize_calendar_events([TIMED_EVENT, ALL_DAY_EVENT])
    metrics = derive_daily_metrics(rows)

    metric_names = {m["metric_name"] for m in metrics}
    assert metric_names == {"meeting_count", "meeting_minutes"}
    assert all(m["bundle"] == "calendar" for m in metrics)
    assert all(m["source"] == "google_calendar" for m in metrics)

    count_row = next(m for m in metrics if m["metric_name"] == "meeting_count")
    minutes_row = next(m for m in metrics if m["metric_name"] == "meeting_minutes")
    assert count_row["value"] == 1.0
    assert minutes_row["value"] == 30.0


def test_derive_daily_metrics_empty_when_no_timed_events():
    rows = normalize_calendar_events([ALL_DAY_EVENT])
    assert derive_daily_metrics(rows) == []
