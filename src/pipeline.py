import logging
import logging.handlers
from datetime import datetime, timezone
from pathlib import Path

import requests

from config import config
from src import fetcher, mapper, mailer, reporter, storage

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("yt_trending")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "run.log", maxBytes=1_000_000, backupCount=5
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)


def _ping_healthchecks():
    if not config.HEALTHCHECKS_URL:
        return
    try:
        requests.get(config.HEALTHCHECKS_URL, timeout=5)
    except requests.RequestException as exc:
        logger.warning("Healthchecks ping failed: %s", exc)


def run_pipeline():
    """Fetch trending videos, store them, render + send the report.

    Shared by both the cron entrypoint (sh/run_daily.sh) and the dashboard's
    /send-now route, so behavior never drifts between the automatic and manual paths.
    An advisory lock prevents an overlapping cron + manual trigger from double-sending.
    """
    conn = storage.get_connection()
    try:
        if not storage.try_acquire_lock(conn):
            logger.info("Pipeline already running elsewhere — skipping this trigger")
            return {"status": "skipped", "reason": "pipeline already running"}

        try:
            logger.info("Fetching trending videos")
            videos = fetcher.fetch_trending_videos()
            category_map = mapper.fetch_category_map()

            now = datetime.now(timezone.utc)
            storage.upsert_videos(conn, videos, category_map, now)

            recent = storage.get_recent_videos(conn)
            html = reporter.render_report(recent)
            mailer.send_report(html)

            logger.info("Pipeline run succeeded (%d videos)", len(videos))
            _ping_healthchecks()
            return {"status": "ok", "video_count": len(videos)}
        except Exception:
            logger.exception("Pipeline run failed")
            raise
        finally:
            storage.release_lock(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    run_pipeline()
