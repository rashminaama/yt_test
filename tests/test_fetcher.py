from unittest.mock import MagicMock, patch

from src import fetcher


@patch("src.fetcher.build")
def test_fetch_trending_videos_returns_items(mock_build):
    mock_youtube = MagicMock()
    mock_build.return_value = mock_youtube
    mock_youtube.videos.return_value.list.return_value.execute.return_value = {
        "items": [{"id": "abc123", "snippet": {"title": "Test Video"}}]
    }

    result = fetcher.fetch_trending_videos()

    assert result == [{"id": "abc123", "snippet": {"title": "Test Video"}}]
    mock_youtube.videos.return_value.list.assert_called_once()
    _, kwargs = mock_youtube.videos.return_value.list.call_args
    assert kwargs["chart"] == "mostPopular"
    assert kwargs["maxResults"] == fetcher.MAX_RESULTS


@patch("src.fetcher.build")
def test_fetch_trending_videos_empty_response(mock_build):
    mock_youtube = MagicMock()
    mock_build.return_value = mock_youtube
    mock_youtube.videos.return_value.list.return_value.execute.return_value = {}

    result = fetcher.fetch_trending_videos()

    assert result == []
