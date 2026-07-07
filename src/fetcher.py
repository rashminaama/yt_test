import logging

from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_exponential

from config import config

logger = logging.getLogger(__name__)

MAX_RESULTS = 20


def _get_client():
    return build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_trending_videos():
    """Fetch the top MAX_RESULTS trending videos for REGION_CODE."""
    youtube = _get_client()
    response = (
        youtube.videos()
        .list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode=config.REGION_CODE,
            maxResults=MAX_RESULTS,
        )
        .execute()
    )
    return response.get("items", [])
