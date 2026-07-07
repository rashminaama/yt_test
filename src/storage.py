import psycopg2
import psycopg2.extras
from tenacity import retry, stop_after_attempt, wait_exponential

from config import config

# Arbitrary fixed key identifying the "run_pipeline" advisory lock. Any bigint works as
# long as it's the same value everywhere this lock is taken/released.
PIPELINE_LOCK_KEY = 918273645

UPSERT_SQL = """
INSERT INTO _videos (
    video_id, title, url, description, category_id, category_name,
    channel_title, view_count, published_at, first_seen_at, last_seen_at,
    times_trending
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
ON CONFLICT (video_id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    category_id = EXCLUDED.category_id,
    category_name = EXCLUDED.category_name,
    view_count = EXCLUDED.view_count,
    last_seen_at = EXCLUDED.last_seen_at,
    times_trending = _videos.times_trending + 1;
"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_connection():
    return psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )


def try_acquire_lock(conn, key=PIPELINE_LOCK_KEY):
    with conn.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_lock(%s);", (key,))
        return cur.fetchone()[0]


def release_lock(conn, key=PIPELINE_LOCK_KEY):
    with conn.cursor() as cur:
        cur.execute("SELECT pg_advisory_unlock(%s);", (key,))


def build_video_row(item, category_map, now):
    snippet = item["snippet"]
    stats = item.get("statistics", {})
    video_id = item["id"]
    category_id = snippet.get("categoryId")
    return (
        video_id,
        snippet["title"],
        f"https://www.youtube.com/watch?v={video_id}",
        snippet.get("description"),
        int(category_id) if category_id is not None else None,
        category_map.get(category_id),
        snippet.get("channelTitle"),
        int(stats["viewCount"]) if "viewCount" in stats else None,
        snippet.get("publishedAt"),
        now,
        now,
    )


def upsert_videos(conn, video_items, category_map, now):
    rows = [build_video_row(item, category_map, now) for item in video_items]
    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, UPSERT_SQL, rows)
    conn.commit()


def get_recent_videos(conn, limit=20):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT * FROM _videos ORDER BY last_seen_at DESC, view_count DESC LIMIT %s;",
            (limit,),
        )
        return cur.fetchall()
