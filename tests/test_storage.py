from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src import storage


def test_build_video_row_maps_fields():
    item = {
        "id": "abc123",
        "snippet": {
            "title": "Test Video",
            "description": "desc",
            "categoryId": "10",
            "channelTitle": "Test Channel",
            "publishedAt": "2026-07-01T00:00:00Z",
        },
        "statistics": {"viewCount": "12345"},
    }
    category_map = {"10": "Music"}
    now = datetime(2026, 7, 7, tzinfo=timezone.utc)

    row = storage.build_video_row(item, category_map, now)

    assert row == (
        "abc123",
        "Test Video",
        "https://www.youtube.com/watch?v=abc123",
        "desc",
        10,
        "Music",
        "Test Channel",
        12345,
        "2026-07-01T00:00:00Z",
        now,
        now,
    )


def test_try_acquire_lock_returns_cursor_result():
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (True,)

    acquired = storage.try_acquire_lock(conn, key=42)

    assert acquired is True
    cursor.execute.assert_called_once_with("SELECT pg_try_advisory_lock(%s);", (42,))


def test_release_lock_calls_unlock():
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value

    storage.release_lock(conn, key=42)

    cursor.execute.assert_called_once_with("SELECT pg_advisory_unlock(%s);", (42,))


@patch("src.storage.psycopg2.extras.execute_batch")
def test_upsert_videos_commits(mock_execute_batch):
    conn = MagicMock()
    now = datetime(2026, 7, 7, tzinfo=timezone.utc)
    item = {
        "id": "abc123",
        "snippet": {"title": "T", "categoryId": "10", "channelTitle": "C"},
        "statistics": {},
    }

    storage.upsert_videos(conn, [item], {"10": "Music"}, now)

    mock_execute_batch.assert_called_once()
    conn.commit.assert_called_once()
