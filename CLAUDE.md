# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
source venv/bin/activate            # Python 3.11 venv, already created
pip install -r requirements.txt

pytest                               # run full test suite (fully mocked, no network/DB needed)
pytest tests/test_pipeline.py        # run one test file
pytest tests/test_pipeline.py::test_run_pipeline_happy_path   # run a single test

sh/run_daily.sh                      # manually trigger the pipeline (cron entrypoint)
FLASK_APP=dashboard/app.py flask run # run the dashboard locally
gunicorn dashboard.app:app           # run the dashboard as it's deployed in production

psql -h localhost -U yt_app -d yt_trending -f scripts/init_db.sql   # (re)apply DB schema
```

`.env` holds real local Postgres credentials plus placeholder values for `YOUTUBE_API_KEY`
and `SMTP_*` — see `README.md` for what needs to be filled in before the pipeline can
actually fetch/send anything for real. Default dashboard login is `admin` / `changeme`.

## Architecture

**One pipeline function, two triggers.** `src/pipeline.py:run_pipeline()` is the entire
fetch → map → store → render → send flow. `sh/run_daily.sh` (cron, 9 AM daily) and
`dashboard/app.py`'s `POST /send-now` route both call this exact function — there is no
separate code path for automatic vs. manual sends, by design (see the doc's change log).

**Data flow through `run_pipeline()`:**
1. `storage.get_connection()` — psycopg2 connection, tenacity-retried for transient DB blips.
2. `storage.try_acquire_lock()` — Postgres advisory lock (`pg_try_advisory_lock`, fixed key
   `PIPELINE_LOCK_KEY` in `src/storage.py`) so an overlapping cron run and dashboard click
   can't both hit the YouTube API and send duplicate emails. If not acquired, the run is
   skipped (returns `{"status": "skipped"}`) rather than blocking.
3. `fetcher.fetch_trending_videos()` — YouTube Data API v3, `videos.list(chart=mostPopular)`.
4. `mapper.fetch_category_map()` — `videoCategories.list`, builds `category_id -> name`.
5. `storage.upsert_videos()` — the `_videos` table upsert; `ON CONFLICT` bumps
   `times_trending` and refreshes `last_seen_at` but never touches `first_seen_at`.
6. `storage.get_recent_videos()` → `reporter.render_report()` → `mailer.send_report()`.
7. On success, pings `HEALTHCHECKS_URL` (best-effort — failure here never fails the run).

All three external calls (YouTube API, SMTP, Postgres connect) are wrapped in `tenacity`
retry/backoff, since this is meant to run unattended via cron.

**Config is centralized.** Every credential and connection value flows through
`config/config.py` (loaded once via `python-dotenv`), never read from `os.environ` directly
elsewhere in the codebase.

**Template split is intentional.** `views/trending_report.html` is the email body only,
rendered standalone via a Jinja2 `Environment` in `src/reporter.py` (not through Flask).
`dashboard/templates/` is the dashboard's own UI (login, video list + button), rendered
through Flask's `render_template`. These are two different renderers and are not
interchangeable.

**Dashboard auth** is a single shared login (`DASHBOARD_USERNAME` / `DASHBOARD_PASSWORD_HASH`
checked via `werkzeug.security`), not a multi-user system — there's no user table.

## Tests

Everything in `tests/` mocks the YouTube API client (`googleapiclient.discovery.build`),
`smtplib.SMTP`, and the psycopg2 connection — the suite never touches real credentials,
network, or the local Postgres instance.
