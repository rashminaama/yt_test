CREATE TABLE IF NOT EXISTS _videos (
    video_id        TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    url             TEXT NOT NULL,
    description     TEXT,
    category_id     INTEGER,
    category_name   TEXT,
    channel_title   TEXT,
    view_count      BIGINT,
    published_at    TIMESTAMPTZ,
    first_seen_at   TIMESTAMPTZ NOT NULL,
    last_seen_at    TIMESTAMPTZ NOT NULL,
    times_trending  INTEGER DEFAULT 1
);
