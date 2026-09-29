# Data ingestion (Google Health API + Google Calendar) — spec

Belongs to Phase 0 (data foundation) of the roadmap; this is Window A's
scope per `.claude/team-status.md`. Live API pull only — the Google Takeout
historical-backfill path (FitOut parser) is a separate, later ticket;
Phase 0's "real historical data loaded" definition of done isn't fully met
until that lands.

`roadmap.md` still lists "Calendar integration" under its "Out of scope
right now" list; this ticket only covers calendar **data plumbing** (OAuth,
schema, ingestion, query interface), not calendar-driven **analysis
features** (meeting-load-vs-recovery reasoning, scheduling questions —
`MattGPT-Outline.md` §5), which remain out of scope. `roadmap.md`'s
out-of-scope line needs a follow-up edit to reflect this split.

## Dependency mode

Depend, per `CLAUDE.md`'s build-philosophy table — Google Health API and
Calendar API client libraries (`google-auth`, `google-auth-oauthlib`) and
`tenacity` are used as-is, no forking.

## What it's for

Pulling three Google Health data-type bundles — Vitals & Health Metrics,
Sleep & Recovery, Activity & Fitness — plus Google Calendar events, into a
normalized local SQLite database, and exposing a `get_metric(name,
date_range)` query interface other windows (the stats layer, later the
router) depend on without knowing anything about Google's API shapes.
Nutrition, Women's Health, and Body Composition are explicitly out of
scope.

Calendar data lands in two places: `calendar_events` (raw, full-fidelity —
start/end, title, attendee count) for future event-level features, and
derived daily scalars (`meeting_count`, `meeting_minutes`) in the same
`metrics` table Health data uses — matching Window B's (`mattgpt/stats/`)
`BiometricRecord`/`Source="calendar"` convention, so `get_metric()` serves
both APIs uniformly.

## OAuth setup — single client, both APIs (manual, one-time — cannot be scripted)

1. Create/select one Google Cloud project (e.g. `mattgpt-personal`).
2. Enable both the target Google Health API and the Google Calendar API in
   the API library.
3. Configure the OAuth consent screen once: User type **External**,
   Publishing status **Testing**, add the Google account holding the
   Fitbit/calendar data as a **test user**. Testing mode exempts a
   personal, non-public app from Google's restricted-scope verification
   review.
4. Create **one** OAuth 2.0 Client ID, application type **Desktop app**,
   requesting scopes for both Health bundles and `calendar.readonly`
   together (`mattgpt/ingest/bundles.py::all_scopes()`) — one consent
   screen, one token file.
5. Download `client_secret.json` to the path set by `GOOGLE_CLIENT_SECRET_PATH`
   in `.env` (see `.env.example`) — this path is gitignored; never commit it.

## Still needs verification before a real run

- Exact OAuth scope strings per Health bundle (`mattgpt/ingest/bundles.py`,
  marked `<TODO>`). `calendar.readonly` is a real, documented Calendar API
  scope and does not need this caveat.
- The Google Health API base URL and per-bundle endpoint paths
  (`mattgpt/ingest/google_health_client.py`, marked `<TODO>`). The Calendar
  client (`mattgpt/ingest/calendar_client.py`) uses the real, documented
  `events.list` endpoint and needs no such verification.
- `google_health_client.extract_records()` — mapping the real Health API
  response JSON into this module's normalized record shape. Left as
  `NotImplementedError` until a real response has been seen, so nothing
  here guesses at Google's field names.

## Module layout

- `mattgpt/config.py` — `pydantic-settings` `Settings` (credential/DB paths, from `.env`)
- `mattgpt/ingest/oauth.py` — interactive consent + token refresh/caching (both APIs, one client)
- `mattgpt/ingest/bundles.py` — Health bundle -> metric name/unit/granularity + scopes; also the Calendar scope constant
- `mattgpt/ingest/http.py` — shared authenticated-GET-with-retry helper (`tenacity`)
- `mattgpt/ingest/google_health_client.py` — authenticated fetch per Health bundle
- `mattgpt/ingest/normalize.py` — pure functions, raw Health records -> DB-ready rows
- `mattgpt/ingest/calendar_client.py` — authenticated fetch of Calendar events in a date range
- `mattgpt/ingest/calendar_normalize.py` — pure functions, raw events -> `calendar_events` rows + derived daily metric rows
- `mattgpt/ingest/pipeline.py` — orchestrates auth -> fetch each Health bundle + calendar -> normalize -> upsert -> log
- `mattgpt/db/schema.py`, `connection.py`, `queries.py` — long-format `metrics`
  table + `calendar_events` table + `get_metric()`/`list_available_metrics()`

## Manual verification (once OAuth setup above is done)

Run a small script that authorizes once, pulls the last 7 days across all
three Health bundles and calendar, and confirms rows land in both `metrics`
and `calendar_events`; spot-check with
`get_metric(conn, "resting_heart_rate", start, end)` and
`get_metric(conn, "meeting_minutes", start, end)`.
