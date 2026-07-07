# YouTube Trending Pipeline

Fetches the top 20 YouTube trending videos daily, stores them in Postgres, and emails an
HTML summary. A Flask dashboard provides a manual "Send Now" trigger. Both the cron job
and the dashboard call the same `run_pipeline()` function (`src/pipeline.py`), so behavior
never drifts between the automatic and manual paths.

## Setup

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database

A local Postgres role (`yt_app`) and database (`yt_trending`) have already been created.
The schema lives in `scripts/init_db.sql`:

```bash
psql -h localhost -U yt_app -d yt_trending -f scripts/init_db.sql
```

### Environment variables

Copy `.env.example` to `.env` and fill in the placeholders:

- `YOUTUBE_API_KEY` — a YouTube Data API v3 key
- `SMTP_HOST` / `SMTP_USERNAME` / `SMTP_PASSWORD` — your outgoing mail provider
- `RECIPIENT_EMAILS` — comma-separated list of report recipients
- `HEALTHCHECKS_URL` — optional healthchecks.io ping URL (leave blank to disable)

`DASHBOARD_USERNAME` / `DASHBOARD_PASSWORD_HASH` / `FLASK_SECRET_KEY` are already populated
in `.env` with a working default login (`admin` / `changeme`). **Change the password before
exposing the dashboard beyond localhost:**

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-new-password'))"
```

Paste the output into `DASHBOARD_PASSWORD_HASH` in `.env`.

## Running

**Automatic daily run (cron)** — fires once a day, owns the 9:00 AM schedule:

```cron
0 9 * * * /path/to/yt_test/sh/run_daily.sh >> /path/to/yt_test/logs/run.log 2>&1
```

**Manual run**, e.g. for testing:

```bash
sh/run_daily.sh
```

**Dashboard** (persistent process, separate from the cron job):

```bash
# local dev
FLASK_APP=dashboard/app.py flask run

# production
gunicorn dashboard.app:app
```

Put the dashboard behind HTTPS if exposed beyond localhost — the login form sends the
password in plaintext over the wire otherwise.

## Testing

```bash
pytest
```

All YouTube API, SMTP, and Postgres calls are mocked, so the suite runs without any real
credentials or network access.
