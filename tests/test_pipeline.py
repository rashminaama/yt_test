from unittest.mock import MagicMock, patch

from src import pipeline


@patch("src.pipeline._ping_healthchecks")
@patch("src.pipeline.mailer.send_report")
@patch("src.pipeline.reporter.render_report", return_value="<html></html>")
@patch("src.pipeline.storage.get_recent_videos", return_value=[{"title": "V"}])
@patch("src.pipeline.storage.upsert_videos")
@patch("src.pipeline.mapper.fetch_category_map", return_value={"10": "Music"})
@patch("src.pipeline.fetcher.fetch_trending_videos", return_value=[{"id": "abc"}])
@patch("src.pipeline.storage.get_connection")
def test_run_pipeline_happy_path(
    mock_get_connection,
    mock_fetch_trending,
    mock_fetch_category_map,
    mock_upsert,
    mock_get_recent,
    mock_render,
    mock_send,
    mock_ping,
):
    conn = MagicMock()
    mock_get_connection.return_value = conn
    conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (True,)

    result = pipeline.run_pipeline()

    assert result == {"status": "ok", "video_count": 1}
    mock_send.assert_called_once_with("<html></html>")
    conn.close.assert_called_once()


@patch("src.pipeline.storage.get_connection")
def test_run_pipeline_skips_when_lock_not_acquired(mock_get_connection):
    conn = MagicMock()
    mock_get_connection.return_value = conn
    conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (False,)

    result = pipeline.run_pipeline()

    assert result == {"status": "skipped", "reason": "pipeline already running"}
    conn.close.assert_called_once()


@patch("src.pipeline.mailer.send_report", side_effect=RuntimeError("smtp down"))
@patch("src.pipeline.reporter.render_report", return_value="<html></html>")
@patch("src.pipeline.storage.get_recent_videos", return_value=[])
@patch("src.pipeline.storage.upsert_videos")
@patch("src.pipeline.mapper.fetch_category_map", return_value={})
@patch("src.pipeline.fetcher.fetch_trending_videos", return_value=[])
@patch("src.pipeline.storage.get_connection")
def test_run_pipeline_releases_lock_on_failure(
    mock_get_connection,
    mock_fetch_trending,
    mock_fetch_category_map,
    mock_upsert,
    mock_get_recent,
    mock_render,
    mock_send,
):
    conn = MagicMock()
    mock_get_connection.return_value = conn
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (True,)

    try:
        pipeline.run_pipeline()
        assert False, "expected RuntimeError to propagate"
    except RuntimeError:
        pass

    execute_calls = [call.args[0] for call in cursor.execute.call_args_list]
    assert "SELECT pg_advisory_unlock(%s);" in execute_calls
    conn.close.assert_called_once()
