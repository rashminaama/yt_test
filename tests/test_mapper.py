from unittest.mock import MagicMock, patch

from src import mapper


@patch("src.mapper.build")
def test_fetch_category_map(mock_build):
    mock_youtube = MagicMock()
    mock_build.return_value = mock_youtube
    mock_youtube.videoCategories.return_value.list.return_value.execute.return_value = {
        "items": [
            {"id": "10", "snippet": {"title": "Music"}},
            {"id": "20", "snippet": {"title": "Gaming"}},
        ]
    }

    result = mapper.fetch_category_map()

    assert result == {"10": "Music", "20": "Gaming"}
